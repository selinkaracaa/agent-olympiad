from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = REPO_ROOT / "data" / "raw"


class RuntimeUnavailableError(RuntimeError):
    pass


class CompetitionRuntime:
    """Docker-backed task runtime gated by a checked-in runtime manifest."""

    def __init__(self, competition_id: str, problem: dict[str, Any]):
        self.competition_id = competition_id
        self.problem = problem
        self.runtime_root = RAW_ROOT / self._runtime_directory_name()
        self.manifest_path = self.runtime_root / "runtime.json"
        self.manifest = self._load_manifest()

    def _runtime_directory_name(self) -> str:
        return {"ijso_practical": "ijso"}.get(self.competition_id, self.competition_id)

    def _load_manifest(self) -> dict[str, Any]:
        if not self.manifest_path.exists():
            return {
                "status": "unavailable",
                "notes": f"No runtime manifest at {self.manifest_path}",
            }
        with self.manifest_path.open(encoding="utf-8") as handle:
            return json.load(handle)

    @property
    def status(self) -> str:
        return str(self.manifest.get("status", "unavailable"))

    def inspect(self) -> str:
        details: dict[str, Any] = {
            "competition_id": self.competition_id,
            "problem_id": self.problem.get("problem_id"),
            "status": self.status,
            "runtime_root": str(self.runtime_root),
            "notes": self.manifest.get("notes"),
            "docker_available": self._docker_available(),
        }
        if self.competition_id == "cybench" and self.status == "runnable":
            try:
                task_root = self._cybench_task_root()
                compose = self._find_compose_file(task_root)
                details.update(
                    {
                        "task_root": str(task_root),
                        "compose_file": str(compose) if compose else None,
                        "solver_image": self.manifest.get("solver_image"),
                        "solver_image_ready": self._image_exists(
                            str(self.manifest.get("solver_image", ""))
                        ),
                        "challenge_running": self._compose_running(compose),
                    }
                )
            except RuntimeUnavailableError as exc:
                details["status"] = "assets_missing"
                details["asset_error"] = str(exc)
        return json.dumps(details, ensure_ascii=False, indent=2)

    def allows_open_internet(self) -> bool:
        if self.competition_id != "cybench" or self.status != "runnable":
            return False
        try:
            metadata_path = self._cybench_task_root() / "metadata" / "metadata.json"
        except RuntimeUnavailableError:
            return False
        if not metadata_path.exists():
            return False
        with metadata_path.open(encoding="utf-8") as handle:
            internet = (json.load(handle).get("internet") or {})
        return bool(internet.get("useful") or internet.get("necessary"))

    def start(self) -> str:
        self._require_runnable()
        if self.competition_id != "cybench":
            raise RuntimeUnavailableError(
                f"{self.competition_id} has no task-specific start adapter."
            )
        task_root = self._cybench_task_root()
        compose = self._find_compose_file(task_root)
        self._prepare_solver_workspace(task_root)
        if compose is None:
            return (
                "Cybench static challenge workspace prepared. "
                "This task has no service container."
            )
        return self._run_compose(compose, ["up", "-d", "--build", "--force-recreate"])

    def reset(self) -> str:
        self._require_runnable()
        if self.competition_id != "cybench":
            raise RuntimeUnavailableError(
                f"{self.competition_id} has no task-specific reset adapter."
            )
        task_root = self._cybench_task_root()
        compose = self._find_compose_file(task_root)
        if compose is not None:
            self._run_compose(compose, ["down", "--volumes", "--remove-orphans"])
        self._remove_solver_workspace()
        return self.start()

    def execute(self, command: str) -> str:
        self._require_runnable()
        if self.competition_id != "cybench":
            raise RuntimeUnavailableError(
                f"{self.competition_id} does not expose a shell runtime."
            )
        if not command.strip():
            raise ValueError("Environment command cannot be empty.")

        task_root = self._cybench_task_root()
        workspace = self._prepare_solver_workspace(task_root)
        compose = self._find_compose_file(task_root)
        image = str(self.manifest.get("solver_image", "cybench/cybench:latest"))
        if not self._image_exists(image):
            return (
                f"Solver image '{image}' is not built. Run:\n"
                f"docker build -t {image} \"{self.runtime_root / 'upstream'}\""
            )

        args = ["docker", "run", "--rm", "--network", "none"]
        if compose is not None and self._compose_running(compose):
            args[-1] = "shared_net"
        args.extend(
            [
                "--mount",
                f"type=bind,source={workspace},target=/workspace",
                "--workdir",
                "/workspace",
                "--memory",
                "2g",
                "--cpus",
                "2",
                "--pids-limit",
                "256",
                "--security-opt",
                "no-new-privileges",
                "--cap-drop",
                "ALL",
                "--cap-add",
                "SYS_PTRACE",
                "--entrypoint",
                "bash",
                image,
                "-lc",
                command,
            ]
        )
        proc = self._run(args, timeout=30)
        output = (proc.stdout or proc.stderr or "(no output)").strip()
        return f"Environment command exit={proc.returncode}\n{output[:12000]}"

    def _require_runnable(self) -> None:
        if self.status != "runnable":
            raise RuntimeUnavailableError(
                f"{self.competition_id} runtime status is '{self.status}': "
                f"{self.manifest.get('notes', 'no runnable environment')}"
            )

    def _cybench_task_root(self) -> Path:
        source = str(self.problem.get("source_file") or "")
        prefix = "benchmark/Cybench/"
        if not source.startswith(prefix):
            raise RuntimeUnavailableError(
                f"Cybench problem has no recognized upstream source_file: {source!r}"
            )
        relative = Path(source[len(prefix) :])
        root = (self.runtime_root / str(self.manifest["upstream_root"]) / relative).resolve()
        upstream = (self.runtime_root / str(self.manifest["upstream_root"])).resolve()
        if upstream not in root.parents or not root.exists():
            raise RuntimeUnavailableError(f"Cybench task assets are missing: {root}")
        return root

    @staticmethod
    def _find_compose_file(task_root: Path) -> Path | None:
        candidates = []
        for name in ("docker-compose.yml", "compose.yml", "docker-compose.yaml", "compose.yaml"):
            candidates.extend(task_root.glob(name))
            candidates.extend(task_root.glob(f"*/{name}"))
        candidates = [
            path
            for path in candidates
            if "metadata" not in path.parts and "solution" not in path.parts
        ]
        return min(candidates, key=lambda path: len(path.parts)) if candidates else None

    def _project_name(self) -> str:
        problem_id = str(self.problem.get("problem_id", "task"))
        digest = hashlib.sha256(problem_id.encode()).hexdigest()[:10]
        return f"ao_{digest}"

    def _workspace_path(self) -> Path:
        safe_id = re.sub(r"[^a-zA-Z0-9_.-]+", "_", str(self.problem["problem_id"]))
        return self.runtime_root / "workspaces" / safe_id

    def _prepare_solver_workspace(self, task_root: Path) -> Path:
        workspace = self._workspace_path()
        if workspace.exists():
            return workspace

        def ignore(directory: str, names: list[str]) -> set[str]:
            ignored = {
                name
                for name in names
                if name.lower() in {"metadata", "solution", ".git"}
                or name.lower().startswith("readme")
                or name in {"start_docker.sh", "stop_docker.sh"}
            }
            return ignored

        workspace.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(task_root, workspace, ignore=ignore)
        return workspace

    def _remove_solver_workspace(self) -> None:
        workspace = self._workspace_path()
        if workspace.exists():
            shutil.rmtree(workspace)

    def _run_compose(self, compose: Path, action: list[str]) -> str:
        if action and action[0] == "up":
            network = self._run(
                ["docker", "network", "inspect", "shared_net"],
                timeout=15,
            )
            if network.returncode != 0:
                created = self._run(
                    ["docker", "network", "create", "--internal", "shared_net"],
                    timeout=30,
                )
                if created.returncode != 0:
                    raise RuntimeError(
                        "Could not create isolated Cybench network:\n"
                        f"{created.stderr.strip()}"
                    )
        args = [
            "docker",
            "compose",
            "-p",
            self._project_name(),
            "-f",
            str(compose),
            *action,
        ]
        proc = self._run(args, cwd=compose.parent, timeout=300)
        output = (proc.stdout or proc.stderr or "(no output)").strip()
        if proc.returncode != 0:
            raise RuntimeError(f"Docker Compose failed:\n{output[-12000:]}")
        return f"Docker Compose {' '.join(action)} succeeded.\n{output[-12000:]}"

    def _compose_running(self, compose: Path | None) -> bool:
        if compose is None:
            return False
        proc = self._run(
            [
                "docker",
                "compose",
                "-p",
                self._project_name(),
                "-f",
                str(compose),
                "ps",
                "--status",
                "running",
                "--quiet",
            ],
            cwd=compose.parent,
            timeout=15,
        )
        return bool(proc.stdout.strip())

    @staticmethod
    def _image_exists(image: str) -> bool:
        if not image:
            return False
        proc = subprocess.run(
            ["docker", "image", "inspect", image],
            capture_output=True,
            text=True,
            timeout=15,
        )
        return proc.returncode == 0

    @staticmethod
    def _docker_available() -> bool:
        try:
            proc = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            return proc.returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            return False

    @staticmethod
    def _run(
        args: list[str],
        *,
        cwd: Path | None = None,
        timeout: int,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            args,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "COMPOSE_ANSI": "never"},
        )
