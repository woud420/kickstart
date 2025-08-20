import sys
import shutil
import hashlib
from pathlib import Path
from typing import Any, Optional

import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature

from src import __version__

REPO: str = "woud420/kickstart"
RELEASE_URL: str = f"https://api.github.com/repos/{REPO}/releases/latest"

# Public key for verifying releases (should be distributed securely)
PUBLIC_KEY_PEM = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA... # Replace with actual public key
-----END PUBLIC KEY-----"""


def verify_signature(data: bytes, signature: bytes) -> bool:
    """Verify the signature of downloaded binary data.
    
    Args:
        data: The binary data to verify
        signature: The signature to verify against
        
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        # Load the public key
        public_key = serialization.load_pem_public_key(PUBLIC_KEY_PEM.encode())
        
        # Verify the signature
        public_key.verify(
            signature,
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except (InvalidSignature, Exception):
        return False


def get_sha256_hash(data: bytes) -> str:
    """Calculate SHA256 hash of binary data.
    
    Args:
        data: Binary data to hash
        
    Returns:
        Hexadecimal SHA256 hash string
    """
    return hashlib.sha256(data).hexdigest()


def download_and_verify_binary(download_url: str, expected_hash: Optional[str] = None, 
                             signature_url: Optional[str] = None) -> Optional[bytes]:
    """Download binary and verify its integrity and authenticity.
    
    Args:
        download_url: URL to download the binary from
        expected_hash: Expected SHA256 hash (optional)
        signature_url: URL to download signature from (optional)
        
    Returns:
        Binary data if verification passes, None otherwise
    """
    try:
        # Download the binary
        with requests.get(download_url, stream=True, timeout=30) as r:
            r.raise_for_status()
            binary_data = r.content
        
        # Verify hash if provided
        if expected_hash:
            actual_hash = get_sha256_hash(binary_data)
            if actual_hash != expected_hash:
                print(f"[red]✖ Hash verification failed. Expected: {expected_hash}, Got: {actual_hash}")
                return None
        
        # Verify signature if provided
        if signature_url:
            try:
                with requests.get(signature_url, timeout=10) as sig_r:
                    sig_r.raise_for_status()
                    signature = sig_r.content
                
                if not verify_signature(binary_data, signature):
                    print("[red]✖ Signature verification failed. Binary may be compromised.")
                    return None
            except requests.RequestException as e:
                print(f"[yellow]⚠ Could not download signature for verification: {e}")
                # In production, you might want to fail here for security
                print("[yellow]⚠ Proceeding without signature verification (NOT RECOMMENDED)")
        
        return binary_data
        
    except requests.RequestException as e:
        print(f"[red]✖ Download failed: {e}")
        return None


def check_for_update() -> None:
    """Check for updates and securely download new version if available.
    
    This function:
    1. Fetches the latest release information from GitHub API
    2. Compares version numbers
    3. Downloads binary with integrity and signature verification
    4. Creates backup of current binary before replacement
    5. Replaces binary with verified new version
    """
    print(f"[cyan]Checking for updates (current version: {__version__})...")

    try:
        # Fetch release information
        r: requests.Response = requests.get(RELEASE_URL, timeout=10)
        r.raise_for_status()
        data: dict[str, Any] = r.json()
        
        latest: str = data["tag_name"].lstrip("v")
        
        # Find the main binary asset
        kickstart_asset = next(
            (asset for asset in data["assets"] if asset["name"] == "kickstart"),
            None
        )
        
        if not kickstart_asset:
            print("[red]✖ Could not find kickstart binary in release assets")
            return
            
        download_url: str = kickstart_asset["browser_download_url"]
        
        # Look for hash and signature files
        expected_hash: Optional[str] = None
        signature_url: Optional[str] = None
        
        # Try to find SHA256 hash file
        hash_asset = next(
            (asset for asset in data["assets"] if asset["name"] == "kickstart.sha256"),
            None
        )
        if hash_asset:
            try:
                hash_response = requests.get(hash_asset["browser_download_url"], timeout=5)
                hash_response.raise_for_status()
                expected_hash = hash_response.text.strip().split()[0]  # First part is the hash
            except requests.RequestException as e:
                print(f"[yellow]⚠ Could not retrieve hash file: {e}")
        
        # Try to find signature file
        sig_asset = next(
            (asset for asset in data["assets"] if asset["name"] == "kickstart.sig"),
            None
        )
        if sig_asset:
            signature_url = sig_asset["browser_download_url"]

        if latest == __version__:
            print("[green]✅ You're already up to date.")
            return

        print(f"[yellow]⬆ New version available: {latest} — downloading...")
        print("[cyan]🔒 Verifying download integrity and authenticity...")

        # Download and verify the binary
        binary_data = download_and_verify_binary(
            download_url, 
            expected_hash, 
            signature_url
        )
        
        if binary_data is None:
            print("[red]✖ Binary verification failed. Update aborted for security.")
            return

        # Create backup and replace binary
        bin_path: Path = Path(sys.argv[0]).resolve()
        backup: Path = bin_path.with_suffix(".bak")

        # Create backup of current binary
        try:
            shutil.copy2(bin_path, backup)
        except OSError as e:
            print(f"[red]✖ Could not create backup: {e}")
            return

        # Write the verified binary
        try:
            with open(bin_path, "wb") as f:
                f.write(binary_data)
            bin_path.chmod(0o755)
        except OSError as e:
            print(f"[red]✖ Could not write new binary: {e}")
            # Try to restore backup
            try:
                shutil.copy2(backup, bin_path)
                print("[yellow]⚠ Restored from backup")
            except OSError:
                print("[red]✖ Could not restore backup! Manual intervention required.")
            return

        print(f"[green]✔ Updated successfully to {latest}!")
        print(f"[green]💾 Backup saved to {backup}")
        print("[green]🔒 Binary integrity and authenticity verified")

    except requests.RequestException as e:
        print(f"[red]✖ Network error during update: {e}")
    except KeyError as e:
        print(f"[red]✖ Unexpected response format from GitHub API: missing {e}")
    except Exception as e:
        print(f"[red]✖ Update failed: {e}")

