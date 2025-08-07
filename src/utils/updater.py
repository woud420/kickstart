import sys
import shutil
import requests
from pathlib import Path
from src import __version__
from .logger import info, success, warn, error

REPO = "woud420/kickstart"
RELEASE_URL = f"https://api.github.com/repos/{REPO}/releases/latest"

def check_for_update():
    info(f"Checking for updates (current version: {__version__})...")

    try:
        r = requests.get(RELEASE_URL, timeout=5)
        r.raise_for_status()
        data = r.json()
        latest = data["tag_name"].lstrip("v")
        assets = data["assets"]
        kickstart_asset = next((asset for asset in assets if asset["name"] == "kickstart"), None)

        if kickstart_asset is None:
            warn("No 'kickstart' asset found; update aborted")
            return

        download_url = kickstart_asset["browser_download_url"]

        if latest == __version__:
            success("You're already up to date")
            return

        info(f"New version available: {latest}; downloading...")

        bin_path = Path(sys.argv[0]).resolve()
        backup = bin_path.with_suffix(".bak")

        shutil.copy2(bin_path, backup)

        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            with open(bin_path, "wb") as f:
                shutil.copyfileobj(r.raw, f)

        bin_path.chmod(0o755)
        success(f"Updated successfully to {latest}; backup saved to {backup}")

    except Exception as e:
        error(f"Update failed: {e}")
