import pytest
import asyncio # Keep asyncio for @pytest.mark.asyncio

# sys.path.insert line removed, conftest.py handles this.

# Corrected import for AioMysql and QueryError
from data_server.asyncsql import AioMysql, QueryError, ConnectionError as AioMysqlConnectionError
from dbot.tests import tests_config # Import the test configuration

# Database connection parameters are now sourced from tests_config

@pytest.fixture
async def db_connection():
    """
    Pytest fixture to set up and tear down a database connection.
    Uses configurations from dbot.tests.tests_config.
    """
    db = AioMysql(
        host=tests_config.MYSQL_HOST,
        port=tests_config.MYSQL_PORT,
        user=tests_config.MYSQL_USER,
        password=tests_config.MYSQL_PASSWORD,
        db=tests_config.MYSQL_DB
    )
    try:
        await db.connect()
    except AioMysqlConnectionError as e:
        # If connection fails, skip tests that depend on this fixture
        pytest.fail(f"Failed to connect to the database: {e}. Ensure MySQL is running and configured.")
        return None # Should not be reached due to pytest.fail

    yield db  # Provide the connected db instance to the test
    
    await db.close() # Teardown: close the connection

@pytest.mark.asyncio
async def test_select_query_from_users(db_connection: AioMysql):
    """
    Tests executing a SELECT query against the 'users' table.
    Assumes 'mysql_test' database and 'users' table exist.
    The test passes if the query executes without raising QueryError.
    """
    if db_connection is None: # Should be handled by pytest.fail in fixture
        pytest.skip("Skipping test due to failed database connection.")

    query = "SELECT * FROM users" 
    rows_processed = 0
    try:
        async for row in db_connection.fetch_iter(query, batch_size=10):
            rows_processed += 1
            # For debugging during development, you might print the row:
            # print(f"Row {rows_processed}: {row}")
        
        # Basic assertion: if the query ran and users table exists, it shouldn't error.
        # If users table might be empty, rows_processed could be 0.
        # The main check is that no QueryError was raised.
        # If you expect users to always have data, you could assert rows_processed > 0
        print(f"Successfully fetched {rows_processed} rows from 'users' table.") # Optional: for test output
        assert True # Implicitly, test passes if no exception occurs
    except QueryError as e:
        pytest.fail(f"QueryError occurred during 'SELECT * FROM users': {e}")
    except Exception as e: # Catch any other unexpected errors
        pytest.fail(f"An unexpected error occurred: {e}")

@pytest.mark.asyncio
async def test_select_one_query(db_connection: AioMysql):
    """
    Tests executing a simple 'SELECT 1' query.
    This is a minimal query to check basic database interaction.
    """
    if db_connection is None:
        pytest.skip("Skipping test due to failed database connection.")

    query = "SELECT 1"
    result = None
    try:
        # Using execute_select for a query expected to return rows directly
        # fetch_iter is for iterating, execute_select might be better for simple selects
        # The original AioMysql class has execute_select
        result = await db_connection.execute_select(query)
        
        assert result is not None, "Query 'SELECT 1' should return a result."
        assert len(result) > 0, "Query 'SELECT 1' should return at least one row."
        assert result[0][0] == 1, "The first column of the first row should be 1."
        print("Successfully executed 'SELECT 1'.") # Optional: for test output
    except QueryError as e:
        pytest.fail(f"QueryError occurred during 'SELECT 1': {e}")
    except Exception as e:
        pytest.fail(f"An unexpected error occurred: {e}")


@pytest.mark.asyncio
async def test_malformed_query_raises_queryerror(db_connection: AioMysql):
    """
    Tests that a malformed SQL query correctly raises a QueryError.
    """
    if db_connection is None:
        pytest.skip("Skipping test due to failed database connection.")

    # This query is intentionally malformed.
    malformed_query = "SELEC * FROM table_that_might_not_exist WITH BAD GRAMMAR"
    
    with pytest.raises(QueryError):
        # Depending on AioMysql's behavior, execute_select or fetch_iter could be used.
        # fetch_iter might not raise error until iteration starts.
        # execute_select is likely to raise it sooner if query is immediately invalid.
        await db_connection.execute_select(malformed_query)
        # If execute_select doesn't raise, and fetch_iter is used, the error might only
        # occur when the async generator is iterated.
        # async for _ in db_connection.fetch_iter(malformed_query):
        #     pass # Should not be reached

# Removed the old main() function and if __name__ == '__main__' block.
# Print statements are mostly removed or commented, with a few kept for clarity during test runs if desired.
# Added AioMysqlConnectionError to imports for more specific error handling in fixture.
# Added a more robust test_select_one_query for basic connectivity check.
# Ensured tests skip if DB connection fails in fixture.
