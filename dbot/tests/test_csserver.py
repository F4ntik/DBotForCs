import pytest
from unittest.mock import MagicMock # unittest.mock.MagicMock is fine for basic mocks
# If RCON methods were async, we might need mocker.AsyncMock, but CSServer's methods are async.
# The original tests use MagicMock for rcon.connect and rcon.execute.

# Corrected import path based on conftest.py
# Assumes CSServer and its exceptions are in cs_server.cs_server
from cs_server.cs_server import CSServer, ConnectionError as CSServerConnectionError, StatusError, CommandExecutionError
# Aliased ConnectionError for clarity, matching previous attempts.

@pytest.fixture
def cs_server_instance():
    """Provides a basic CSServer instance."""
    # Host and password are placeholders as the RCON client will be mocked.
    return CSServer(host="localhost", password="password")

@pytest.mark.asyncio
async def test_connect_to_server_success(cs_server_instance: CSServer, mocker):
    # Mock the RCON class constructor and its instance methods
    mock_rcon_class = mocker.patch('rehlds.rcon.RCON') # Patches 'rehlds.rcon.RCON' in the context of where CSServer might import/use it
    mock_rcon_object = MagicMock() # This is the object that RCON() would return
    mock_rcon_object.connect = MagicMock() # connect method on the RCON instance
    
    mock_rcon_class.return_value = mock_rcon_object # When RCON() is called, it returns our mock_rcon_object

    # Crucial: Mimic the original test's setup where the server's RCON client attribute is replaced.
    # This assumes CSServer initializes or allows setting an attribute like 'cs_server'
    # that holds the RCON client. The original test did: self.server.cs_server = mock_rcon.return_value
    # If CSServer instantiates RCON internally when connect_to_server is called, this might need adjustment.
    # However, the original test structure implies cs_server is an attribute that's set.
    cs_server_instance.cs_server = mock_rcon_object

    try:
        await cs_server_instance.connect_to_server()
    except CSServerConnectionError: # Use the aliased exception name
        pytest.fail("connect_to_server raised CSServerConnectionError unexpectedly!")
    
    mock_rcon_object.connect.assert_called_once()

@pytest.mark.asyncio
async def test_connect_to_server_failure(cs_server_instance: CSServer, mocker):
    mock_rcon_class = mocker.patch('rehlds.rcon.RCON')
    mock_rcon_object = MagicMock()
    mock_rcon_object.connect = MagicMock(side_effect=Exception("Connection failed"))
    mock_rcon_class.return_value = mock_rcon_object
    
    cs_server_instance.cs_server = mock_rcon_object

    with pytest.raises(CSServerConnectionError, match="Ошибка подключения: Connection failed"):
        await cs_server_instance.connect_to_server()
    
    mock_rcon_object.connect.assert_called_once()

@pytest.mark.asyncio
async def test_fetch_status_success(cs_server_instance: CSServer, mocker):
    mock_rcon_class = mocker.patch('rehlds.rcon.RCON')
    mock_rcon_object = MagicMock()
    expected_status_output = "Server status is good"
    mock_rcon_object.execute = MagicMock(return_value=expected_status_output)
    mock_rcon_class.return_value = mock_rcon_object

    cs_server_instance.cs_server = mock_rcon_object

    try:
        status_result = await cs_server_instance.fetch_status()
        assert status_result == expected_status_output
    except StatusError:
        pytest.fail("fetch_status raised StatusError unexpectedly!")
        
    mock_rcon_object.execute.assert_called_once_with("status")

@pytest.mark.asyncio
async def test_fetch_status_failure(cs_server_instance: CSServer, mocker):
    mock_rcon_class = mocker.patch('rehlds.rcon.RCON')
    mock_rcon_object = MagicMock()
    mock_rcon_object.execute = MagicMock(side_effect=Exception("Status fetch failed"))
    mock_rcon_class.return_value = mock_rcon_object

    cs_server_instance.cs_server = mock_rcon_object

    with pytest.raises(StatusError, match="Ошибка получения статуса: Status fetch failed"):
        await cs_server_instance.fetch_status()
        
    mock_rcon_object.execute.assert_called_once_with("status")

@pytest.mark.asyncio
async def test_exec_success(cs_server_instance: CSServer, mocker):
    mock_rcon_class = mocker.patch('rehlds.rcon.RCON')
    mock_rcon_object = MagicMock()
    command_to_run = "test_server_command"
    expected_command_output = "Command ran successfully"
    mock_rcon_object.execute = MagicMock(return_value=expected_command_output)
    mock_rcon_class.return_value = mock_rcon_object

    cs_server_instance.cs_server = mock_rcon_object

    try:
        result = await cs_server_instance.exec(command_to_run)
        assert result == expected_command_output
    except CommandExecutionError:
        pytest.fail("exec raised CommandExecutionError unexpectedly!")
        
    mock_rcon_object.execute.assert_called_once_with(command_to_run)

@pytest.mark.asyncio
async def test_exec_failure(cs_server_instance: CSServer, mocker):
    mock_rcon_class = mocker.patch('rehlds.rcon.RCON')
    mock_rcon_object = MagicMock()
    command_to_run = "failing_server_command"
    mock_rcon_object.execute = MagicMock(side_effect=Exception("Command execution failed"))
    mock_rcon_class.return_value = mock_rcon_object

    cs_server_instance.cs_server = mock_rcon_object

    with pytest.raises(CommandExecutionError, match="Ошибка выполнения команды: Command execution failed"):
        await cs_server_instance.exec(command_to_run)
        
    mock_rcon_object.execute.assert_called_once_with(command_to_run)

# Note: The original test file `dbot/tests/test_csserver.py` uses `@patch('rehlds.rcon.RCON')`
# as a decorator for each test method. This passes a `mock_rcon` argument to the test method,
# which is the mocked *class*. Then, `self.server.cs_server = mock_rcon.return_value` is used.
# The pytest equivalent here uses `mocker.patch('rehlds.rcon.RCON')` to get the mocked class,
# then we create a `MagicMock()` for what `RCON()` would return (`mock_rcon_object`),
# and assign that to `mock_rcon_class.return_value`.
# Finally, `cs_server_instance.cs_server = mock_rcon_object` achieves the same attribute mocking.
# This assumes `rehlds.rcon.RCON` is the correct path that CSServer uses to get the RCON class.
# If CSServer imports RCON like `from rehlds import rcon` and uses `rcon.RCON()`,
# then the path to patch might need to be `cs_server.cs_server.rcon.RCON`
# or wherever it's actually referenced in the `cs_server.py` module.
# For now, 'rehlds.rcon.RCON' is used as per the original test's patching.
# The key is that the `cs_server_instance.cs_server` attribute is what gets the final mock instance.
