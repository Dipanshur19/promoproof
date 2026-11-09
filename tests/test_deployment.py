"""Offline checks for source-only handoff and private-target upload policy."""
import contextlib
import io
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import release_bundle
import push_space

class ReleaseTests(unittest.TestCase):
    def check_source(self, name, body=b""):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(body)
            with patch.object(release_bundle, "ROOT", root), patch.object(
                release_bundle.subprocess, "check_output", return_value=name.encode() + b"\0"
            ):
                return release_bundle.release_files()

    def test_safe_source(self):
        self.assertEqual(self.check_source("README.md", b"Original software source")[0][0], "README.md")

    def test_raw_run_is_not_root_allowlisted(self):
        with self.assertRaises(ValueError):
            self.check_source("raw-run.json", b"{}")

    def test_env_blocked(self):
        with self.assertRaises(ValueError):
            self.check_source(".env", b"GROQ_API_KEY=")

    def test_archive_blocked_inside_client(self):
        with self.assertRaises(ValueError):
            self.check_source("client/fixture.zip")

    def test_possible_credential_blocked(self):
        with self.assertRaises(ValueError):
            self.check_source("README.md", b"gsk_" + b"A" * 32)

    def test_reviewer_json_blocked(self):
        with self.assertRaises(ValueError):
            self.check_source("client/run.json", json.dumps({"promos": []}).encode())

    def test_symlink_blocked(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "actual").write_text("source")
            (root / "README.md").symlink_to(root / "actual")
            with patch.object(release_bundle, "ROOT", root), patch.object(
                release_bundle.subprocess, "check_output", return_value=b"README.md\0"
            ):
                with self.assertRaises(ValueError):
                    release_bundle.release_files()

class UploadTests(unittest.TestCase):
    def run_upload(self, private=True, sdk="docker"):
        api = Mock()
        api.repo_info.return_value = types.SimpleNamespace(private=private, sdk=sdk)
        module = types.SimpleNamespace(HfApi=lambda: api, CommitOperationAdd=lambda **kw: kw)
        self.api = api
        with patch.dict(sys.modules, {"huggingface_hub": module}), \
             patch.object(sys, "argv", ["push_space.py", "owner/promoproof"]), \
             patch.object(push_space, "release_files", return_value=[
                 ("README.md", b"source"), (".github/workflows/ci.yml", b"workflow")
             ]), contextlib.redirect_stdout(io.StringIO()):
            push_space.main()

    def test_refuses_public_space(self):
        with self.assertRaises(SystemExit):
            self.run_upload(private=False)
        self.api.create_commit.assert_not_called()

    def test_refuses_wrong_sdk(self):
        with self.assertRaises(SystemExit):
            self.run_upload(sdk="gradio")
        self.api.create_commit.assert_not_called()

    def test_private_upload_excludes_github_workflows(self):
        self.run_upload()
        operations = self.api.create_commit.call_args.kwargs["operations"]
        self.assertEqual([o["path_in_repo"] for o in operations], ["README.md"])

if __name__ == "__main__":
    unittest.main()
