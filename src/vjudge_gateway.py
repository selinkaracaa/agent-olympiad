"""Local VJudge submission gateway.

Holds the browser session cookie in-process. Agents only talk to localhost.

Examples:
  python src/vjudge_gateway.py serve --port 8787
  python src/vjudge_gateway.py submit --problem 4A --lang python3 --source-file sol.py
  python src/vjudge_gateway.py submit --contest 845103 --problem A --lang cpp17 --source-file sol.cpp
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from env_config import load_repo_dotenv
from judge.remote import RemoteSubmitRequest
from judge.vjudge import VJudgeClient

load_repo_dotenv(REPO_ROOT / ".env")

_RUNS: dict[str, dict[str, Any]] = {}
_LOCK = threading.Lock()


def _json_response(handler: BaseHTTPRequestHandler, code: int, payload: dict[str, Any]) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _read_json(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length") or "0")
    raw = handler.rfile.read(length) if length else b"{}"
    if not raw:
        return {}
    data = json.loads(raw.decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("JSON body must be an object")
    return data


class GatewayHandler(BaseHTTPRequestHandler):
    server_version = "VJudgeGateway/0.1"

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path in {"/health", "/v1/health"}:
            _json_response(
                self,
                200,
                {
                    "ok": True,
                    "service": "vjudge-gateway",
                    "adapter_protocol": "problem-or-contest-v2",
                },
            )
            return
        if path.startswith("/v1/runs/"):
            run_id = path[len("/v1/runs/") :].strip("/")
            with _LOCK:
                row = _RUNS.get(run_id)
            if not row:
                _json_response(self, 404, {"error": "run not found", "run_id": run_id})
                return
            if row.get("status") in {"submitted", "polling", "queued"} and row.get("vjudge_run_id"):
                client = VJudgeClient()
                remote = client.get_result(str(row["vjudge_run_id"]))
                row = {**row, **remote.to_dict(), "gateway_run_id": run_id}
                with _LOCK:
                    _RUNS[run_id] = row
            _json_response(self, 200, row)
            return
        _json_response(self, 404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path != "/v1/submit":
            _json_response(self, 404, {"error": "not found"})
            return
        try:
            data = _read_json(self)
            request = RemoteSubmitRequest(
                contest_id=str(data.get("contest_id") or ""),
                oj=str(data.get("oj") or "CodeForces"),
                problem=str(data.get("problem") or ""),
                language=str(data.get("language") or ""),
                source=str(data.get("source") or ""),
                idempotency_key=str(data.get("idempotency_key") or ""),
                open_source=bool(data.get("open_source", False)),
            )
            if not request.problem or not request.source:
                raise ValueError("problem and source are required")
            if not request.contest_id and not request.oj:
                raise ValueError("oj is required for problem-mode submit")
            if request.idempotency_key:
                with _LOCK:
                    for existing in _RUNS.values():
                        if existing.get("idempotency_key") == request.idempotency_key:
                            _json_response(self, 200, existing)
                            return
            poll = bool(data.get("poll", True))
            client = VJudgeClient()
            gateway_run_id = uuid.uuid4().hex
            if poll:
                remote = client.submit_and_poll(request)
            else:
                remote = client.submit(request)
            row = {
                "gateway_run_id": gateway_run_id,
                "idempotency_key": request.idempotency_key,
                "contest_id": request.contest_id,
                "oj": request.oj,
                "problem": request.problem,
                "language": request.language,
                "vjudge_run_id": remote.run_id,
                **remote.to_dict(),
            }
            with _LOCK:
                _RUNS[gateway_run_id] = row
            _json_response(self, 200, row)
        except Exception as exc:  # noqa: BLE001 - gateway boundary
            _json_response(self, 400, {"error": str(exc), "status": "failed"})


def cmd_serve(args: argparse.Namespace) -> int:
    host = args.host
    port = int(args.port)
    # Fail fast if cookie missing.
    VJudgeClient()
    server = ThreadingHTTPServer((host, port), GatewayHandler)
    print(f"VJudge gateway listening on http://{host}:{port}", flush=True)
    print("POST /v1/submit  GET /v1/runs/{id}  GET /health", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nshutdown", flush=True)
    return 0


def cmd_submit(args: argparse.Namespace) -> int:
    source = args.source
    if args.source_file:
        source = Path(args.source_file).read_text(encoding="utf-8")
    if not source:
        raise SystemExit("provide --source or --source-file")
    client = VJudgeClient()
    request = RemoteSubmitRequest(
        contest_id=str(args.contest or ""),
        oj=str(args.oj or "CodeForces"),
        problem=str(args.problem),
        language=str(args.lang),
        source=source,
        idempotency_key=str(args.idempotency_key or ""),
    )
    if args.no_poll:
        result = client.submit(request)
    else:
        result = client.submit_and_poll(
            request,
            interval_sec=float(args.interval),
            timeout_sec=float(args.timeout),
        )
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    if result.status == "final" and result.verdict == "AC":
        return 0
    if result.status == "needs_human":
        return 2
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    serve = sub.add_parser("serve", help="Run local HTTP gateway")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8787)
    serve.set_defaults(func=cmd_serve)

    submit = sub.add_parser("submit", help="Submit once via direct VJudge client")
    submit.add_argument(
        "--contest",
        default="",
        help="Contest id for contest mode; omit for problem mode",
    )
    submit.add_argument("--oj", default="CodeForces", help="OJ for problem mode")
    submit.add_argument(
        "--problem",
        required=True,
        help="Contest letter A/B/C, or CF id like 4A / 231A in problem mode",
    )
    submit.add_argument("--lang", default="cpp17")
    submit.add_argument("--source")
    submit.add_argument("--source-file")
    submit.add_argument("--idempotency-key", default="")
    submit.add_argument("--interval", type=float, default=2.0)
    submit.add_argument("--timeout", type=float, default=120.0)
    submit.add_argument("--no-poll", action="store_true")
    submit.set_defaults(func=cmd_submit)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
