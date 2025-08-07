"""Utilities for interacting with the GitHub API."""

from __future__ import annotations

import os
from typing import Optional

import requests

from .logger import info, warn, success, error


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

    try:
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        if r.status_code == 201:
            success("GitHub repository created")
            return True
        error(f"GitHub API error {r.status_code}: {r.text}")
    except Exception as exc:
        error(f"Failed to create GitHub repository: {exc}")

    return False
