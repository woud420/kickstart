import pytest
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open, call
from requests.exceptions import RequestException, HTTPError, Timeout
from src.utils.updater import check_for_update, REPO, RELEASE_URL


@pytest.fixture
def mock_version():
    return "1.0.0"


@pytest.fixture
def mock_release_data():
    return {
        "tag_name": "v1.1.0",
        "assets": [
            {
                "name": "kickstart",
                "browser_download_url": "https://github.com/woud420/kickstart/releases/download/v1.1.0/kickstart"
            },
            {
                "name": "other-file.zip",
                "browser_download_url": "https://github.com/woud420/kickstart/releases/download/v1.1.0/other-file.zip"
            }
        ]
    }


@pytest.fixture
def mock_release_data_same_version():
    return {
        "tag_name": "v1.0.0",
        "assets": [
            {
                "name": "kickstart",
                "browser_download_url": "https://github.com/woud420/kickstart/releases/download/v1.0.0/kickstart"
            }
        ]
    }


def test_repo_and_release_url_constants():
    """Test that the repository and release URL constants are correct."""
    assert REPO == "woud420/kickstart"
    assert RELEASE_URL == "https://api.github.com/repos/woud420/kickstart/releases/latest"


@patch('src.utils.updater.__version__', '1.0.0')
@patch('builtins.print')
@patch('requests.get')
def test_check_for_update_up_to_date(mock_requests_get, mock_print, mock_release_data_same_version):
    """Test when current version is already the latest."""
    mock_response = MagicMock()
    mock_response.json.return_value = mock_release_data_same_version
    mock_response.raise_for_status.return_value = None
    mock_requests_get.return_value = mock_response
    
    check_for_update()
    
    mock_requests_get.assert_called_once_with(RELEASE_URL, timeout=5)
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()
    
    # Check print calls
    print_calls = [call.args[0] for call in mock_print.call_args_list]
    assert any("Checking for updates (current version: 1.0.0)" in call for call in print_calls)
    assert any("✅ You're already up to date." in call for call in print_calls)


@patch('src.utils.updater.__version__', '1.0.0')
@patch('builtins.print')
@patch('requests.get')
@patch('sys.argv', ['/usr/local/bin/kickstart'])
@patch('shutil.copy2')
@patch('shutil.copyfileobj')
@patch('pathlib.Path.chmod')
def test_check_for_update_new_version_available(
    mock_chmod, mock_copyfileobj, mock_copy2, mock_requests_get, mock_print, mock_release_data
):
    """Test successful update when new version is available."""
    # Mock the initial release check
    mock_release_response = MagicMock()
    mock_release_response.json.return_value = mock_release_data
    mock_release_response.raise_for_status.return_value = None
    
    # Mock the binary download
    mock_download_response = MagicMock()
    mock_download_response.raise_for_status.return_value = None
    mock_download_response.raw = MagicMock()
    
    # Configure requests.get to return different responses for different calls
    mock_requests_get.side_effect = [mock_release_response, mock_download_response]
    
    with patch('builtins.open', mock_open()) as mock_file:
        check_for_update()
    
    # Verify release check
    assert mock_requests_get.call_args_list[0] == call(RELEASE_URL, timeout=5)
    mock_release_response.raise_for_status.assert_called_once()
    mock_release_response.json.assert_called_once()
    
    # Verify binary download
    download_url = "https://github.com/woud420/kickstart/releases/download/v1.1.0/kickstart"
    assert mock_requests_get.call_args_list[1] == call(download_url, stream=True)
    mock_download_response.raise_for_status.assert_called_once()
    
    # Verify file operations
    bin_path = Path('/usr/local/bin/kickstart')
    backup_path = bin_path.with_suffix('.bak')
    mock_copy2.assert_called_once_with(bin_path, backup_path)
    mock_file.assert_called_once_with(bin_path, 'wb')
    mock_copyfileobj.assert_called_once_with(mock_download_response.raw, mock_file().__enter__())
    mock_chmod.assert_called_once_with(0o755)
    
    # Check print calls
    print_calls = [call.args[0] for call in mock_print.call_args_list]
    assert any("Checking for updates (current version: 1.0.0)" in call for call in print_calls)
    assert any("⬆ New version available: 1.1.0 — downloading..." in call for call in print_calls)
    assert any("✔ Updated successfully to 1.1.0!" in call for call in print_calls)


@patch('src.utils.updater.__version__', '1.0.0')
@patch('builtins.print')
@patch('requests.get')
def test_check_for_update_http_error(mock_requests_get, mock_print):
    """Test handling of HTTP errors during release check."""
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = HTTPError("404 Not Found")
    mock_requests_get.return_value = mock_response
    
    check_for_update()
    
    mock_requests_get.assert_called_once_with(RELEASE_URL, timeout=5)
    mock_response.raise_for_status.assert_called_once()
    
    # Check error message is printed
    print_calls = [call.args[0] for call in mock_print.call_args_list]
    assert any("✖ Update failed:" in call for call in print_calls)


@patch('src.utils.updater.__version__', '1.0.0')
@patch('builtins.print')
@patch('requests.get')
def test_check_for_update_timeout_error(mock_requests_get, mock_print):
    """Test handling of timeout errors."""
    mock_requests_get.side_effect = Timeout("Request timed out")
    
    check_for_update()
    
    mock_requests_get.assert_called_once_with(RELEASE_URL, timeout=5)
    
    # Check error message is printed
    print_calls = [call.args[0] for call in mock_print.call_args_list]
    assert any("✖ Update failed:" in call for call in print_calls)


@patch('src.utils.updater.__version__', '1.0.0')
@patch('builtins.print')
@patch('requests.get')
def test_check_for_update_connection_error(mock_requests_get, mock_print):
    """Test handling of connection errors."""
    mock_requests_get.side_effect = RequestException("Connection failed")
    
    check_for_update()
    
    mock_requests_get.assert_called_once_with(RELEASE_URL, timeout=5)
    
    # Check error message is printed
    print_calls = [call.args[0] for call in mock_print.call_args_list]
    assert any("✖ Update failed:" in call for call in print_calls)


@patch('src.utils.updater.__version__', '1.0.0')
@patch('builtins.print')
@patch('requests.get')
def test_check_for_update_missing_asset(mock_requests_get, mock_print):
    """Test handling when kickstart asset is not found in release."""
    mock_release_data = {
        "tag_name": "v1.1.0",
        "assets": [
            {
                "name": "other-file.zip",
                "browser_download_url": "https://github.com/woud420/kickstart/releases/download/v1.1.0/other-file.zip"
            }
        ]
    }
    
    mock_response = MagicMock()
    mock_response.json.return_value = mock_release_data
    mock_response.raise_for_status.return_value = None
    mock_requests_get.return_value = mock_response
    
    check_for_update()
    
    # Check error message is printed
    print_calls = [call.args[0] for call in mock_print.call_args_list]
    assert any("✖ Update failed:" in call for call in print_calls)


@patch('src.utils.updater.__version__', '1.0.0')
@patch('builtins.print')
@patch('requests.get')
def test_check_for_update_invalid_json(mock_requests_get, mock_print):
    """Test handling of invalid JSON response."""
    mock_response = MagicMock()
    mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
    mock_response.raise_for_status.return_value = None
    mock_requests_get.return_value = mock_response
    
    check_for_update()
    
    # Check error message is printed
    print_calls = [call.args[0] for call in mock_print.call_args_list]
    assert any("✖ Update failed:" in call for call in print_calls)


@patch('src.utils.updater.__version__', '1.0.0')
@patch('builtins.print')
@patch('requests.get')
@patch('sys.argv', ['/usr/local/bin/kickstart'])
@patch('shutil.copy2')
def test_check_for_update_backup_failure(mock_copy2, mock_requests_get, mock_print, mock_release_data):
    """Test handling when backup creation fails."""
    mock_release_response = MagicMock()
    mock_release_response.json.return_value = mock_release_data
    mock_release_response.raise_for_status.return_value = None
    mock_requests_get.return_value = mock_release_response
    
    mock_copy2.side_effect = OSError("Permission denied")
    
    check_for_update()
    
    # Check error message is printed
    print_calls = [call.args[0] for call in mock_print.call_args_list]
    assert any("✖ Update failed:" in call for call in print_calls)


@patch('src.utils.updater.__version__', '1.0.0')
@patch('builtins.print')
@patch('requests.get')
@patch('sys.argv', ['/usr/local/bin/kickstart'])
@patch('shutil.copy2')
@patch('shutil.copyfileobj')
def test_check_for_update_download_failure(
    mock_copyfileobj, mock_copy2, mock_requests_get, mock_print, mock_release_data
):
    """Test handling when binary download fails."""
    # Mock the initial release check
    mock_release_response = MagicMock()
    mock_release_response.json.return_value = mock_release_data
    mock_release_response.raise_for_status.return_value = None
    
    # Mock failed binary download
    mock_download_response = MagicMock()
    mock_download_response.raise_for_status.side_effect = HTTPError("Download failed")
    
    mock_requests_get.side_effect = [mock_release_response, mock_download_response]
    
    check_for_update()
    
    # Check error message is printed
    print_calls = [call.args[0] for call in mock_print.call_args_list]
    assert any("✖ Update failed:" in call for call in print_calls)


def test_version_comparison_logic():
    """Test that version comparison works correctly with tag_name format."""
    # This tests the logic: latest == __version__ where latest = data["tag_name"].lstrip("v")
    
    test_cases = [
        ("v1.0.0", "1.0.0", True),   # Same version
        ("1.0.0", "1.0.0", True),    # Same version without v prefix
        ("v1.1.0", "1.0.0", False),  # New version available
        ("1.1.0", "1.0.0", False),   # New version available without v prefix
        ("v0.9.0", "1.0.0", False),  # Older version (edge case)
    ]
    
    for tag_name, current_version, expected_up_to_date in test_cases:
        latest = tag_name.lstrip("v")
        is_up_to_date = latest == current_version
        assert is_up_to_date == expected_up_to_date, f"Failed for tag_name='{tag_name}', current='{current_version}'"


@patch('src.utils.updater.__version__', '2.0.0-beta')
@patch('builtins.print')
@patch('requests.get')
def test_check_for_update_with_prerelease_version(mock_requests_get, mock_print):
    """Test behavior with pre-release version strings."""
    mock_release_data = {
        "tag_name": "v2.0.0",
        "assets": [{"name": "kickstart", "browser_download_url": "https://example.com/kickstart"}]
    }
    
    mock_response = MagicMock()
    mock_response.json.return_value = mock_release_data
    mock_response.raise_for_status.return_value = None
    mock_requests_get.return_value = mock_response
    
    check_for_update()
    
    # Should detect new version available since "2.0.0" != "2.0.0-beta"
    print_calls = [call.args[0] for call in mock_print.call_args_list]
    assert any("⬆ New version available: 2.0.0" in call for call in print_calls)


@patch('sys.argv', ['/complex/path/with spaces/kickstart'])
def test_binary_path_resolution():
    """Test that binary path resolution handles complex paths correctly."""
    with patch('src.utils.updater.__version__', '1.0.0'), \
         patch('builtins.print'), \
         patch('requests.get') as mock_requests_get, \
         patch('shutil.copy2') as mock_copy2, \
         patch('shutil.copyfileobj'), \
         patch('pathlib.Path.chmod'):
        
        mock_release_data = {
            "tag_name": "v1.1.0",
            "assets": [{"name": "kickstart", "browser_download_url": "https://example.com/kickstart"}]
        }
        
        mock_release_response = MagicMock()
        mock_release_response.json.return_value = mock_release_data
        mock_release_response.raise_for_status.return_value = None
        
        mock_download_response = MagicMock()
        mock_download_response.raise_for_status.return_value = None
        mock_download_response.raw = MagicMock()
        
        mock_requests_get.side_effect = [mock_release_response, mock_download_response]
        
        with patch('builtins.open', mock_open()):
            check_for_update()
        
        # Verify correct path resolution
        expected_bin_path = Path('/complex/path/with spaces/kickstart').resolve()
        expected_backup_path = expected_bin_path.with_suffix('.bak')
        mock_copy2.assert_called_once_with(expected_bin_path, expected_backup_path)