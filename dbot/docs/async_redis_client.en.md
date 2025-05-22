## Requirements

To work with the `AsyncRedisClient` class, you need to install the following non-standard modules:

`pip install redis`

## Classes

### AsyncRedisClient

A class for asynchronous interaction with Redis.

#### Attributes

- `host` (str): The Redis host address.
- `port` (int): The Redis port.
- `db` (int): The Redis database number.
- `client` (Optional[aioredis.Redis]): An instance of the Redis client.

#### Methods

- `__init__(host: str = '127.0.0.1', port: int = 6379, db: int = 0) -> None`
  - Initializes an instance of the Redis client.
  - **Parameters:**
    - `host`: The Redis host address (default '127.0.0.1').
    - `port`: The Redis port (default 6379).
    - `db`: The Redis database number (default 0).

- `async def connect() -> None`
  - Connects the client to Redis and checks the connection using the `PING` command.

- `async def set(key: str, value: Union[str, bytes]) -> None`
  - Sets a value for the specified key.
  - **Parameters:**
    - `key`: The key for which the value will be set.
    - `value`: The value to be set (string or bytes).

- `async def get(key: str) -> Optional[Union[str, bytes]]`
  - Retrieves the value for the specified key.
  - **Parameters:**
    - `key`: The key for which the value will be retrieved.

- `async def delete(key: str) -> int`
  - Deletes the specified key.
  - **Parameters:**
    - `key`: The key to be deleted.

- `async def exists(key: str) -> bool`
  - Checks if the specified key exists.
  - **Parameters:**
    - `key`: The key whose existence will be checked.

- `async def keys(pattern: str = '*') -> List[str]`
  - Returns a list of keys matching the specified pattern.
  - **Parameters:**
    - `pattern`: The pattern for searching keys (default '*').

- `async def close() -> None`
  - Closes the connection to Redis.

## Exceptions

- `RedisError`: Base class for all Redis-related exceptions.
- `RedisConnectionError`: Exception raised for errors during connection to Redis.
- `RedisSetError`: Exception raised for errors when setting a value in Redis.
- `RedisGetError`: Exception raised for errors when retrieving a value from Redis.
- `RedisDeleteError`: Exception raised for errors when deleting a key from Redis.
- `RedisExistsError`: Exception raised for errors when checking key existence in Redis.
- `RedisKeysError`: Exception raised for errors when retrieving keys from Redis.

## License

This project is licensed under the MIT License.
