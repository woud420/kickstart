"""Utilities for interacting with the GitHub API."""

from __future__ import annotations

import os
from typing import Optional

import requests

from .logger import info, warn, success
from .error_handling import handle_http_operations


@handle_http_operations("GitHub repository creation", default_return=False, log_errors=True)
def create_repo(name: str, private: bool = False, description: str | None = None) -> bool:
    """Create a repository under the authenticated user.

    Parameters
    ----------
    name:
        Name of the repository to create.
    private:
        Whether the repository should be private.
    description:
        Optional repository description.

    Returns
    -------
    bool
        ``True`` on success, ``False`` otherwise.
    """

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        warn("GITHUB_TOKEN not set; skipping remote repository creation")
        return False

    info(f"Creating GitHub repository '{name}' ...")

    url = "https://api.github.com/user/repos"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }
    payload = {
        "name": name,
        "private": private,
    }
    if description:
        payload["description"] = description

    r = requests.post(url, json=payload, headers=headers, timeout=10)
    if r.status_code == 201:
        success("GitHub repository created")
        return True

    # For non-201 status codes, the decorator will handle the error
    # This will trigger an exception that the decorator catches
    r.raise_for_status()
    return False

