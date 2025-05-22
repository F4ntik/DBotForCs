import pytest
from unittest.mock import MagicMock # Still useful for creating standalone mocks if needed
import logging # For type hinting if necessary, not strictly for runtime here
import traceback

# Removed sys.path.insert and os import, conftest.py handles the path.

# Corrected import for Log class based on project structure
from logger.log import Log

@pytest.fixture
def mocked_log_init(mocker):
    """
    Mocks logging.getLogger calls that happen inside Log.__init__.
    Returns the mock objects for info and error loggers.
    """
    mock_info_logger = MagicMock()
    mock_error_logger = MagicMock()
    
    # Configure the mock for logging.getLogger
    # This mock will be used by Log.__init__ when it calls logging.getLogger
    mock_getLogger = mocker.patch('logging.getLogger')
    
    # Define the side_effect for multiple calls if Log() calls getLogger multiple times
    # with different names, or if the order is fixed.
    # The original test implies Log() results in two getLogger calls, one for info, one for error.
    # Let's assume Log class calls logging.getLogger('info_logger_name_placeholder')
    # and logging.getLogger('error_logger_name_placeholder') internally, or just two sequential calls.
    # The original test used: mock_get_logger.side_effect = [self.mock_info_logger, self.mock_error_logger]
    # This means Log() must call logging.getLogger() twice, and these are the instances it gets.
    mock_getLogger.side_effect = [mock_info_logger, mock_error_logger]
    
    return mock_info_logger, mock_error_logger

@pytest.fixture
def log_instance(mocked_log_init):
    """
    Provides a Log instance that has its internal loggers mocked by mocked_log_init.
    Also returns the mock loggers for assertion.
    """
    mock_info_logger, mock_error_logger = mocked_log_init
    
    # When Log() is instantiated, its calls to logging.getLogger will use the
    # patched version from mocked_log_init fixture.
    log = Log()
    
    # Return the Log instance and the individual mocks for easy assertion in tests
    return log, mock_info_logger, mock_error_logger

def test_info_logging(log_instance):
    log, mock_info_logger, _ = log_instance # Unpack the tuple from fixture
    message = "This is an info message"
    
    log.info(message)
    
    mock_info_logger.info.assert_called_once_with(message)

def test_error_logging(log_instance):
    log, _, mock_error_logger = log_instance # Unpack the tuple from fixture
    message = "This is an error message"
    
    log.error(message)
    
    mock_error_logger.error.assert_called_once_with(message)

def test_exception_logging(log_instance, mocker): # Add mocker for patching traceback
    log, _, mock_error_logger = log_instance # Unpack the tuple
    
    # Mock traceback.format_exc for this test
    mock_format_exc = mocker.patch('traceback.format_exc')
    
    message = "This is an exception message"
    traceback_output = "Traceback (most recent call last): ..."
    mock_format_exc.return_value = traceback_output
    
    log.exception(message)
    
    mock_error_logger.error.assert_called_once_with(f"{message}\n{traceback_output}")

# Removed if __name__ == '__main__': unittest.main() block.
# Unittest class TestLog and its setUp method are replaced by fixtures and test functions.
# Assertions remain the same as they are unittest.mock assertions, compatible with pytest.
# Imports updated (pytest, removed os, sys, unittest).
# `pytest-mock` (and its `mocker` fixture) is assumed to be available.
# If `pytest-mock` is not installed, `pip install pytest-mock` would be needed.
# The solution relies on `pytest-mock` for `mocker.patch`.
# The original `Log` class seems to call `logging.getLogger()` twice upon instantiation.
# The `mocked_log_init` fixture replicates this by setting `side_effect` on the patched `logging.getLogger`.
# The `log_instance` fixture then creates `Log()` which gets these mocked loggers,
# and returns the `Log` instance along with the mocks for tests to use.
