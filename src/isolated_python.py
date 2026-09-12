"""Run agent Python with no host data, network, or inherited credentials."""
from __future__ import annotations

import json
import math
import shutil
import subprocess
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

PYTHON_IMAGE = 'python:3.11-slim@sha256:9534e5a8e315485d4061ed659af0fd78a284c015f9b73661b41d6bab25604534'


class IsolationUnavailable(RuntimeError):
    """The isolated backend failed; agent code was not run on the host."""


@dataclass(frozen=True)
class PythonExecution:
    stdout: str
    stderr: str
    returncode: int
    timed_out: bool = False
    output_limited: bool = False
    elapsed_ms: int = 0


# Only this trusted supervisor and the submitted source enter the container.
# Output goes to bounded temporary files, not an unbounded Docker stdout pipe.
_SUPERVISOR = r'''
import json, resource, subprocess, sys, tempfile
limit, seconds = int(sys.argv[1]), float(sys.argv[2])
def limits():
    resource.setrlimit(resource.RLIMIT_FSIZE, (limit, limit))
with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
    timed_out = False
    try:
        proc = subprocess.run([sys.executable, '-I', '/submission/main.py'],
            stdin=sys.stdin.buffer, stdout=out, stderr=err,
            timeout=seconds, preexec_fn=limits)
        code = proc.returncode
    except subprocess.TimeoutExpired:
        timed_out, code = True, 124
    sizes = (out.tell(), err.tell())
    out.seek(0); err.seek(0)
    print(json.dumps(dict(stdout=out.read(limit).decode('utf-8','replace'),
        stderr=err.read(limit).decode('utf-8','replace'), returncode=code,
        timed_out=timed_out, output_limited=max(sizes) >= limit)))
'''


def run_python_isolated(source: str, *, stdin: str = '', timeout_sec: float = 5,
                        memory_mb: int = 256, output_bytes: int = 1024 * 1024) -> PythonExecution:
    docker = shutil.which('docker')
    if docker is None:
        raise IsolationUnavailable('Docker is required; host execution is disabled.')
    if timeout_sec <= 0 or memory_mb < 16 or output_bytes < 1:
        raise ValueError('Invalid isolated execution limits')
    container = 'ao-python-' + uuid.uuid4().hex
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='ao_isolated_') as temp:
        script = Path(temp) / 'main.py'
        script.write_text(source, encoding='utf-8')
        script.chmod(0o444)
        command = [docker, 'run', '--rm', '--pull=never', '--name', container, '-i',
            '--network', 'none', '--read-only', '--cap-drop', 'ALL',
            '--security-opt', 'no-new-privileges', '--pids-limit', '32',
            '--memory', f'{memory_mb}m', '--memory-swap', f'{memory_mb}m',
            '--cpus', '1', '--user', '65534:65534',
            '--tmpfs', '/tmp:rw,noexec,nosuid,size=64m', '--workdir', '/tmp',
            '--mount', f'type=bind,source={script.resolve()},target=/submission/main.py,readonly',
            PYTHON_IMAGE, 'python', '-I', '-c', _SUPERVISOR,
            str(output_bytes), str(timeout_sec)]
        try:
            process = subprocess.run(command, input=stdin, capture_output=True,
                text=True, encoding='utf-8', errors='replace', timeout=math.ceil(timeout_sec) + 20)
            if process.returncode:
                raise IsolationUnavailable(f'Isolated Python failed ({process.returncode}): {process.stderr[:1000]}')
            payload = json.loads(process.stdout)
            return PythonExecution(**payload, elapsed_ms=int((time.monotonic()-started)*1000))
        except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
            raise IsolationUnavailable(f'Isolated Python unavailable: {exc}') from exc
        finally:
            # Kill only this invocation's container if Docker timed out. No
            # user containers or services are touched.
            try:
                subprocess.run([docker, 'rm', '-f', container], capture_output=True, timeout=10)
            except (OSError, subprocess.TimeoutExpired):
                pass
