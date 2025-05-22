import pytest
import asyncio
from data_server.redis_client import AsyncRedisClient, RedisConnectionError, RedisSetError, RedisGetError

# It's good practice to ensure the event loop is handled correctly for all tests,
# especially when mixing asyncio and pytest. Pytest-asyncio handles this.
# If not already installed, pytest-asyncio might be needed.
# pip install pytest-asyncio

@pytest.fixture
async def redis_client():
    client = AsyncRedisClient(host='localhost', port=6379, db=0) # Assuming default Redis connection
    try:
        await client.connect()
    except RedisConnectionError as e:
        pytest.fail(f"Failed to connect to Redis: {e}")
    
    yield client # Provide the connected client to the test
    
    # Teardown: Clean up any keys used in tests and close connection
    # This is a simple cleanup; more sophisticated key management might be needed for complex tests
    await client.delete("test_key_pytest") 
    await client.close()

@pytest.mark.asyncio
async def test_redis_operations(redis_client: AsyncRedisClient):
    key = "test_key_pytest"
    value = "test_value_pytest"

    # Test SET operation
    try:
        await redis_client.set(key, value)
    except RedisSetError as e:
        pytest.fail(f"Failed to set key '{key}': {e}")

    # Test GET operation
    retrieved_value_bytes = await redis_client.get(key)
    assert retrieved_value_bytes is not None, f"Key '{key}' should exist after set."
    # Assuming get returns bytes, decode to string for comparison
    retrieved_value = retrieved_value_bytes.decode('utf-8')
    assert retrieved_value == value, f"Retrieved value '{retrieved_value}' does not match expected '{value}'."

    # Test EXISTS operation
    exists = await redis_client.exists(key)
    assert exists is True, f"Key '{key}' should exist after set."

    # Test DELETE operation
    await redis_client.delete(key)
    
    # Test EXISTS operation after delete
    exists_after_delete = await redis_client.exists(key)
    assert exists_after_delete is False, f"Key '{key}' should not exist after delete."

@pytest.mark.asyncio
async def test_redis_get_non_existent_key(redis_client: AsyncRedisClient):
    key = "non_existent_key_pytest"
    # Ensure the key doesn't exist before testing get
    await redis_client.delete(key) 
    
    retrieved_value = await redis_client.get(key)
    assert retrieved_value is None, f"Getting a non-existent key '{key}' should return None."

@pytest.mark.asyncio
async def test_redis_delete_non_existent_key(redis_client: AsyncRedisClient):
    key = "non_existent_key_for_delete_pytest"
    # Ensure the key doesn't exist
    await redis_client.delete(key)
    
    # Deleting a non-existent key should not raise an error and return 0 (or a similar value indicating no key was deleted)
    # The exact return value depends on the redis client library's implementation for `delete`
    delete_result = await redis_client.delete(key)
    assert delete_result == 0, "Deleting a non-existent key should result in 0 keys deleted."
    
    exists_after_delete = await redis_client.exists(key)
    assert exists_after_delete is False, f"Key '{key}' should still not exist after attempting to delete a non-existent key."
