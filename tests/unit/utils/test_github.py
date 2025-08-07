import os
from unittest.mock import patch, MagicMock

from src.utils.github import create_repo
from src.generators.mixins import GitHubMixin


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


def test_mixin_warns_on_repo_creation_failure():
    class Dummy(GitHubMixin):
        def __init__(self):
            self.gh = True
            self.name = "dummy"

    dummy = Dummy()
    with patch("src.generators.mixins.create_repo", return_value=False) as mock_create, \
         patch("src.generators.mixins.warn") as mock_warn:
        dummy.create_github_repo_if_requested()
        mock_create.assert_called_once_with("dummy")
        mock_warn.assert_called_once_with("Failed to create GitHub repository 'dummy'")
