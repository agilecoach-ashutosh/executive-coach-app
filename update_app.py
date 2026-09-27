"""Git-free, release-based updater for the source installation of Presence Coach."""
from __future__ import annotations

import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

REPOSITORY = "agilecoach-ashutosh/executive-coach-app"
API = f"https://api.github.com/repos/{REPOSITORY}"
ASSET_NAME = "Presence-Coach-source.zip"
MARKER = ".presence-update.json"
RELEASE_MANIFEST = "presence-manifest.json"
MAX_DOWNLOAD = 30 * 1024 * 1024
MAX_UNPACKED = 80 * 1024 * 1024
MAX_FILES = 1000
ROOT = Path(__file__).resolve().parent
USER_AGENT = "PresenceCoach-Updater/1"


class UpdateError(Exception):
    pass


def request_bytes(url: str, *, accept: str = "application/vnd.github+json") -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
    with urllib.request.urlopen(request, timeout=45) as response:
        data = response.read(MAX_DOWNLOAD + 1)
    if len(data) > MAX_DOWNLOAD:
        raise UpdateError("The downloaded update exceeds the allowed size.")
    return data


def latest_release() -> tuple[str, str, str]:
    try:
        release = json.loads(request_bytes(f"{API}/releases/latest"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise UpdateError("No stable Presence Coach release is available yet.") from exc
        raise
    if release.get("draft") or release.get("prerelease"):
        raise UpdateError("The latest release is not a stable release.")
    tag = release.get("tag_name")
    for asset in release.get("assets", []):
        if asset.get("name") != ASSET_NAME or asset.get("state") != "uploaded":
            continue
        url = asset.get("browser_download_url", "")
        digest = asset.get("digest", "")
        if not url.startswith(f"https://github.com/{REPOSITORY}/releases/download/"):
            raise UpdateError("The release download location is unexpected.")
        if not digest.startswith("sha256:") or len(digest) != 71:
            raise UpdateError("The release does not provide a valid SHA-256 digest.")
        if not isinstance(tag, str) or not tag:
            raise UpdateError("The release has no version tag.")
        return tag, url, digest[7:].lower()
    raise UpdateError("This release has no verified Presence Coach source package.")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def safe_relative_path(relative: str) -> bool:
    if not isinstance(relative, str) or not relative or "\\" in relative or ":" in relative:
        return False
    parts = PurePosixPath(relative).parts
    return (all(part not in ("", ".", "..") for part in parts)
            and not relative.startswith("/") and relative not in (".git", ".venv", MARKER)
            and not relative.startswith((".git/", ".venv/")))


def unpack_release(archive: bytes, destination: Path, expected_digest: str) -> dict[str, str]:
    if sha256(archive) != expected_digest:
        raise UpdateError("The release checksum did not match. Nothing was changed.")
    hashes: dict[str, str] = {}
    total = 0
    try:
        with zipfile.ZipFile(io.BytesIO(archive)) as package:
            for item in package.infolist():
                parts = PurePosixPath(item.filename).parts
                if not parts or parts[0] != "presence-coach" or item.is_dir():
                    continue
                relative_parts = parts[1:]
                if not relative_parts or any(part in ("", ".", "..") for part in relative_parts):
                    raise UpdateError("The release contains an unsafe file path.")
                if item.filename.startswith("/") or "\\" in item.filename or ":" in item.filename:
                    raise UpdateError("The release contains an unsafe file path.")
                if (item.external_attr >> 16) & 0o170000 == 0o120000:
                    raise UpdateError("The release contains a symbolic link.")
                relative = "/".join(relative_parts)
                if relative in hashes or not safe_relative_path(relative):
                    raise UpdateError("The release contains a duplicate or protected path.")
                total += item.file_size
                if len(hashes) >= MAX_FILES or total > MAX_UNPACKED:
                    raise UpdateError("The release contains too many or too large files.")
                target = destination.joinpath(*relative_parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                with package.open(item) as source, target.open("wb") as output:
                    shutil.copyfileobj(source, output)
                hashes[relative] = sha256(target.read_bytes())
    except (zipfile.BadZipFile, EOFError) as exc:
        raise UpdateError("The downloaded release is not a valid ZIP package.") from exc
    required = {"update_app.py", "requirements.txt", "constraints.txt", "session_export_mode.py"}
    if not required.issubset(hashes):
        raise UpdateError("The release is missing required application files.")
    return hashes


def local_git_head(root: Path) -> str | None:
    git_dir = root / ".git"
    if git_dir.is_file():
        pointer = git_dir.read_text(encoding="utf-8").strip()
        if not pointer.startswith("gitdir: "):
            return None
        git_dir = (root / pointer[8:]).resolve()
    if not git_dir.is_dir():
        return None
    head = (git_dir / "HEAD").read_text(encoding="utf-8").strip()
    if not head.startswith("ref: "):
        return head if len(head) == 40 else None
    ref = head[5:]
    if (git_dir / ref).is_file():
        return (git_dir / ref).read_text(encoding="utf-8").strip()
    packed = git_dir / "packed-refs"
    if packed.exists():
        for line in packed.read_text(encoding="utf-8").splitlines():
            if line.endswith(" " + ref):
                return line.split(" ", 1)[0]
    return None


def existing_baseline(root: Path) -> tuple[dict[str, str] | None, str | None]:
    marker = root / MARKER
    if marker.exists():
        data = json.loads(marker.read_text(encoding="utf-8"))
        files = data.get("files")
        if (not isinstance(files, dict) or any(
            not safe_relative_path(path) or not isinstance(digest, str)
            or re.fullmatch(r"[0-9a-f]{64}", digest) is None
            for path, digest in files.items()
        )):
            raise UpdateError("The local update record is damaged. Nothing was changed.")
        return files, data.get("version")
    head = local_git_head(root)
    if head:
        if re.fullmatch(r"[0-9a-fA-F]{40}", head) is None:
            raise UpdateError("Could not verify the current checkout commit.")
        tree = json.loads(request_bytes(f"{API}/git/trees/{head}?recursive=1"))
        if tree.get("truncated"):
            raise UpdateError("Could not verify the current checkout before updating.")
        return {
            entry["path"]: entry["sha"]
            for entry in tree.get("tree", [])
            if entry.get("type") == "blob"
            and not entry["path"].startswith((".github/", "tests/"))
        }, None
    return None, None


def register_install(root: Path = ROOT) -> bool:
    """Record file hashes after first-time setup of a published release ZIP."""
    manifest = root / RELEASE_MANIFEST
    if not manifest.exists():
        return False  # Existing source checkout; the updater verifies its GitHub tree.
    data = json.loads(manifest.read_text(encoding="utf-8"))
    files = data.get("files")
    if not isinstance(files, dict) or not isinstance(data.get("version"), str):
        raise UpdateError("The release package has an invalid install manifest.")
    for relative, expected in files.items():
        if (not safe_relative_path(relative) or not isinstance(expected, str)
                or re.fullmatch(r"[0-9a-f]{64}", expected) is None):
            raise UpdateError("The release package has an invalid install manifest.")
        target = root / relative
        if not target.is_file() or sha256(target.read_bytes()) != expected:
            raise UpdateError(f"Release file failed verification: {relative}")
    files[RELEASE_MANIFEST] = sha256(manifest.read_bytes())
    (root / MARKER).write_text(json.dumps({"version": data["version"], "files": files}, indent=2), encoding="utf-8")
    return True


def verify_local_files(root: Path, new_files: dict[str, str], baseline: dict[str, str] | None,
                       *, git_baseline: bool = False) -> None:
    if baseline is None:
        print("This installation has no update record, so local edits cannot be verified.")
        if input("Back up and replace app files anyway? [y/N]: ").strip().lower() != "y":
            raise UpdateError("Update cancelled. No files were changed.")
        return
    for relative in sorted(set(new_files) | set(baseline)):
        target = root / relative
        parts = PurePosixPath(relative).parts
        if target.is_symlink() or any(
            root.joinpath(*parts[:index]).is_symlink()
            for index in range(1, len(parts))
        ):
            raise UpdateError(f"A managed path is a symbolic link: {relative}")
        expected = baseline.get(relative)
        if expected is None:
            if target.exists():
                raise UpdateError(f"A personal file conflicts with this update: {relative}")
            continue
        if not target.is_file():
            raise UpdateError(f"A managed application file has changed: {relative}")
        current = target.read_bytes()
        actual = git_blob_sha(current) if git_baseline else sha256(current)
        if actual != expected:
            raise UpdateError(f"A managed application file has local edits: {relative}")


def install_dependencies(staged: Path, root: Path, work: Path) -> Path | None:
    if all((staged / name).read_bytes() == (root / name).read_bytes()
           for name in ("requirements.txt", "constraints.txt")):
        return None
    print("Preparing updated Python dependencies...")
    target = work / "venv-new"
    base_python = getattr(sys, "_base_executable", sys.executable)
    subprocess.run([base_python, "-m", "venv", str(target)], check=True)
    executable = target / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    subprocess.run([str(executable), "-m", "pip", "install", "-r",
                    str(staged / "requirements.txt"), "-c", str(staged / "constraints.txt")], check=True)
    subprocess.run([str(executable), "-m", "pip", "check"], check=True)
    return target


def apply_update(root: Path, staged: Path, new_files: dict[str, str], old_files: dict[str, str] | None,
                 version: str, new_venv: Path | None, work: Path) -> None:
    backup = work / "backup"
    backup.mkdir()
    obsolete = set(old_files or {}) - set(new_files)
    paths = sorted(set(new_files) | obsolete)
    saved: list[str] = []
    installed: list[str] = []
    venv_backup = work / "venv-old"
    venv_swapped = False
    try:
        for relative in paths:
            target = root / relative
            if target.exists():
                saved_path = backup / relative
                saved_path.parent.mkdir(parents=True, exist_ok=True)
                os.replace(target, saved_path)
                saved.append(relative)
            if relative in new_files:
                target.parent.mkdir(parents=True, exist_ok=True)
                os.replace(staged / relative, target)
                installed.append(relative)
                if target.suffix == ".command" and os.name != "nt":
                    target.chmod(target.stat().st_mode | 0o111)
        if new_venv:
            os.replace(root / ".venv", venv_backup)
            try:
                os.replace(new_venv, root / ".venv")
            except Exception:
                os.replace(venv_backup, root / ".venv")
                raise
            venv_swapped = True
            executable = root / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            # Ensure the interpreter still works at its final path before retiring
            # the previous environment. Use -m pip: venv console scripts can embed
            # their staging path and are not used by the app or updater.
            subprocess.run([str(executable), "-m", "pip", "check"], check=True)
        marker = root / MARKER
        temp_marker = work / "marker.json"
        temp_marker.write_text(json.dumps({"version": version, "files": new_files}, indent=2), encoding="utf-8")
        if marker.exists():
            os.replace(marker, work / "marker-old.json")
        os.replace(temp_marker, marker)
    except Exception:
        if venv_swapped:
            os.replace(root / ".venv", new_venv)
            os.replace(venv_backup, root / ".venv")
        for relative in reversed(installed):
            (root / relative).unlink(missing_ok=True)
        for relative in reversed(saved):
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(backup / relative, target)
        old_marker = work / "marker-old.json"
        if old_marker.exists():
            os.replace(old_marker, root / MARKER)
        raise


def main(root: Path = ROOT) -> int:
    if sys.version_info[:2] != (3, 12):
        raise UpdateError("Use Python 3.12 to update Presence Coach.")
    if not (root / ".venv").is_dir():
        raise UpdateError("Run setup once before updating Presence Coach.")
    print("Checking the latest stable Presence Coach release...")
    version, url, digest = latest_release()
    baseline, current_version = existing_baseline(root)
    if current_version == version:
        print(f"Presence Coach is already up to date ({version}).")
        return 0
    archive = request_bytes(url, accept="application/octet-stream")
    with tempfile.TemporaryDirectory(prefix="presence-update-", dir=root.parent) as folder:
        work = Path(folder)
        staged = work / "source"
        staged.mkdir()
        new_files = unpack_release(archive, staged, digest)
        git_baseline = current_version is None and baseline is not None
        verify_local_files(root, new_files, baseline, git_baseline=git_baseline)
        new_venv = install_dependencies(staged, root, work)
        apply_update(root, staged, new_files, baseline, version, new_venv, work)
    if os.name == "nt":
        try:
            subprocess.run([str(root / ".venv" / "Scripts" / "python.exe"),
                            str(root / "windows_setup.py")], cwd=root, check=True)
        except Exception as exc:
            print(f"Update succeeded, but shortcut refresh failed: {exc}")
            print("Start.cmd can still launch Presence Coach.")
    print(f"Presence Coach updated to {version}. Open it using your usual shortcut.")
    return 0


if __name__ == "__main__":
    try:
        if sys.argv[1:] == ["--register-install"]:
            register_install()
            raise SystemExit(0)
        raise SystemExit(main())
    except (UpdateError, OSError, ValueError, subprocess.CalledProcessError,
            urllib.error.URLError) as exc:
        print(f"Update did not complete: {exc}", file=sys.stderr)
        raise SystemExit(1)
