import os
from unittest.mock import patch, MagicMock

from src.utils.github import create_repo


def test_create_repo_no_token():
    with patch.dict(os.environ, {}, clear=True):
        assert create_repo("myrepo") is False


def test_create_repo_success():
    with patch.dict(os.environ, {"GITHUB_TOKEN": "abc"}, clear=True), \
         patch("requests.post") as mock_post:
        mock_resp = MagicMock(status_code=201)
        mock_post.return_value = mock_resp
        assert create_repo("myrepo") is True
        mock_post.assert_called_once()


def test_create_repo_failure():
    with patch.dict(os.environ, {"GITHUB_TOKEN": "abc"}, clear=True), \
         patch("requests.post") as mock_post:
        mock_resp = MagicMock(status_code=400, text="bad request")
        mock_post.return_value = mock_resp
        assert create_repo("bad") is False
        mock_post.assert_called_once()
