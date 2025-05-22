## Requirements

To work with the `CSServer` class, you need to install the following non-standard modules:

- `rehlds`: A library for working with RCON connections for servers using ReHLDS.

## Classes

### CSServer

A class for interacting with a Counter-Strike server via RCON.

#### Attributes

- `cs_server` (RCON): An RCON instance for connecting to the server.

#### Methods

- `__init__(host: str, password: str) -> None`
  - Initializes an instance of CSServer.
  - **Parameters:**
    - `host`: The server address.
    - `password`: The password for connecting to the server.

- `async def connect_to_server() -> None`
  - Connects to the CS server and returns the status.
  - **Exceptions:**
    - `ConnectionError`: If it failed to connect to the server.

- `async def fetch_status() -> None`
  - Retrieves the server status.
  - **Exceptions:**
    - `ServerNotConnected`: If the server is not connected.
    - `StatusError`: If an error occurred while retrieving the server status.

- `async def exec(command: str) -> str`
  - Executes a command on the server.
  - **Parameters:**
    - `command`: The command to execute.
  - **Exceptions:**
    - `CommandExecutionError`: If an error occurred while executing the command.

## Exceptions

- `CSServerError`: Base class for all exceptions related to CSServer.
- `ServerNotConnected`: Exception for when the server is not connected.
- `ConnectionError`: Exception for server connection errors.
- `StatusError`: Exception for errors when retrieving server status.
- `CommandExecutionError`: Exception for errors when executing a command on the server.

## License

This project is licensed under the MIT License.
