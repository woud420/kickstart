from unittest.mock import patch, MagicMock

from src.utils.updater import check_for_update


def test_missing_kickstart_asset_logs_warning_and_aborts():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "tag_name": "v1.2.3",
        "assets": [],
    }

    with patch("requests.get", return_value=mock_response) as mock_get, \
         patch("src.utils.updater.warn") as mock_warn:
        assert check_for_update() is None
        mock_warn.assert_called_once_with("No 'kickstart' asset found; update aborted")
        mock_get.assert_called_once()
