import ast
import json
import operator
import os
import re
import subprocess
import sys
from html import unescape
from typing import Any, Optional
from urllib.parse import parse_qs, quote_plus, urlparse
from urllib.request import Request, urlopen

from rules import RuleCardError, load_rule_card
from runtimes import CompetitionRuntime, RuntimeUnavailableError

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_BENCHMARK_PATH = os.path.join(REPO_ROOT, "data", "benchmarks")

TEAM_SIZE_MATRIX = {
    "iol_team": 4,
    "ioaa_group": 5,
    "arml_power": 15,
    "arml_national_team": 15,
    "arml_national_power": 15,
    "arml_local": 6,
    "ijso_practical": 3,
    "ieo_business_case": 5,
    "iypt": 5,
    "fyziklani": 5,
    "hmmt_team": 8,
    "hmmt_guts": 8,
    "mcm": 3,
    "icm": 3,
    "purple_comet": 6,
    "itym": 6,
    "wsc_writing": 3,
    "jessup": 5,
    "iiot": 4,
    "icpc": 3,
    "ccdc": 8,
    "cfa_research_challenge": 4,
    "cybench": 5,
    "debatebench": 8,
    "eoes": 3,
    "ethics_bowl_appe": 5,
    "ethics_bowl_nhseb": 5,
    "gcch_harvard": 4,
    "history_olympiad": 4,
    "ichto": 3,
    "ioaa": 5,
    "ioai": 4,
    "iol": 4,
    "mystery_hunt": 12,
    "nyu_ctf_bench": 5,
    "pumac_power": 8,
    "qanta": 4,
    "science_bowl": 4,
    "vis_moot": 5,
    "wharton_investment": 5,
    "ioai_team": 4,
    "wro": 3,
    "envirothon": 5,
    "science_olympiad": 15,
    "odyssey_of_the_mind": 7,
    "wmtc": 6,
}

COMPETITION_TOOL_REGISTRY = {
    "purple_comet": ["use_calculator"],
    "fyziklani": ["use_calculator"],
    "iiot": ["execute_code"],
    "icpc": ["execute_code"],
    "mcm": ["execute_code", "web_search"],
    "icm": ["execute_code", "web_search"],
    "ieo_business_case": ["use_calculator", "execute_code", "web_search"],
    "jessup": ["web_search"],
    "ijso_practical": ["use_calculator", "inspect_environment"],
    "ioaa_group": ["use_calculator", "read_star_chart"],
    "iol_team": [],
    "arml_power": [],
    "arml_national_team": [],
    "arml_national_power": [],
    "arml_local": [],
    "hmmt_team": [],
    "hmmt_guts": [],
    "wsc_writing": [],
    "cfa_research_challenge": ["use_calculator", "execute_code", "web_search"],
    "eoes": ["use_calculator", "inspect_environment"],
    "ethics_bowl_appe": [],
    "ethics_bowl_nhseb": [],
    "ichto": ["use_calculator", "execute_code", "web_search"],
    "pumac_power": ["use_calculator", "execute_code", "web_search"],
    "vis_moot": ["web_search"],
    "wharton_investment": ["use_calculator", "execute_code", "web_search"],
    "ccdc": ["inspect_environment"],
    "debatebench": [],
    "gcch_harvard": ["use_calculator", "execute_code", "web_search"],
    "ioai_team": ["execute_code", "web_search"],
    "wro": ["inspect_environment"],
    "envirothon": ["web_search"],
    "science_olympiad": ["use_calculator", "read_official_materials"],
    "odyssey_of_the_mind": [],
    "wmtc": [],
    # question-level skill corpora (promoted into primary catalog)
    "qanta": [],
    "science_bowl": [],
    "mystery_hunt": ["execute_code", "web_search"],
    "nyu_ctf_bench": ["execute_code", "web_search"],
    "cybench": [
        "inspect_environment",
        "start_environment",
        "execute_environment_command",
        "reset_environment",
    ],
}

ALL_ACTIONS = {
    "speak",
    "write_scratchpad",
    "submit_final",
    "query_rules",
    "use_calculator",
    "execute_code",
    "web_search",
    "read_official_materials",
    "read_lab_equipment",
    "read_star_chart",
    "inspect_environment",
    "start_environment",
    "execute_environment_command",
    "reset_environment",
}

TOOL_ACTIONS = ALL_ACTIONS - {"speak", "write_scratchpad", "submit_final"}

_SAFE_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_SAFE_UNARYOPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


class ProblemNotFoundError(ValueError):
    pass


class TurnLimitExceededError(RuntimeError):
    pass


class OlympiadEnvironment:
    def __init__(
        self,
        competition_id: str,
        problem_id: str,
        base_path: str = DEFAULT_BENCHMARK_PATH,
        max_turns: Optional[int] = None,
    ):
        self.competition_id = competition_id
        self.problem_id = problem_id
        self.base_path = base_path

        self.chat_history: list[dict[str, str]] = []
        self.action_log: list[dict[str, Any]] = []
        self.workspace = {"scratchpad": "", "final_answer": ""}
        self.current_turn = 0
        self.submitted = False
        self.submitted_by: Optional[str] = None

        self.problem_data = self._load_problem()
        self.rule_card = load_rule_card(competition_id)
        self.max_turns = (
            int(max_turns)
            if max_turns is not None
            else self.rule_card.max_turns
            if self.rule_card is not None
            else 50
        )
        if self.max_turns < 1:
            raise ValueError("max_turns must be positive.")
        self.runtime = CompetitionRuntime(competition_id, self.problem_data)
        if self.rule_card is not None:
            unknown_tools = set(self.rule_card.allowed_tools) - TOOL_ACTIONS
            if unknown_tools:
                raise RuleCardError(
                    f"Rule card for {competition_id!r} declares unknown tools: "
                    + ", ".join(sorted(unknown_tools))
                )
            self.allowed_tools = list(self.rule_card.allowed_tools)
        else:
            self.allowed_tools = list(COMPETITION_TOOL_REGISTRY.get(competition_id, []))
        if competition_id == "cybench" and self.runtime.allows_open_internet():
            self.allowed_tools.append("web_search")

        problem_team_size = self.problem_data.get("team_size")
        rule_default = (
            self.rule_card.team_size_default if self.rule_card is not None else None
        )
        self.team_size = self._coerce_team_size(
            problem_team_size,
            competition_id,
            default_size=rule_default,
        )
        if self.rule_card is not None and not (
            self.rule_card.team_size_min
            <= self.team_size
            <= self.rule_card.team_size_max
        ):
            raise RuleCardError(
                f"Problem {problem_id!r} team_size={self.team_size} is outside rule-card "
                f"range {self.rule_card.team_size_min}-{self.rule_card.team_size_max}."
            )

    @staticmethod
    def _coerce_team_size(
        raw: Any,
        competition_id: str,
        *,
        default_size: Optional[int] = None,
    ) -> int:
        if isinstance(raw, int) and raw > 0:
            return raw
        if isinstance(raw, str) and raw.strip().isdigit():
            return int(raw.strip())
        if default_size is not None:
            return default_size
        return TEAM_SIZE_MATRIX.get(competition_id, 3)

    def _benchmark_file(self) -> str:
        return os.path.join(self.base_path, self.competition_id, "benchmark.json")

    def _load_problem(self) -> dict:
        target_file = self._benchmark_file()
        if not os.path.exists(target_file):
            raise ProblemNotFoundError(
                f"No benchmark file for competition '{self.competition_id}' at {target_file}"
            )

        with open(target_file, "r", encoding="utf-8") as f:
            problems = json.load(f)

        problem = next((p for p in problems if p.get("problem_id") == self.problem_id), None)
        if problem is None:
            available = [p.get("problem_id") for p in problems[:5]]
            suffix = f" (first ids: {available})" if available else ""
            raise ProblemNotFoundError(
                f"Problem '{self.problem_id}' not found in {target_file}{suffix}"
            )
        return problem

    def get_available_tools(self) -> list[str]:
        return list(self.allowed_tools)

    def get_metadata(self) -> dict:
        gold = self.problem_data.get("gold_label") or {}
        metadata = {
            "competition_id": self.competition_id,
            "problem_id": self.problem_id,
            "title": self.problem_data.get("title"),
            "year": self.problem_data.get("year"),
            "task_type": self.problem_data.get("task_type"),
            "team_size": self.team_size,
            "allowed_tools": self.get_available_tools(),
            "has_gold_answer": bool(
                gold.get("expected_answer") or gold.get("parts") or gold.get("answers")
            ),
        }
        if self.rule_card is not None:
            metadata["rule"] = {
                "rule_id": self.rule_card.rule_id,
                "profile": self.rule_card.profile,
                "protocol": self.rule_card.protocol,
                "rules_text": self.rule_card.rules_text,
                "human_constraints": list(self.rule_card.human_constraints),
                "answer_format": self.rule_card.answer_format,
                "scoring": self.rule_card.scoring,
                "submission": self.rule_card.submission,
                "resources": self.rule_card.resources,
                "comparability": self.rule_card.comparability,
                "agent_roles": [
                    {
                        "name": role.name,
                        "title": role.title,
                        "duties": list(role.duties),
                        "may_submit": role.may_submit,
                    }
                    for role in self.rule_card.roster(self.team_size)
                ],
            }
        return metadata

    def query_rules(self, query: str = "") -> str:
        if self.rule_card is None:
            return json.dumps(
                {
                    "competition_id": self.competition_id,
                    "allowed_tools": self.get_available_tools(),
                    "team_size": self.team_size,
                    "note": "No rule card on file; legacy env defaults are in effect.",
                },
                ensure_ascii=False,
                indent=2,
            )
        card = self.rule_card
        payload = {
            "rule_id": card.rule_id,
            "competition_id": card.competition_id,
            "profile": card.profile,
            "protocol": card.protocol,
            "rules_text": card.rules_text,
            "human_constraints": list(card.human_constraints),
            "answer_format": card.answer_format,
            "allowed_tools": list(card.allowed_tools),
            "resources": card.resources,
            "scoring": card.scoring,
            "comparability": card.comparability,
            "agent_roles": [
                {
                    "name": role.name,
                    "title": role.title,
                    "duties": list(role.duties),
                    "may_submit": role.may_submit,
                }
                for role in card.roster(self.team_size)
            ],
        }
        prefix = f"Rule query: {query}\n" if query.strip() else ""
        return prefix + json.dumps(payload, ensure_ascii=False, indent=2)

    def get_state(self) -> dict:
        return {
            "competition_id": self.competition_id,
            "problem_id": self.problem_id,
            "team_size": self.team_size,
            "allowed_tools": self.get_available_tools(),
            "problem_statement": self.problem_data["problem_description"],
            "chat_logs": list(self.chat_history),
            "shared_workspace": dict(self.workspace),
            "turn_status": f"{self.current_turn}/{self.max_turns}",
            "submitted": self.submitted,
        }

    def _check_turn_limit(self) -> None:
        if self.current_turn >= self.max_turns:
            raise TurnLimitExceededError(
                f"Turn limit reached ({self.max_turns}) for {self.problem_id}"
            )

    def _log_action(self, agent_name: str, action_type: str, payload: str, result: str) -> None:
        self.action_log.append(
            {
                "turn": self.current_turn,
                "agent": agent_name,
                "action": action_type,
                "payload": payload,
                "result": result,
            }
        )

    def validate_action(self, action_type: str) -> Optional[str]:
        if action_type not in ALL_ACTIONS:
            return f"Unrecognized action '{action_type}'."
        if action_type in TOOL_ACTIONS and action_type not in self.allowed_tools:
            return (
                f"RULE VIOLATION: Tool '{action_type}' is banned in {self.competition_id}. "
                f"Allowed tools: {self.allowed_tools or 'none (paper and pencil only)'}"
            )
        if action_type == "submit_final" and self.submitted:
            return "Submission already finalized; further submit_final actions are ignored."
        return None

    def execute_action(self, agent_name: str, action_type: str, payload: str) -> str:
        self._check_turn_limit()
        self.current_turn += 1

        violation = self.validate_action(action_type)
        if violation:
            self._log_action(agent_name, action_type, payload, violation)
            return violation

        if action_type == "speak":
            self.chat_history.append({"sender": agent_name, "message": payload})
            result = "Message broadcast to all agents."
        elif action_type == "write_scratchpad":
            self.workspace["scratchpad"] = payload
            result = "Shared scratchpad updated."
        elif action_type == "submit_final":
            error = self._validate_submission(payload)
            if error:
                result = error
            else:
                self.workspace["final_answer"] = payload.strip()
                self.submitted = True
                self.submitted_by = agent_name
                result = f"Submission finalized by {agent_name}."
        elif action_type == "query_rules":
            result = self.query_rules(payload)
        elif action_type == "use_calculator":
            result = self._run_calculator(payload)
        elif action_type == "execute_code":
            result = self._run_code(payload)
        elif action_type == "web_search":
            result = self._run_web_search(payload)
        elif action_type == "read_official_materials":
            result = self._read_official_materials(payload)
        elif action_type == "read_lab_equipment":
            result = (
                "Lab equipment is not connected to a task-specific simulator. "
                "Use inspect_environment for the verified runtime status."
            )
        elif action_type == "read_star_chart":
            result = f"[read_star_chart stub] Simulated star chart for: {payload}"
        elif action_type == "inspect_environment":
            result = self.runtime.inspect()
        elif action_type == "start_environment":
            result = self._run_runtime_action("start", payload)
        elif action_type == "execute_environment_command":
            result = self._run_runtime_action("execute", payload)
        elif action_type == "reset_environment":
            result = self._run_runtime_action("reset", payload)
        else:
            result = f"Operational error: action '{action_type}' not implemented."

        self._log_action(agent_name, action_type, payload, result)
        return result

    def _validate_submission(self, payload: str) -> Optional[str]:
        if not payload or not payload.strip():
            return "Submission rejected: final answer cannot be empty."
        if len(payload.strip()) < 10:
            return "Submission rejected: final answer is too short (minimum 10 characters)."
        return None

    @staticmethod
    def _safe_calculate(expression: str) -> str:
        try:
            node = ast.parse(expression.strip(), mode="eval")
            value = OlympiadEnvironment._eval_ast(node.body)
            return str(value)
        except (SyntaxError, ValueError, TypeError, ZeroDivisionError, OverflowError) as exc:
            return f"Calculator error: {exc}"

    @staticmethod
    def _eval_ast(node: ast.AST) -> float:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.BinOp) and type(node.op) in _SAFE_BINOPS:
            left = OlympiadEnvironment._eval_ast(node.left)
            right = OlympiadEnvironment._eval_ast(node.right)
            return float(_SAFE_BINOPS[type(node.op)](left, right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _SAFE_UNARYOPS:
            return float(_SAFE_UNARYOPS[type(node.op)](OlympiadEnvironment._eval_ast(node.operand)))
        raise ValueError("Only basic arithmetic expressions are allowed.")

    def _run_calculator(self, payload: str) -> str:
        return f"Calculator output: {self._safe_calculate(payload)}"

    def _run_code(self, payload: str) -> str:
        try:
            proc = subprocess.run(
                [sys.executable, "-I", "-c", payload],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=REPO_ROOT,
            )
            if proc.returncode == 0:
                output = (proc.stdout or "").strip() or "(no stdout)"
                return f"Code output:\n{output}"
            stderr = (proc.stderr or proc.stdout or "unknown error").strip()
            return f"Code error (exit {proc.returncode}):\n{stderr}"
        except subprocess.TimeoutExpired:
            return "Code error: execution timed out after 5 seconds."
        except OSError as exc:
            return f"Code error: {exc}"

    @staticmethod
    def _run_web_search(query: str) -> str:
        if not query.strip():
            return "Web search error: query cannot be empty."
        try:
            request = Request(
                f"https://lite.duckduckgo.com/lite/?q={quote_plus(query.strip())}",
                headers={"User-Agent": "Mozilla/5.0 AgentOlympiad/1.0"},
            )
            with urlopen(request, timeout=10) as response:
                html = response.read(1_000_000).decode("utf-8", errors="replace")
            matches = re.findall(
                r"<a[^>]+href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>",
                html,
                flags=re.IGNORECASE | re.DOTALL,
            )
            results = []
            for url, title_html in matches:
                title = unescape(re.sub(r"<[^>]+>", "", title_html)).strip()
                if not title or title.lower() == "duckduckgo":
                    continue
                if url.startswith("//duckduckgo.com/l/"):
                    url = parse_qs(urlparse("https:" + url).query).get("uddg", [url])[0]
                results.append(f"- {title}\n  {unescape(url)}")
                if len(results) == 5:
                    break
            if not results:
                return "Web search returned no parseable results."
            return "Web search results:\n" + "\n".join(results)
        except (OSError, TimeoutError, ValueError) as exc:
            return f"Web search error: {exc}"

    def _read_official_materials(self, query: str) -> str:
        raw_root = os.path.realpath(os.path.join(REPO_ROOT, "data", "raw"))
        declared = [self.problem_data.get("source_file")]
        declared.extend(self.problem_data.get("agent_visible_files") or [])
        files = []
        for value in declared:
            if not value:
                continue
            candidate = os.path.realpath(os.path.join(REPO_ROOT, str(value)))
            if os.path.commonpath([candidate, raw_root]) != raw_root:
                continue
            if os.path.isfile(candidate):
                files.append(candidate)

        if not files:
            return (
                "Official-material lookup unavailable: this problem has no existing "
                "agent-visible source files under data/raw."
            )

        needle = query.strip().lower()
        excerpts = []
        for path in files[:10]:
            try:
                if path.lower().endswith(".pdf"):
                    from pypdf import PdfReader

                    pages = []
                    for page in PdfReader(path).pages:
                        page_text = page.extract_text() or ""
                        if re.search(r"\bANSWER\s+KEY\b", page_text[:500], re.IGNORECASE):
                            break
                        pages.append(page_text)
                    text = "\n".join(pages)
                elif path.lower().endswith((".txt", ".md", ".json", ".csv")):
                    with open(path, "r", encoding="utf-8", errors="replace") as handle:
                        text = handle.read(2_000_000)
                else:
                    excerpts.append(f"{os.path.relpath(path, REPO_ROOT)} (binary material)")
                    continue
            except (OSError, ValueError) as exc:
                excerpts.append(f"{os.path.relpath(path, REPO_ROOT)}: read error: {exc}")
                continue

            if not needle:
                excerpt = text[:1500]
            else:
                index = text.lower().find(needle)
                if index < 0:
                    continue
                excerpt = text[max(0, index - 500) : index + len(needle) + 1000]
            excerpts.append(f"=== {os.path.relpath(path, REPO_ROOT)} ===\n{excerpt.strip()}")

        if not excerpts:
            return f"No occurrence of {query!r} in the declared official materials."
        return "\n\n".join(excerpts)[:12000]

    def _run_runtime_action(self, action: str, payload: str) -> str:
        try:
            if action == "start":
                return self.runtime.start()
            if action == "execute":
                return self.runtime.execute(payload)
            if action == "reset":
                return self.runtime.reset()
            return f"Unknown runtime action: {action}"
        except (RuntimeUnavailableError, RuntimeError, ValueError, OSError) as exc:
            return f"Environment error: {exc}"
        except subprocess.TimeoutExpired:
            return "Environment error: Docker operation timed out."

    @staticmethod
    def _normalize_answer(text: str) -> str:
        return " ".join(text.lower().split())

    def grade_submission(self) -> dict:
        if not self.submitted:
            return {
                "graded": False,
                "reason": "No submission yet.",
                "score": None,
                "max_score": None,
            }

        answer = self.workspace["final_answer"]
        gold = self.problem_data.get("gold_label", {})
        expected = gold.get("expected_answer")
        rubric = gold.get("grading_rubric") or ""

        if expected:
            norm_answer = self._normalize_answer(answer)
            norm_gold = self._normalize_answer(str(expected))
            if norm_gold in norm_answer or norm_answer in norm_gold:
                return {
                    "graded": True,
                    "method": "gold_substring_match",
                    "score": 1.0,
                    "max_score": 1.0,
                    "correct": True,
                    "submitted_by": self.submitted_by,
                }
            return {
                "graded": True,
                "method": "gold_substring_match",
                "score": 0.0,
                "max_score": 1.0,
                "correct": False,
                "submitted_by": self.submitted_by,
                "note": "Answer did not match gold via substring check; use LLM judge for partial credit.",
            }

        task_type = self.problem_data.get("task_type", "")
        if task_type in {"algorithmic_programming", "programming"}:
            return {
                "graded": False,
                "method": "judge_sandbox_required",
                "score": None,
                "max_score": None,
                "reason": "ICPC/IIOT problems require an automated judge, not text gold.",
                "submitted_by": self.submitted_by,
            }

        return {
            "graded": False,
            "method": "llm_judge_required",
            "score": None,
            "max_score": None,
            "reason": "No exact gold answer on file; use LLM or human judge.",
            "grading_rubric": rubric,
            "submitted_by": self.submitted_by,
        }

    def reset(self) -> None:
        self.chat_history.clear()
        self.action_log.clear()
        self.workspace = {"scratchpad": "", "final_answer": ""}
        self.current_turn = 0
        self.submitted = False
        self.submitted_by = None
