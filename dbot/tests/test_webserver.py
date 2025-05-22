import pytest
from aiohttp import web

# Removed sys.path.insert and os import, conftest.py handles the path.
# Removed unittest import.

# Updated import for WebServer and its exceptions
from webserver.web_server import WebServer, AllowedIPsEmpty, ServerSetupFailed, ServerStartFailed

# Handler function as defined in the original test
async def example_handler(request: web.Request) -> web.Response:
    return web.Response(text="Hello, world!")

@pytest.fixture
def base_server_config():
    """Provides a base configuration for the WebServer."""
    return {'host': '127.0.0.1', 'port': 8080, 'allowed_ips': ['127.0.0.1']}

@pytest.fixture
def web_server_instance(base_server_config):
    """Fixture to create a WebServer instance with default config."""
    return WebServer(**base_server_config)

@pytest.fixture
def app(web_server_instance: WebServer):
    """
    Fixture that provides the aiohttp app from a WebServer instance.
    This is used by aiohttp_client.
    """
    web_server_instance.add_route('/test', example_handler)
    return web_server_instance.app

# --- Tests for initialization (do not require aiohttp_client) ---
def test_initialization_with_empty_allowed_ips():
    """Test WebServer initialization with an empty list of allowed IP addresses."""
    with pytest.raises(AllowedIPsEmpty):
        WebServer(host='127.0.0.1', port=8080, allowed_ips=[])

def test_initialization_with_invalid_port(base_server_config):
    """Test WebServer initialization with invalid port numbers."""
    config_invalid_low = base_server_config.copy()
    config_invalid_low['port'] = 0
    with pytest.raises(ServerSetupFailed):
        WebServer(**config_invalid_low)
    
    config_invalid_high = base_server_config.copy()
    config_invalid_high['port'] = 70000
    with pytest.raises(ServerSetupFailed):
        WebServer(**config_invalid_high)

# --- Tests for server behavior using aiohttp_client ---
@pytest.mark.asyncio
async def test_ip_check_middleware_allowed_ip(aiohttp_client, app):
    """Test that requests from an allowed IP address are successful."""
    client = await aiohttp_client(app)
    response = await client.get('/test')
    assert response.status == 200
    text = await response.text()
    assert text == 'Hello, world!'

@pytest.mark.asyncio
async def test_ip_check_middleware_denied_ip(aiohttp_client, base_server_config):
    """Test that requests from a denied IP address are forbidden."""
    # Create a specific WebServer instance for this test with modified allowed_ips
    config_denied = base_server_config.copy()
    config_denied['allowed_ips'] = ['1.2.3.4'] # A different IP not matching client default
    
    temp_web_server = WebServer(**config_denied)
    temp_web_server.add_route('/test', example_handler) # Add route to this instance
    
    client = await aiohttp_client(temp_web_server.app)
    response = await client.get('/test')
    assert response.status == 403
    text = await response.text()
    assert text == 'Access Forbidden: Your IP is not allowed.'

# --- Tests for run_webserver method (these are a bit tricky as run_webserver typically blocks) ---
# The original tests for run_webserver were likely not testing actual server run, 
# but rather setup errors before the server starts blocking.
# We will replicate that by checking for exceptions during the setup phase of run_webserver.
# Note: Actually starting and stopping the server for a test is more involved and
# usually handled by pytest-aiohttp's server fixture if testing against a live server process.
# Here, we're testing WebServer's internal logic before it hits `web.run_app`.

@pytest.mark.asyncio
async def test_run_webserver_setup_failure_invalid_host(mocker, base_server_config):
    """Test run_webserver detects setup failure with an invalid host."""
    # We need to mock web.run_app to prevent actual server start
    mocker.patch('aiohttp.web.run_app') 
    
    config_invalid_host = base_server_config.copy()
    config_invalid_host['host'] = None # Invalid host
    
    server_invalid_host = WebServer(**config_invalid_host)
    server_invalid_host.add_route('/test', example_handler)

    with pytest.raises(ServerSetupFailed):
        # run_webserver itself is not async in the original class, but it might call async methods
        # or the error occurs before any async part. Let's assume it's okay to call directly.
        # If run_webserver becomes async: await server_invalid_host.run_webserver()
        server_invalid_host.run_webserver() 

@pytest.mark.asyncio
async def test_run_webserver_start_failure_invalid_port(mocker, base_server_config):
    """Test run_webserver detects start failure with an invalid port (mocking run_app)."""
    mock_run_app = mocker.patch('aiohttp.web.run_app')
    # Simulate an error during run_app, e.g., port already in use or other OS level error
    mock_run_app.side_effect = OSError("Simulated OS error on run_app, e.g. port unavailable")

    config_bad_port_sim = base_server_config.copy() 
    # Port itself is valid for setup, but we simulate run_app failing for it
    
    server_bad_port_sim = WebServer(**config_bad_port_sim)
    server_bad_port_sim.add_route('/test', example_handler)

    # The original test expected ServerStartFailed. This implies WebServer catches OSError
    # from web.run_app and re-raises it as ServerStartFailed.
    with pytest.raises(ServerStartFailed):
        server_bad_port_sim.run_webserver()

@pytest.mark.asyncio
async def test_successful_server_start_mocked(mocker, web_server_instance: WebServer):
    """
    Test that run_webserver proceeds without error if setup is fine (mocking actual server run).
    """
    mock_run_app = mocker.patch('aiohttp.web.run_app') # Mock web.run_app
    
    try:
        # web_server_instance already has /test route from 'app' fixture dependency if we reuse it,
        # but 'app' fixture is for client tests.
        # Let's use a fresh instance or ensure state is clean.
        # For this test, web_server_instance from fixture is fine, as its app isn't run by client.
        web_server_instance.run_webserver() 
        mock_run_app.assert_called_once() # Verify that web.run_app was called
    except Exception as e:
        pytest.fail(f"Server failed to logically start with valid parameters: {e}")

# Removed if __name__ == '__main__': unittest.main() block
# Removed AioHTTPTestCase class structure and @unittest_run_loop decorators.
# Converted assertions to pytest style.
# Used aiohttp_client fixture for making requests.
# Handled test-specific state changes by creating new WebServer instances where necessary.
# Mocked aiohttp.web.run_app for tests involving `run_webserver` to prevent actual server start.
