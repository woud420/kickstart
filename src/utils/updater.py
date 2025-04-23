import sys
import shutil
import requests
from pathlib import Path
from src import __version__

REPO = "woud420/kickstart"
RELEASE_URL = f"https://api.github.com/repos/{REPO}/releases/latest"

def check_for_update():
    print(f"[cyan]Checking for updates (current version: {__version__})...")

    try:
        r = requests.get(RELEASE_URL, timeout=5)
        r.raise_for_status()
        data = r.json()
        latest = data["tag_name"].lstrip("v")
        download_url = next(asset["browser_download_url"]
                            for asset in data["assets"]
                            if asset["name"] == "kickstart")

        if latest == __version__:
            print("[green]✅ You're already up to date.")
            return

        print(f"[yellow]⬆ New version available: {latest} — downloading...")

        bin_path = Path(sys.argv[0]).resolve()
        backup = bin_path.with_suffix(".bak")

        shutil.copy2(bin_path, backup)

        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            with open(bin_path, "wb") as f:
                shutil.copyfileobj(r.raw, f)

        bin_path.chmod(0o755)
        print(f"[green]✔ Updated successfully to {latest}! Backup saved to {backup}")

    except Exception as e:
        print(f"[red]✖ Update failed: {e}")

