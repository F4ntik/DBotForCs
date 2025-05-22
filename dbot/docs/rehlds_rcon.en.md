# RCON Module

This module implements a client for remote server management via RCON (Remote Console). It supports connecting to a server, executing commands, and handling errors.

## Installation

No additional dependencies are required to use this module as it uses standard Python libraries.

## Classes

### RCON

A class for creating and managing a connection to an RCON server.

#### Attributes

- `host` (str): The server host address.
- `port` (int): The server port (default 27015).
- `password` (str): The RCON password.
- `sock` (Optional[socket.socket]): The socket for connecting to the server.

#### Methods

- `__init__(host: str, port: int = 27015, password: str) -> None`
  - Initializes an instance of the RCON class.
  - **Parameters:**
    - `host`: The server host address.
    - `port`: The server port (default 27015).
    - `password`: The RCON password.

- `connect(timeout: int = 6) -> None`
  - Connects to the RCON server.
  - **Parameters:**
    - `timeout`: Connection timeout in seconds.

- `disconnect() -> None`
  - Disconnects from the RCON server.

- `getChallenge() -> str`
  - Retrieves a challenge from the server.
  - **Returns:**
    - The challenge string.

- `execute(cmd: str) -> str`
  - Executes a command on the server.
  - **Parameters:**
    - `cmd`: The command to execute.
  - **Returns:**
    - The result of the command execution.

## Exceptions

- `RCONError`: Base class for RCON exceptions.
- `BadRCONPassword`: Exception for an incorrect RCON password.
- `BadConnection`: Exception for connection errors.
- `ServerOffline`: Exception for an offline server.
- `NoConnection`: Exception for no connection.

## License

This project is licensed under the MIT License.
