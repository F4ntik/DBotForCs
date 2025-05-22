from aiohttp import web
import json # Added
from enum import Enum
from typing import Callable, List, Optional, Dict, Any # Added Dict, Any

from observer.observer_client import observer, Event, logger # Added logger
from data_server import sql_server # Added
import config # Added

# SECTION Исключения WebServer

# -- WebServerError
class WebServerError(Exception):
  """Базовый класс для исключений веб-сервера."""
  pass

# -- ServerSetupFailed
class ServerSetupFailed(WebServerError):
  """Исключение для ошибок при настройке сервера."""
  pass

# -- ServerStartFailed
class ServerStartFailed(WebServerError):
  """Исключение для ошибок при запуске сервера."""
  pass

# -- AllowedIPsEmpty
class AllowedIPsEmpty(WebServerError):
  """Исключение для случая, когда список разрешенных IP-адресов пуст."""
  pass

# !SECTION

# SECTION Class WebServer
class WebServer:
  # -- __init__()
  def __init__(self, host: str, port: int, allowed_ips: List[str]) -> None:
    """
    Инициализирует экземпляр веб-сервера.

    :param host: Адрес, на котором будет запущен сервер.
    :param port: Порт, на котором будет запущен сервер.
    :param allowed_ips: Список разрешенных IP-адресов для доступа к серверу.
    """
    if not allowed_ips:
      raise AllowedIPsEmpty("allowed_ips list cannot be empty.")
    
    if port <= 0 or port > 65535:
      raise ServerSetupFailed("Port must be between 1 and 65535.")
    
    self.app: web.Application = web.Application()
    self.host: str = host
    self.port: int = port
    self.allowed_ips: List[str] = allowed_ips

    # Добавление middleware для проверки IP-адресов
    self.app.middlewares.append(self.ip_check_middleware)

    # Добавление маршрута для загрузки карт
    self.app.router.add_post('/maps/upload_from_server', self.handle_map_upload_request)

  # -- handle_map_upload_request()
  async def handle_map_upload_request(self, request: web.Request) -> web.Response:
    # Verify Authorization
    auth_header = request.headers.get('Authorization')
    # Use config.API_KEY as the token. 
    # A dedicated config.CS_PLUGIN_TOKEN or WEBHOOK_TOKEN would be better.
    # The plugin sends its own configured token; this side should match it.
    expected_token = getattr(config, 'API_KEY', None) 

    if not expected_token:
        logger.warning("WebServer: API_KEY (used as CS Plugin Token) is not set in config.py. Map upload endpoint will reject all requests if API_KEY remains unset.")
    
    if not auth_header or auth_header != expected_token:
        logger.warning(f"WebServer: Unauthorized map upload attempt. IP: {request.remote}. Token used: '{auth_header}'. Expected a token matching config.API_KEY.")
        return web.Response(status=403, text="Forbidden: Invalid or missing Authorization token.")

    try:
        maps_data = await request.json()
    except json.JSONDecodeError:
        body_text = await request.text()
        logger.error(f"WebServer: Failed to decode JSON from map upload request. IP: {request.remote}. Body: '{body_text[:500]}' (first 500 chars)")
        return web.Response(status=400, text="Invalid JSON format")

    if not isinstance(maps_data, list):
        logger.error(f"WebServer: Map upload data is not a list. IP: {request.remote}. Data type: {type(maps_data)}")
        return web.Response(status=400, text="JSON data must be a list of maps")
    
    processed_count = 0
    errors_count = 0
    received_count = len(maps_data)
    batch_map_names_for_logging = [] # For concise logging of processed maps

    logger.info(f"WebServer: Received {received_count} maps for upload from server. IP: {request.remote}")

    for map_item in maps_data:
        if not isinstance(map_item, dict) or not all(k in map_item for k in ["map_name", "min_players", "max_players", "priority", "activated"]):
            logger.warning(f"WebServer: Skipping invalid map item (missing keys or not a dict): {map_item}. IP: {request.remote}")
            errors_count +=1
            continue
        
        map_name_for_log = map_item.get('map_name', 'UnknownMap')
        batch_map_names_for_logging.append(map_name_for_log)

        try:
            # Call the function in sql_server.py to upsert the map
            await sql_server.upsert_map_from_server(map_item) # map_item is Dict[str, Any]
            processed_count += 1
        except sql_server.QueryError as qe: # Catch specific QueryError from sql_server
            logger.error(f"WebServer: QueryError processing map '{map_name_for_log}' from IP {request.remote}: {qe}")
            errors_count += 1
        except Exception as e:
            # Log with exc_info=True to get the traceback for unexpected errors
            logger.error(f"WebServer: Generic error processing map '{map_name_for_log}' from IP {request.remote}: {e}", exc_info=True)
            errors_count += 1
            
    if batch_map_names_for_logging:
        logger.info(f"WebServer: Batch map upload from server processing finished for maps (first 10 shown): {batch_map_names_for_logging[:10]}{'...' if len(batch_map_names_for_logging) > 10 else ''}. IP: {request.remote}")

    # After processing all maps, update the main map list cache in sql_server.py
    # This ensures that the global map_list_cache used by route_get_map_list is up-to-date.
    try:
        await sql_server.update_map_list_cache()
        logger.info(f"WebServer: Successfully updated map list cache after server sync. IP: {request.remote}")
    except Exception as e:
        logger.error(f"WebServer: Failed to update map list cache after server sync. IP: {request.remote}: {e}", exc_info=True)
        # This error doesn't make the whole request fail, but it's important to log.

    response_summary = {
        "message": "Map list processed.",
        "received": received_count,
        "processed": processed_count,
        "errors": errors_count
    }
    logger.info(f"WebServer: Map upload from server complete. Summary: {response_summary}. IP: {request.remote}")
    return web.Response(status=200, content_type='application/json', text=json.dumps(response_summary))

  # -- ip_check_middleware()
  @web.middleware
  async def ip_check_middleware(self, request: web.Request, handler: Callable) -> web.Response:
    """
    Middleware для проверки IP-адресов клиентов.

    :param request: HTTP-запрос.
    :param handler: Функция-обработчик для обработки запроса.
    :return: Ответ на запрос или ошибка доступа.
    """
    client_ip: str = request.remote
    if client_ip not in self.allowed_ips:
      await observer.notify(Event.WS_IP_NOT_ALLOWED, {
        "request_remote": request.remote,
        "request_url": request.url,
        "request_method": request.method,
        "request_headers": request.headers,
        "request_body": await request.text()
      })
      return web.Response(status=403, text="Access Forbidden: Your IP is not allowed.")
    
    # Если IP-адрес разрешен, продолжить обработку запроса
    return await handler(request)

  # -- add_post()
  # Corrected signature: method parameter is not needed for add_post
  def add_post(self, path: str, handler: Callable) -> None:
    """
    Добавляет POST маршрут в приложение.

    :param path: Путь маршрута.
    :param handler: Функция-обработчик для данного маршрута.
    """
    self.app.router.add_post(path, handler)

  # -- run_webserver()
  async def run_webserver(self) -> None:
    """
    Запускает веб-сервер.
    :raises ServerSetupFailed: Ошибка при настройке сервера.
    :raises ServerStartFailed: Ошибка при запуске сервера.
    """
    if self.host is None:
      raise ServerSetupFailed("Host cannot be None.")
    
    try:
      self._runner: web.AppRunner = web.AppRunner(self.app)
      await self._runner.setup()
    except Exception as e:
      raise ServerSetupFailed(f"Ошибка при настройке сервера: {str(e)}") from e
    
    try:
      self._site: web.TCPSite = web.TCPSite(self._runner, self.host, self.port)
      await self._site.start()
    except Exception as e:
      raise ServerStartFailed(f"Ошибка при запуске сервера: {str(e)}") from e

# !SECTION
