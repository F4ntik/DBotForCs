## Requirements

To work with the `WebServer` class, you need to install the following non-standard modules:

`pip install aiohttp`

### WebServer

A class for creating and managing a web server.

#### Attributes

- `app` (web.Application): An instance of the `aiohttp` application.
- `host` (str): The address on which the server will run.
- `port` (int): The port on which the server will run.
- `allowed_ips` (List[str]): A list of allowed IP addresses for accessing the server.

#### Methods

- `__init__(host: str, port: int, allowed_ips: List[str]) -> None`
  - Initializes an instance of the web server.
  - **Parameters:**
    - `host`: The address on which the server will run.
    - `port`: The port on which the server will run.
    - `allowed_ips`: A list of allowed IP addresses for accessing the server.

- `add_route(path: str, handler: Callable, method: str = 'GET') -> None`
  - Adds a route to the application.
  - **Parameters:**
    - `path`: The route path.
    - `handler`: The handler function for this route.
    - `method`: The HTTP method (default 'GET').

- `run_webserver() -> None`
  - Starts the web server.

- `ip_check_middleware(request: web.Request, handler: Callable) -> web.Response`
  - Middleware for checking client IP addresses.
  - **Parameters:**
    - `request`: The HTTP request.
    - `handler`: The handler function for processing the request.

## Exceptions

- `ServerSetupFailed`: Exception for errors during server setup.
- `ServerStartFailed`: Exception for errors during server startup.
- `AllowedIPsEmpty`: Exception for when the list of allowed IP addresses is empty.

## License

This project is licensed under the MIT License.
