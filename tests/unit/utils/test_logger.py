import pytest
from unittest.mock import patch
from src.utils.logger import info, success, warn, error

@patch('src.utils.logger.print')
def test_info_logging(mock_print):
    message = "Test info message"
    info(message)
    mock_print.assert_called_once_with(f"[cyan]➤ {message}")

@patch('src.utils.logger.print')
def test_success_logging(mock_print):
    message = "Test success message"
    success(message)
    mock_print.assert_called_once_with(f"[green]✔ {message}")

@patch('src.utils.logger.print')
def test_warn_logging(mock_print):
    message = "Test warning message"
    warn(message)
    mock_print.assert_called_once_with(f"[yellow]⚠ {message}")

@patch('src.utils.logger.print')
def test_error_logging(mock_print):
    message = "Test error message"
    error(message)
    mock_print.assert_called_once_with(f"[red]✖ {message}") 
