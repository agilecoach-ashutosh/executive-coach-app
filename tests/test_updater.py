import hashlib
import io
import json
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path
from unittest.mock import patch

import update_app as updater


def package(files):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr("presence-coach/" + name, content)
    return buffer.getvalue()


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "app"
        self.root.mkdir()
        (self.root / ".venv").mkdir()
        self.files = {
            "update_app.py": b"updater release",
            "requirements.txt": b"example==1\n",
            "constraints.txt": b"example==1\n",
            "session_export_mode.py": b"new version\n",
            "Update.cmd": b"@echo off\n",
            "Update-Mac.command": b"#!/bin/bash\n",
        }

    def stage(self, files=None):
        archive = package(files or self.files)
        destination = Path(self.temp.name) / "stage"
        destination.mkdir(exist_ok=True)
        return destination, updater.unpack_release(archive, destination, hashlib.sha256(archive).hexdigest())

    def test_checksum_failure_does_not_extract_files(self):
        with self.assertRaisesRegex(updater.UpdateError, "checksum"):
            updater.unpack_release(package(self.files), self.root, "0" * 64)
        self.assertFalse((self.root / "update_app.py").exists())

    def test_unsafe_paths_and_duplicate_members_are_rejected(self):
        for extra in ("../outside.txt", "folder/../../outside.txt", "Update.cmd"):
            with self.subTest(extra=extra):
                archive = package({**self.files, extra: b"bad"}) if extra != "Update.cmd" else None
                if archive is None:
                    buf = io.BytesIO()
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore", UserWarning)
                        with zipfile.ZipFile(buf, "w") as z:
                            for name, content in self.files.items():
                                z.writestr("presence-coach/" + name, content)
                            z.writestr("presence-coach/Update.cmd", b"duplicate")
                    archive = buf.getvalue()
                with self.assertRaises(updater.UpdateError):
                    updater.unpack_release(archive, Path(self.temp.name) / "stage", updater.sha256(archive))

    def test_git_baseline_detects_local_edits_without_git_executable(self):
        (self.root / "session_export_mode.py").write_bytes(b"personal edit")
        baseline = {"session_export_mode.py": updater.git_blob_sha(b"original")}
        with self.assertRaisesRegex(updater.UpdateError, "local edits"):
            updater.verify_local_files(self.root, {"session_export_mode.py": "new"},
                                       baseline, git_baseline=True)

    def test_release_upgrade_preserves_user_files_and_installed_environment(self):
        stage, hashes = self.stage()
        (self.root / "requirements.txt").write_bytes(self.files["requirements.txt"])
        (self.root / "constraints.txt").write_bytes(self.files["constraints.txt"])
        (self.root / "session_export_mode.py").write_bytes(b"old version\n")
        (self.root / "my-export.docx").write_bytes(b"private export")
        old = {"session_export_mode.py": updater.sha256(b"old version\n")}
        with tempfile.TemporaryDirectory(dir=self.root.parent) as work:
            updater.apply_update(self.root, stage, hashes, old, "v0.0.9", None, Path(work))
        self.assertEqual((self.root / "session_export_mode.py").read_bytes(), b"new version\n")
        self.assertEqual((self.root / "my-export.docx").read_bytes(), b"private export")
        self.assertTrue((self.root / ".venv").exists())
        self.assertEqual(json.loads((self.root / updater.MARKER).read_text())["version"], "v0.0.9")

    def test_failed_replacement_restores_previous_files(self):
        stage, hashes = self.stage()
        (self.root / "session_export_mode.py").write_bytes(b"old version\n")
        old = {"session_export_mode.py": updater.sha256(b"old version\n")}
        original = updater.os.replace
        failed = False

        def fail_once(source, target):
            nonlocal failed
            if (not failed and str(source).endswith("session_export_mode.py")
                    and str(target).startswith(str(self.root))):
                failed = True
                raise OSError("simulated replacement failure")
            return original(source, target)

        with tempfile.TemporaryDirectory(dir=self.root.parent) as work, patch.object(
            updater.os, "replace", side_effect=fail_once
        ):
            with self.assertRaisesRegex(OSError, "simulated"):
                updater.apply_update(self.root, stage, hashes, old, "v0.0.9", None, Path(work))
        self.assertEqual((self.root / "session_export_mode.py").read_bytes(), b"old version\n")
        self.assertFalse((self.root / "update_app.py").exists())

    def test_main_updates_from_mock_release_without_git(self):
        (self.root / "requirements.txt").write_bytes(self.files["requirements.txt"])
        (self.root / "constraints.txt").write_bytes(self.files["constraints.txt"])
        (self.root / "session_export_mode.py").write_bytes(b"old version\n")
        old = {
            "session_export_mode.py": updater.sha256(b"old version\n"),
            "requirements.txt": updater.sha256(self.files["requirements.txt"]),
            "constraints.txt": updater.sha256(self.files["constraints.txt"]),
        }
        (self.root / updater.MARKER).write_text(json.dumps({"version": "v0.0.8", "files": old}))
        archive = package(self.files)
        with patch.object(updater, "latest_release", return_value=("v0.0.9", "release-url", updater.sha256(archive))), patch.object(
            updater, "request_bytes", return_value=archive
        ):
            self.assertEqual(updater.main(self.root), 0)
        self.assertEqual((self.root / "session_export_mode.py").read_bytes(), b"new version\n")

    def test_fresh_release_setup_registers_file_hashes(self):
        for relative, content in self.files.items():
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        manifest = {
            "version": "v0.0.9",
            "files": {name: updater.sha256(content) for name, content in self.files.items()},
        }
        (self.root / updater.RELEASE_MANIFEST).write_text(json.dumps(manifest))
        self.assertTrue(updater.register_install(self.root))
        baseline, version = updater.existing_baseline(self.root)
        self.assertEqual(version, "v0.0.9")
        self.assertIn(updater.RELEASE_MANIFEST, baseline)
        (self.root / "Update.cmd").write_bytes(b"personal edit")
        with self.assertRaisesRegex(updater.UpdateError, "local edits"):
            updater.verify_local_files(self.root, baseline, baseline)

    def test_replacement_environment_rolls_back_if_marker_cannot_be_saved(self):
        stage, hashes = self.stage()
        (self.root / "session_export_mode.py").write_bytes(b"old version\n")
        (self.root / ".venv" / "old.txt").write_bytes(b"old environment")
        with tempfile.TemporaryDirectory(dir=self.root.parent) as folder:
            work = Path(folder)
            new_venv = work / "venv-new"
            new_venv.mkdir()
            (new_venv / "new.txt").write_bytes(b"new environment")
            original = updater.os.replace

            def fail_marker(source, target):
                if Path(source).name == "marker.json":
                    raise OSError("simulated marker failure")
                return original(source, target)

            with patch.object(updater.os, "replace", side_effect=fail_marker), patch.object(
                updater.subprocess, "run"
            ):
                with self.assertRaisesRegex(OSError, "marker failure"):
                    updater.apply_update(self.root, stage, hashes, None, "v0.0.9", new_venv, work)
        self.assertEqual((self.root / ".venv" / "old.txt").read_bytes(), b"old environment")
        self.assertEqual((self.root / "session_export_mode.py").read_bytes(), b"old version\n")
