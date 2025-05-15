import aiomysql
from typing import Any, List, Optional, Tuple, Dict, AsyncIterator, Iterator, Callable
import logging
import asyncio
from observer.observer_client import logger

# SECTION AioMysqlError
class AioMysqlError(Exception):
  """Базовый класс для исключений AioMysql."""
  pass

# -- ConnectionError
class ConnectionError(AioMysqlError):
  """Исключение для ошибок подключения к базе данных."""
  pass

# -- QueryError
class QueryError(AioMysqlError):
  """Исключение для ошибок выполнения SQL-запросов."""
  pass

# -- MultipleQueryError
class MultipleQueryError(AioMysqlError):
  """Исключение для ошибок выполнения нескольких SQL-запросов."""
  pass

# -- TransactionError
class TransactionError(AioMysqlError):
  """Исключение для ошибок, связанных с транзакциями."""
  pass

# !SECTION

# SECTION AioMysql
class AioMysql:
  # -- __init__()
  def __init__(self, host: str, port: int, user: str, password: str, db: str) -> None:
    self.host: str = host
    self.port: int = port
    self.user: str = user
    self.password: str = password
    self.db: str = db
    self.pool: Optional[aiomysql.Pool] = None
    self.conn: Optional[aiomysql.Connection] = None
    self._connecting: bool = False
    self._connection_attempts: int = 0
    self._reconnect_backoff_time: int = 5  # Начальное время задержки перед повторной попыткой (в секундах)
    self._max_reconnect_attempts: int = 10  # Максимальное количество попыток переподключения
    self._is_healthy: bool = False
    
  # -- is_connected
  def is_connected(self) -> bool:
    """Проверяет, существует ли соединение с базой данных и оно здорово."""
    return self.pool is not None and not self.pool.closed and self._is_healthy
    
  # -- connect()
  async def connect(self) -> None:
    """Создает пул соединений с базой данных."""
    # Предотвращаем повторные попытки подключения во время выполнения
    if self._connecting:
      return
      
    self._connecting = True
    self._connection_attempts = 0
    self._is_healthy = False
    
    while self._connection_attempts < self._max_reconnect_attempts:
      try:
        # Если уже есть пул, но он не работает - закрываем его
        if self.pool:
          try:
            self.pool.close()
            await self.pool.wait_closed()
          except Exception:
            pass
            
        self.pool = await aiomysql.create_pool(
          host=self.host,
          port=self.port,
          user=self.user,
          password=self.password,
          db=self.db,
          autocommit=True,  # Автоматический коммит для операций
          maxsize=10,  # Максимальное количество соединений в пуле
          minsize=1,  # Минимальное количество соединений в пуле
          loop=asyncio.get_event_loop()
        )
        
        # Проверка соединения
        async with self.pool.acquire() as conn:
          async with conn.cursor() as cursor:
            await cursor.execute('SELECT 1')  # Простой запрос для проверки
        
        self._is_healthy = True
        self._connecting = False
        return
        
      except aiomysql.Error as e:
        self._connection_attempts += 1
        wait_time = min(60, self._reconnect_backoff_time * (2 ** (self._connection_attempts - 1)))  # Exponential backoff
        logger.error(f"Ошибка при подключении к MySQL ({self._connection_attempts}/{self._max_reconnect_attempts}): {e}. Повторная попытка через {wait_time} сек.")
        await asyncio.sleep(wait_time)
      except Exception as e:
        logger.error(f"Неожиданная ошибка при подключении к MySQL: {e}")
        self._connection_attempts += 1
        await asyncio.sleep(self._reconnect_backoff_time)

    # Если исчерпаны все попытки
    self._connecting = False
    raise ConnectionError(f"Не удалось подключиться к базе данных после {self._max_reconnect_attempts} попыток.")
    
  # -- _execute_one_internal
  async def _execute_one_internal(self, query: str, args: Optional[Tuple[Any, ...]] = ()) -> Tuple[int, Optional[List[Tuple[Any, ...]]]]:
    async with self.pool.acquire() as conn:
      async with conn.cursor() as cursor:
        await cursor.execute(query, args)
        affected_rows = cursor.rowcount  # Получаем количество затронутых строк
        
        if cursor.description:  # Проверяем, есть ли результат
          result = await cursor.fetchall()
          return affected_rows, result
        
        await conn.commit()
        return affected_rows, None  # Если нет результата
  
  # -- execute_one()
  async def execute_one(self, query: str, args: Optional[Tuple[Any, ...]] = ()) -> Tuple[int, Optional[List[Tuple[Any, ...]]]]:
    """Выполняет SQL-запрос и возвращает количество затронутых строк и результат."""
    try:
      return await self.execute_with_retry(self._execute_one_internal, query, args)
    except aiomysql.Error as e:
      raise QueryError(f"Ошибка при выполнении запроса: {e}. Запрос: {query}, Параметры: {args}")
    except Exception as e:
      raise QueryError(f"Неожиданная ошибка: {e}. Запрос: {query}, Параметры: {args}")

  # -- _execute_change_internal
  async def _execute_change_internal(self, query: str, args: Optional[Tuple[Any, ...]] = ()) -> int:
    async with self.pool.acquire() as conn:
      async with conn.cursor() as cursor:
        await cursor.execute(query, args)
        affected_rows = cursor.rowcount
        await conn.commit()  # Коммитим изменения
        return affected_rows
        
  # -- execute_change()
  async def execute_change(self, query: str, args: Optional[Tuple[Any, ...]] = ()) -> int:
    """Выполняет SQL-запрос, изменяющий данные, и возвращает количество затронутых строк."""
    try:
      return await self.execute_with_retry(self._execute_change_internal, query, args)
    except aiomysql.Error as e:
      raise QueryError(f"Ошибка при выполнении запроса: {e}. Запрос: {query}, Параметры: {args}")
    except Exception as e:
      raise QueryError(f"Неожиданная ошибка: {e}. Запрос: {query}, Параметры: {args}")

  # -- check_connection
  async def check_connection(self) -> bool:
    """Проверяет соединение с базой данных и при необходимости переподключается."""
    if not self.pool:
      # Соединение никогда не было установлено
      try:
        await self.connect()
        return True
      except ConnectionError:
        return False
    
    # Проверяем соединение простым запросом
    try:
      async with self.pool.acquire() as conn:
        async with conn.cursor() as cursor:
          await cursor.execute('SELECT 1')
          self._is_healthy = True
          return True
    except Exception as e:
      logger.error(f"Проверка соединения с MySQL не удалась: {e}. Попытка переподключения.")
      self._is_healthy = False
      # Пытаемся переподключиться
      try:
        await self.connect()
        return True
      except ConnectionError:
        return False

  # -- execute_with_retry
  async def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
    """Выполняет функцию с повторными попытками при ошибках соединения."""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
      if not self._is_healthy:
        if not await self.check_connection():
          retry_count += 1
          if retry_count >= max_retries:
            raise ConnectionError("Не удалось восстановить соединение с базой данных.")
          await asyncio.sleep(1 * retry_count)  # Линейный backoff
          continue
      
      try:
        return await func(*args, **kwargs)
      except (aiomysql.OperationalError, aiomysql.InterfaceError) as e:
        # Ошибки соединения
        logger.error(f"Ошибка соединения при выполнении запроса: {e}. Попытка {retry_count+1}/{max_retries}")
        self._is_healthy = False
        retry_count += 1
        if retry_count >= max_retries:
          raise
        await asyncio.sleep(1 * retry_count)  # Линейный backoff
      except Exception as e:
        # Другие ошибки просто пробрасываем дальше
        raise

  # -- _execute_select_internal
  async def _execute_select_internal(self, query: str, args: Optional[Tuple[Any, ...]] = ()) -> List[Tuple[Any, ...]]:
    async with self.pool.acquire() as conn:
      async with conn.cursor() as cursor:
        await cursor.execute(query, args)
        result = await cursor.fetchall()  # Получаем результат
        return result

  # -- execute_select()
  async def execute_select(self, query: str, args: Optional[Tuple[Any, ...]] = ()) -> List[Tuple[Any, ...]]:
    """Выполняет SQL-запрос на выборку данных и возвращает результат."""
    try:
      return await self.execute_with_retry(self._execute_select_internal, query, args)
    except aiomysql.Error as e:
      raise QueryError(f"Ошибка при выполнении запроса: {e}. Запрос: {query}, Параметры: {args}")
    except Exception as e:
      raise QueryError(f"Неожиданная ошибка: {e}. Запрос: {query}, Параметры: {args}")


  # -- _exec_many_internal
  async def _exec_many_internal(self, query: str, args_list: List[Tuple[Any, ...]]) -> None:
    async with self.pool.acquire() as conn:
      async with conn.cursor() as cursor:
        await cursor.executemany(query, args_list)
        await conn.commit()
  
  # -- exec_many()
  async def exec_many(self, query: str, args_list: List[Tuple[Any, ...]]) -> None:
    """Выполняет один и тот же SQL-запрос несколько раз с разными наборами параметров."""
    try:
      return await self.execute_with_retry(self._exec_many_internal, query, args_list)
    except aiomysql.Error as e:
      raise MultipleQueryError(f"Ошибка при выполнении нескольких запросов: {e}. Запрос: {query}, Параметры: {args_list}")
    except Exception as e:
      raise MultipleQueryError(f"Неожиданная ошибка: {e}. Запрос: {query}, Параметры: {args_list}")

  # -- fetch_iter()
  async def fetch_iter(self, query: str, *, args: Optional[Tuple[Any, ...]] = (), batch_size: int = 100) -> AsyncIterator[Tuple[Any, ...]]:
    """Асинхронный итератор для выборки данных по частям."""
    # Для итераторов мы не можем использовать простой механизм retry, поэтому реализуем его здесь
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
      if not self._is_healthy:
        if not await self.check_connection():
          retry_count += 1
          if retry_count >= max_retries:
            raise ConnectionError("Не удалось восстановить соединение с базой данных.")
          await asyncio.sleep(1 * retry_count)  # Линейный backoff
          continue
      
      try:
        async with self.pool.acquire() as conn:
          async with conn.cursor() as cursor:
            await cursor.execute(query, args)
            while True:
              rows = await cursor.fetchmany(size=batch_size)  # Получаем указанное количество строк за раз
              if not rows:
                break
              for row in rows:
                yield row  # Возвращаем строку
        return  # Успешно завершаем итерацию
      except (aiomysql.OperationalError, aiomysql.InterfaceError) as e:
        # Ошибки соединения
        logger.error(f"Ошибка соединения при выполнении итерации: {e}. Попытка {retry_count+1}/{max_retries}")
        self._is_healthy = False
        retry_count += 1
        if retry_count >= max_retries:
          raise QueryError(f"Ошибка при выборке данных: {e}. Запрос: {query}, Параметры: {args}")
        await asyncio.sleep(1 * retry_count)  # Линейный backoff
      except aiomysql.Error as e:
        raise QueryError(f"Ошибка при выборке данных: {e}. Запрос: {query}, Параметры: {args}")
      except Exception as e:
        raise QueryError(f"Неожиданная ошибка: {e}. Запрос: {query}, Параметры: {args}")

  # -- close()
  async def close(self) -> None:
    """Закрывает пул соединений."""
    if not self.pool:
        raise ConnectionError("Пул соединений уже закрыт.")
    self.pool.close()
    await self.pool.wait_closed()
    self.pool = None
      
# !SECTION

# SECTION Transaction
class Transaction:
  # -- __init__()
  def __init__(self, pool: aiomysql.Pool) -> None:
    """Инициализирует объект транзакции с пулом соединений."""
    self.pool: aiomysql.Pool = pool
    self.conn: Optional[aiomysql.Connection] = None  # Соединение, используемое в транзакции
  
  # -- begin()
  async def begin(self) -> None:
    """Начинает транзакцию."""
    if not self.pool:
      raise ConnectionError("Пул соединений не инициализирован.")
    try:
      self.conn = await self.pool.acquire()  # Получаем соединение
      await self.conn.begin()  # Начинаем транзакцию
    except aiomysql.Error as e:
      raise TransactionError(f"Ошибка при начале транзакции: {e}")
  
  # -- execute()
  async def execute(self, query: str, args: Optional[Tuple[Any, ...]] = ()) -> Tuple[int, Optional[List[Tuple[Any, ...]]]]:
    """Выполняет SQL-запрос в рамках текущей транзакции.
    
    Args:
      query (str): SQL-запрос для выполнения.
      args (Optional[Tuple[Any, ...]]): Параметры для SQL-запроса.

    Returns:
      Tuple[int, Optional[List[Tuple[Any, ...]]]]: Количество затронутых строк и результат запроса.
    """
    if not self.conn:
      raise TransactionError("Нет активной транзакции.")
    try:
      async with self.conn.cursor() as cursor:
        await cursor.execute(query, args)  # Выполняем запрос
        affected_rows = cursor.rowcount  # Получаем количество затронутых строк
        result = await cursor.fetchall()  # Возвращаем результаты
        return affected_rows, result
    except aiomysql.Error as e:
      raise TransactionError(f"Ошибка при выполнении запроса: {e}. Запрос: {query}, Параметры: {args}")
  
  # -- commit()
  async def commit(self) -> None:
    """Коммитит текущую транзакцию."""
    if not self.conn:
      raise TransactionError("Нет активной транзакции.")
    try:
      await self.conn.commit()  # Коммитим изменения
    except aiomysql.Error as e:
      raise TransactionError(f"Ошибка при коммите транзакции: {e}")
  
  # -- rollback()
  async def rollback(self) -> None:
    """Откатывает текущую транзакцию."""
    if not self.conn:
      raise TransactionError("Нет активной транзакции.")
    try:
      await self.conn.rollback()  # Откатываем изменения
    except aiomysql.Error as e:
      raise TransactionError(f"Ошибка при откате транзакции: {e}")
  
  # -- close()
  async def close(self) -> None:
    """Закрывает соединение."""
    if self.conn:
      await self.pool.release(self.conn)  # Освобождаем соединение
      self.conn = None  # Сбрасываем соединение

# !SECTION