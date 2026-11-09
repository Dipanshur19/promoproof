"""Export audited tracked source only, without Git history or run artifacts."""
import argparse
import json
import re
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROOT_FILES = {
    "README.md", "DEPLOYMENT.md", "HANDOFF_VERIFICATION.md", "FLOWS.md", "Dockerfile", ".dockerignore",
    ".gitignore", ".env.example", "package.json", "package-lock.json",
    "requirements.txt", "requirements-lock.txt", "requirements-deploy.txt",
    "engine.py", "tsconfig.json", "vite.config.ts", "tailwind.config.ts",
    "postcss.config.js", "components.json", "drizzle.config.ts",
}
DIRECTORIES = {"client", "server", "shared", "script", "scripts", "tests", ".github", "docs"}
FORBIDDEN_PARTS = {".git", ".venv", "node_modules", "__pycache__", "raw_outputs", "release"}
TOKEN = re.compile(rb"(?:gsk_[A-Za-z0-9]{20,}|hf_[A-Za-z0-9]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{32,}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----)")

def release_files():
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
    files = []
    for name in filter(None, tracked):
        path = Path(name)
        if name not in ROOT_FILES and path.parts[0] not in DIRECTORIES:
            raise ValueError(f"Unapproved tracked path: {name}")
        if any(p in FORBIDDEN_PARTS or p.lower().startswith("private") for p in path.parts):
            raise ValueError(f"Forbidden path: {name}")
        if path.name.startswith(".env") and name != ".env.example":
            raise ValueError(f"Environment file: {name}")
        if path.suffix.lower() in {".zip", ".sqlite", ".db"}:
            raise ValueError(f"Data/archive file: {name}")
        if path.suffix.lower() in {".pdf", ".csv"} and "docs" not in path.parts:
            raise ValueError(f"Data/archive file: {name}")
        if path.suffix.lower() == ".txt" and name not in ROOT_FILES:
            raise ValueError(f"Unexpected text fixture: {name}")
        source = ROOT / path
        if source.is_symlink():
            raise ValueError(f"Symlink not allowed: {name}")
        body = source.read_bytes()
        if TOKEN.search(body):
            raise ValueError(f"Possible embedded credential: {name}")
        if path.suffix == ".json":
            value = json.loads(body)
            if isinstance(value, dict) and ({"raw_model_logs", "promos"} & value.keys()) and "docs" not in path.parts:
                raise ValueError(f"Possible reviewer run: {name}")
        files.append((name, body))
    if not files:
        raise ValueError("No tracked files; initialize Git and add reviewed source first.")
    return files

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(ROOT.parent / "promoproof-deployment-handoff.zip"))
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    files = release_files()
    if not args.check_only:
        with zipfile.ZipFile(args.output, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, body in files:
                archive.writestr("promoproof/" + name, body)
    print(f"Source safety checks passed: {len(files)} tracked files.")
    if not args.check_only:
        print(f"Created {args.output}")

if __name__ == "__main__":
    main()
