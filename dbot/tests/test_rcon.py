import pytest
import asyncio # Required for @pytest.mark.asyncio if not using pytest-asyncio plugin explicitly in older pytest

# sys.path.insert line removed, conftest.py handles this.
# os import removed as it's no longer used.
# unittest import removed.

from rehlds.rcon import RCON, BadRCONPassword, BadConnection, NoConnection, ServerOffline # Import necessary exceptions

# RCON server configuration (consider making these environment variables or configurable)
RCON_HOST = '127.0.0.1'
RCON_PORT = 27015
RCON_PASSWORD = '12345' # Replace with your actual RCON password for testing

@pytest.fixture
async def rcon_client(): # Fixture can be async to align with async tests, though RCON ops are sync
    """
    Pytest fixture to set up and tear down an RCON connection.
    """
    rcon = RCON(host=RCON_HOST, port=RCON_PORT, password=RCON_PASSWORD)
    try:
        rcon.connect() # Synchronous connect
    except (BadRCONPassword, BadConnection, ServerOffline, ConnectionRefusedError) as e: # Catch specific connection errors
        pytest.fail(f"Failed to connect to RCON server at {RCON_HOST}:{RCON_PORT}: {e}. Ensure server is running and password is correct.")
        return None # Should not be reached due to pytest.fail
        
    yield rcon  # Provide the connected rcon instance to the test
    
    # Teardown: disconnect from RCON server
    # Ensure disconnect is called even if connect failed but didn't raise an error caught above (unlikely here)
    if rcon.sock: # Check if socket exists, implying a connection attempt was made
        try:
            rcon.disconnect() # Synchronous disconnect
        except NoConnection: # It might already be disconnected or failed to connect properly
            pass 
        except Exception as e: # Catch any other disconnect errors
            print(f"Error during RCON disconnect: {e}") # Log, but don't fail test for teardown issues

@pytest.mark.asyncio
async def test_rcon_connect_and_execute_status(rcon_client: RCON):
    """
    Tests connecting to the RCON server and executing the 'status' command.
    """
    if rcon_client is None: # Should be handled by pytest.fail in fixture
        pytest.skip("Skipping test due to failed RCON connection.")

    command_to_execute = 'status' # Using 'status' as a less impactful command
    
    try:
        response = rcon_client.execute(command_to_execute)
        assert isinstance(response, str), f"Expected response to be a string, got {type(response)}"
        # Optionally, check for content specific to 'status' command if output is predictable
        # For example:
        assert "hostname:" in response, "The 'status' command response should contain 'hostname:'"
        assert "version :" in response, "The 'status' command response should contain 'version :'"
        assert "map     :" in response, "The 'status' command response should contain 'map     :'"
        print(f"RCON command '{command_to_execute}' executed successfully. Response snippet: {response[:100]}...") # Optional: for test output
    except (BadRCONPassword, BadConnection, NoConnection, ServerOffline) as e: # RCON-specific errors for execute
        pytest.fail(f"RCON command '{command_to_execute}' failed: {e}")
    except Exception as e: # Catch any other unexpected errors during command execution
        pytest.fail(f"An unexpected error occurred during RCON command '{command_to_execute}': {e}")

# Removed the old TestRCON class and if __name__ == '__main__' block.
# print(response) from original test_connect_and_execute_command is removed,
# but an optional print with snippet is added for verbosity if desired during testing.
# Added more specific RCON exceptions to import and error handling.
# Made RCON connection parameters constants for clarity.
# Added more assertions to 'status' command output for robustness.
# Improved teardown in fixture to be more resilient.
