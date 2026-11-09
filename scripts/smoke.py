"""Synthetic, rules-only HTTP smoke test. Never submits confidential data."""
import argparse
import base64
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from test_engine import fixture

def request(url, body=None):
    req = urllib.request.Request(url, data=None if body is None else json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.status, response.read()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", help="Existing local/container server; omit to start production server")
    args = parser.parse_args()
    worker = None
    private_marker = "SYNTHETIC_PRIVATE_LOG_REGRESSION_MARKER"
    if args.url:
        url = args.url.rstrip("/")
    else:
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        env = dict(os.environ, PORT=str(port), NODE_ENV="production")
        worker = subprocess.Popen(["node", "dist/index.cjs"], cwd=ROOT, env=env,
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        url = f"http://127.0.0.1:{port}"
    try:
        deadline = time.monotonic() + 30
        while True:
            try:
                code, body = request(url + "/api/status")
                status = json.loads(body)
                assert code == 200 and status["version"] == "1.0.0"
                break
            except (OSError, urllib.error.URLError):
                if time.monotonic() >= deadline:
                    raise RuntimeError("Server failed readiness within 30 seconds")
                time.sleep(0.1)
        code, html = request(url + "/")
        assert code == 200 and b'<div id="root">' in html, "Production frontend missing"
        payload = {"files": [{"name": "synthetic-smoke.txt",
                              "data": base64.b64encode(fixture().encode()).decode()}],
                   "use_ai": False, "provider": "groq", "model": "openai/gpt-oss-120b",
                   "composites": True}
        code, body = request(url + "/api/analyze", payload)
        result = json.loads(body)
        assert code == 200 and result["run_mode"] == "rules_only"
        assert result["summary"]["episodes"] == 1 and result["summary"]["promos"] > 0
        assert result["summary"]["mechanical_passes"] == result["summary"]["promos"]
        assert result["raw_model_logs"] == [] and result["summary"]["semantic_gate_passes"] == 0
        bad_request = urllib.request.Request(url + "/api/analyze",
                         data=('{"private":"' + private_marker + '",invalid}').encode(),
                         headers={"Content-Type": "application/json"})
        try:
            urllib.request.urlopen(bad_request, timeout=10)
            raise AssertionError("Malformed JSON unexpectedly accepted")
        except urllib.error.HTTPError as exc:
            assert exc.code == 400
            body = json.loads(exc.read())
            assert body["message"] == "Invalid request body."
        print("PASS: readiness, production frontend, Python worker, synthetic rules analysis, sanitized request error.")
    finally:
        if worker:
            worker.terminate()
            try:
                worker.wait(timeout=5)
            except subprocess.TimeoutExpired:
                worker.kill()
                worker.wait()
            logs = worker.stdout.read()
            worker.stdout.close()
            assert private_marker not in logs, "Malformed request contents leaked to server logs"
            print("PASS: malformed-request marker absent from captured production server logs.")

if __name__ == "__main__":
    main()
