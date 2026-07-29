"""Generate the current formal benchmark statistical figures.

Data contract:
  - primary session catalog: data/benchmarks/index_new.json
  - auxiliary corpora: data/benchmarks/index_aux.json

Reads the merged catalog data/benchmarks/index_new.json (index.json core + promotions).
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, Patch


REPO = Path(__file__).resolve().parents[2]
BENCHMARKS = REPO / "data" / "benchmarks"
OUTPUT = REPO / "data" / "viz"

SNAPSHOT_DATE = "2026-07-28"
TAXONOMY_VERSION = "2026-07-28.formal-v1"

COLORS = {
    "blue": "#1f7398",
    "orange": "#c85a22",
    "green": "#2f7055",
    "purple": "#7044aa",
    "gold": "#bd8704",
    "gray": "#aaa5a0",
    "light_gray": "#e6e3df",
    "ink": "#202020",
    "muted": "#5e5a56",
    "paper": "#f6f2ea",
    "panel": "#ffffff",
    "grid": "#d8d4cf",
}

TYPE_COLORS = {
    "test_based": COLORS["blue"],
    "rubric_based": COLORS["orange"],
}

STATUS_COLORS = {
    "collected": COLORS["green"],
    "partial": COLORS["orange"],
    "pipeline_working": COLORS["purple"],
}

COARSE_DOMAINS = (
    "Math & modeling",
    "Science & engineering",
    "Computing & AI",
    "Cybersecurity",
    "Humanities, language & puzzles",
    "Law, ethics & debate",
    "Business & economics",
)

COARSE_COLORS = {
    "Math & modeling": COLORS["blue"],
    "Science & engineering": "#3b8fb2",
    "Computing & AI": COLORS["purple"],
    "Cybersecurity": "#8b5fbf",
    "Humanities, language & puzzles": COLORS["orange"],
    "Law, ethics & debate": "#d7834a",
    "Business & economics": COLORS["green"],
}

# index_new has eight historical entries without an explicit domain. Keep this
# mapping versioned so figures never silently depend on missing catalog fields.
DOMAIN_OVERRIDES = {
    "ijso_practical": "Science lab",
    "ieo_business_case": "Economics / Business",
    "iol_team": "Linguistics",
    "ioaa_group": "Astronomy",
    "arml_power": "Mathematics",
    "arml_national_team": "Mathematics",
    "arml_national_power": "Mathematics",
    "arml_local": "Mathematics",
}

DOMAIN_TO_COARSE = {
    "Mathematics": "Math & modeling",
    "Math modeling": "Math & modeling",
    "Physics": "Science & engineering",
    "Science lab": "Science & engineering",
    "Science / STEM": "Science & engineering",
    "Chemistry": "Science & engineering",
    "Astronomy": "Science & engineering",
    "Environmental science": "Science & engineering",
    "Robotics / STEM": "Science & engineering",
    "Artificial Intelligence": "Computing & AI",
    "Informatics / Computer Science": "Computing & AI",
    "Cybersecurity / CTF": "Cybersecurity",
    "History": "Humanities, language & puzzles",
    "Literature / Humanities": "Humanities, language & puzzles",
    "Linguistics": "Humanities, language & puzzles",
    "Creative problem-solving": "Humanities, language & puzzles",
    "International Law": "Law, ethics & debate",
    "Ethics": "Law, ethics & debate",
    "Debate": "Law, ethics & debate",
    "Finance": "Business & economics",
    "Business / Case": "Business & economics",
    "Economics / Business": "Business & economics",
}

TASK_MODE = {
    "ijso_practical": "Lab / design",
    "ieo_business_case": "Research / case",
    "iol_team": "Timed problem solving",
    "ioaa_group": "Timed problem solving",
    "arml_power": "Timed problem solving",
    "arml_national_team": "Timed problem solving",
    "arml_national_power": "Timed problem solving",
    "arml_local": "Timed problem solving",
    "wsc_writing": "Argument / writing",
    "jessup": "Argument / writing",
    "iiot": "Programming",
    "icpc": "Programming",
    "cfa_research_challenge": "Research / case",
    "eoes": "Lab / design",
    "ethics_bowl_appe": "Argument / writing",
    "ethics_bowl_nhseb": "Argument / writing",
    "ichto": "Lab / design",
    "modeling_agent": "Research / case",
    "pumac_power": "Timed problem solving",
    "vis_moot": "Argument / writing",
    "wharton_investment": "Research / case",
    "ccdc": "Cyber operations",
    "debatebench": "Argument / writing",
    "gcch_harvard": "Research / case",
    "history_olympiad": "Timed problem solving",
    "envirothon": "Lab / design",
    "ioai_team": "Lab / design",
    "science_olympiad": "Lab / design",
    "wro": "Lab / design",
    "odyssey_of_the_mind": "Quiz / puzzle",
    "wmtc": "Timed problem solving",
    "fyziklani": "Timed problem solving",
    "hmmt_guts": "Timed problem solving",
    "purple_comet": "Timed problem solving",
}

FIGURES = [
    ("01_overview", "Current formal-catalog overview"),
    ("02_scale_by_track", "Primary session scale and auxiliary row scale"),
    ("03_domain_type_heatmap", "Coarse domain by catalog evaluator type"),
    ("04_teamsize_scale_scatter", "Configured team size and primary scale"),
    ("05_coverage_gold", "Field, payload, path, and governance completeness"),
    ("06_year_coverage", "Exact-year primary archive presence"),
    ("07_family_radar", "Domain weighting sensitivity"),
    ("08_task_types", "Coarse task-mode mix under two weighting views"),
    ("09_storyboard", "Multi-dimensional formal-catalog storyboard"),
    ("10_domains_pie", "Coarse-domain composition pie charts"),
    ("11_domain_weighting_divergence", "Detailed-domain weighting divergence"),
    ("12_benchmark_profiles", "Per-benchmark multi-dimensional profiles"),
    (
        "13_question_distribution",
        "Current primary question and task-unit distribution",
    ),
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_gold_claim(raw: Any) -> str:
    if raw is True:
        return "full"
    if isinstance(raw, str) and raw.strip().lower() == "partial":
        return "partial"
    return "missing"


def nonempty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict, tuple, set)):
        return bool(value)
    return True


def nested(row: dict[str, Any], *keys: str) -> Any:
    value: Any = row
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def field_state(rows: list[dict[str, Any]], getter: Callable[[dict[str, Any]], Any]) -> str:
    present = sum(nonempty(getter(row)) for row in rows)
    if present == 0:
        return "missing"
    if present == len(rows):
        return "full"
    return "partial"


def path_state(rows: list[dict[str, Any]], key: str) -> str:
    present = 0
    for row in rows:
        raw = row.get(key)
        if isinstance(raw, str) and raw.strip() and (REPO / raw).is_file():
            present += 1
    if present == 0:
        return "missing"
    if present == len(rows):
        return "full"
    return "partial"


def extract_years(value: Any) -> set[int]:
    if isinstance(value, bool) or value is None:
        return set()
    if isinstance(value, int):
        return {value} if 1900 <= value <= 2030 else set()
    if isinstance(value, float) and value.is_integer():
        year = int(value)
        return {year} if 1900 <= year <= 2030 else set()
    if isinstance(value, str):
        return {
            int(match)
            for match in re.findall(r"(?:19|20)\d{2}", value)
            if 1900 <= int(match) <= 2030
        }
    if isinstance(value, (list, tuple, set)):
        result: set[int] = set()
        for item in value:
            result.update(extract_years(item))
        return result
    return set()


def parse_team_config(raw: Any) -> tuple[list[float], bool]:
    if isinstance(raw, int) and raw > 0:
        return [float(raw)], False
    text = str(raw or "").strip().lower()
    values = [float(value) for value in re.findall(r"\d+(?:\.\d+)?", text)]
    if not values:
        return [], False
    is_range = bool(re.search(r"\d\s*[-–]\s*\d", text))
    if "or" in text:
        is_range = False
    return values, is_range


def source_family(dataset_id: str) -> str:
    return "arml" if dataset_id.startswith("arml_") else dataset_id


def compact_number(value: int) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}k"
    return f"{value:,}"


def configure_style() -> None:
    mpl.rcParams.update(
        {
            "figure.facecolor": COLORS["paper"],
            "axes.facecolor": COLORS["panel"],
            "savefig.facecolor": COLORS["paper"],
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.titlesize": 14,
            "axes.titleweight": "bold",
            "axes.labelsize": 11,
            "xtick.color": "#475569",
            "ytick.color": "#475569",
            "axes.labelcolor": COLORS["ink"],
            "text.color": COLORS["ink"],
            "axes.edgecolor": "#9aa7b7",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "grid.color": COLORS["grid"],
            "grid.alpha": 0.7,
            "grid.linestyle": "--",
            "legend.frameon": False,
        }
    )


def save_figure(fig: plt.Figure, stem: str) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT / f"{stem}.png", dpi=190, bbox_inches="tight")
    plt.close(fig)


def annotate_bars(ax: plt.Axes, bars: Any, *, fmt: Callable[[float], str] | None = None) -> None:
    formatter = fmt or (lambda value: f"{int(round(value)):,}")
    for bar in bars:
        value = float(bar.get_width())
        ax.text(
            value,
            bar.get_y() + bar.get_height() / 2,
            "  " + formatter(value),
            va="center",
            fontsize=9,
            color=COLORS["muted"],
        )


def load_portfolio() -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, list[dict[str, Any]]],
    dict[str, list[dict[str, Any]]],
]:
    primary_catalog = load_json(BENCHMARKS / "index_new.json")["olympiads"]
    auxiliary_catalog = load_json(BENCHMARKS / "index_aux.json")["olympiads"]
    primary_rows: dict[str, list[dict[str, Any]]] = {}
    auxiliary_rows: dict[str, list[dict[str, Any]]] = {}

    for entry in primary_catalog:
        rows = load_json(REPO / entry["benchmark_path"])
        if not isinstance(rows, list):
            raise TypeError(entry["benchmark_path"])
        primary_rows[entry["id"]] = rows
        collected_rows = sum(
            (row.get("status") or "collected") != "placeholder" for row in rows
        )
        declared_rows = int(entry["problems_collected"])
        if declared_rows not in {len(rows), collected_rows}:
            raise AssertionError(
                f"{entry['id']}: index={declared_rows} actual={len(rows)} "
                f"non_placeholder={collected_rows}"
            )
        entry["_domain"] = entry.get("domain") or DOMAIN_OVERRIDES.get(entry["id"])
        if not entry["_domain"]:
            raise AssertionError(f"Missing domain taxonomy for {entry['id']}")
        entry["_coarse_domain"] = DOMAIN_TO_COARSE.get(entry["_domain"])
        if not entry["_coarse_domain"]:
            raise AssertionError(
                f"Missing coarse domain for {entry['id']}: {entry['_domain']}"
            )

    for entry in auxiliary_catalog:
        rows = load_json(REPO / entry["benchmark_path"])
        if not isinstance(rows, list):
            raise TypeError(entry["benchmark_path"])
        auxiliary_rows[entry["id"]] = rows
        collected_rows = sum(
            (row.get("status") or "collected") != "placeholder" for row in rows
        )
        declared_rows = int(entry["problems_collected"])
        if declared_rows not in {len(rows), collected_rows}:
            raise AssertionError(
                f"{entry['id']}: index={declared_rows} actual={len(rows)} "
                f"non_placeholder={collected_rows}"
            )

    primary_ids = {entry["id"] for entry in primary_catalog}
    if set(TASK_MODE) != primary_ids:
        raise AssertionError(
            f"Task-mode taxonomy mismatch: missing={primary_ids - set(TASK_MODE)}, "
            f"extra={set(TASK_MODE) - primary_ids}"
        )
    if len(primary_ids) != len(primary_catalog):
        raise AssertionError("Duplicate primary catalog ID")
    if len({entry["id"] for entry in auxiliary_catalog}) != len(auxiliary_catalog):
        raise AssertionError("Duplicate auxiliary catalog ID")

    all_primary_problem_ids = [
        row.get("problem_id")
        for rows in primary_rows.values()
        for row in rows
    ]
    if len(all_primary_problem_ids) != len(set(all_primary_problem_ids)):
        raise AssertionError("Primary problem_id values are not globally unique")

    return primary_catalog, auxiliary_catalog, primary_rows, auxiliary_rows


def build_metrics() -> dict[str, Any]:
    primary, auxiliary, primary_rows, auxiliary_rows = load_portfolio()
    primary_total = sum(len(rows) for rows in primary_rows.values())
    auxiliary_total = sum(len(rows) for rows in auxiliary_rows.values())

    type_counts = Counter(entry["type"] for entry in primary)
    status_counts = Counter(entry["status"] for entry in primary)
    catalog_gold = Counter(
        normalize_gold_claim((entry.get("gold_scores") or {}).get("available"))
        for entry in primary
    )
    row_status = Counter(
        row.get("status") or "missing"
        for rows in primary_rows.values()
        for row in rows
    )

    track_metrics: dict[str, dict[str, Any]] = {}
    for entry in primary:
        dataset_id = entry["id"]
        rows = primary_rows[dataset_id]
        years: set[int] = set()
        for row in rows:
            years.update(extract_years(row.get("year")))

        expected_present = sum(
            nonempty(nested(row, "gold_label", "expected_answer")) for row in rows
        )
        rubric_present = sum(
            nonempty(nested(row, "gold_label", "grading_rubric")) for row in rows
        )
        baseline_present = sum(
            nonempty(nested(row, "gold_label", "human_baseline")) for row in rows
        )
        team_values, team_is_range = parse_team_config(entry.get("team_size"))
        track_metrics[dataset_id] = {
            "id": dataset_id,
            "entry": entry,
            "rows": rows,
            "count": len(rows),
            "domain": entry["_domain"],
            "coarse_domain": entry["_coarse_domain"],
            "type": entry["type"],
            "status": entry["status"],
            "catalog_gold": normalize_gold_claim(
                (entry.get("gold_scores") or {}).get("available")
            ),
            "expected_present": expected_present,
            "rubric_present": rubric_present,
            "baseline_present": baseline_present,
            "embedded_answer_fraction": expected_present / len(rows),
            "years": years,
            "team_values": team_values,
            "team_is_range": team_is_range,
            "task_mode": TASK_MODE[dataset_id],
            "source_family": source_family(dataset_id),
        }

    embedded_answer_rows = sum(
        metric["expected_present"] for metric in track_metrics.values()
    )
    rubric_rows = sum(metric["rubric_present"] for metric in track_metrics.values())
    baseline_rows = sum(metric["baseline_present"] for metric in track_metrics.values())
    question_count_by_dataset: dict[str, int] = {}
    question_count_rows_by_dataset: dict[str, int] = {}
    question_units_by_dataset: dict[str, int] = {}
    for dataset_id, metric in track_metrics.items():
        explicit_counts = [
            int(row["question_count"])
            for row in metric["rows"]
            if isinstance(row.get("question_count"), (int, float))
            and not isinstance(row.get("question_count"), bool)
            and int(row["question_count"]) > 0
        ]
        if explicit_counts:
            question_count_by_dataset[dataset_id] = sum(explicit_counts)
            question_count_rows_by_dataset[dataset_id] = len(explicit_counts)
        question_units_by_dataset[dataset_id] = sum(
            (
                int(row["question_count"])
                if isinstance(row.get("question_count"), (int, float))
                and not isinstance(row.get("question_count"), bool)
                and int(row["question_count"]) > 0
                else 1
            )
            for row in metric["rows"]
        )

    all_primary_years = sorted(
        {
            year
            for metric in track_metrics.values()
            for year in metric["years"]
        }
    )

    return {
        "primary": primary,
        "auxiliary": auxiliary,
        "primary_rows": primary_rows,
        "auxiliary_rows": auxiliary_rows,
        "tracks": track_metrics,
        "primary_total": primary_total,
        "auxiliary_total": auxiliary_total,
        "type_counts": type_counts,
        "status_counts": status_counts,
        "catalog_gold": catalog_gold,
        "row_status": row_status,
        "embedded_answer_rows": embedded_answer_rows,
        "rubric_rows": rubric_rows,
        "baseline_rows": baseline_rows,
        "question_count_by_dataset": question_count_by_dataset,
        "question_count_rows_by_dataset": question_count_rows_by_dataset,
        "question_units_by_dataset": question_units_by_dataset,
        "all_primary_years": all_primary_years,
        "n_source_families": len(
            {metric["source_family"] for metric in track_metrics.values()}
        ),
    }


def draw_stat_card(ax: plt.Axes, value: str, label: str, note: str = "") -> None:
    ax.set_axis_off()
    card = FancyBboxPatch(
        (0.02, 0.06),
        0.96,
        0.86,
        boxstyle="round,pad=0.02,rounding_size=0.08",
        transform=ax.transAxes,
        facecolor=COLORS["panel"],
        edgecolor="#d5d1cc",
        linewidth=1.2,
    )
    ax.add_patch(card)
    ax.text(
        0.5,
        0.60,
        value,
        ha="center",
        va="center",
        transform=ax.transAxes,
        fontsize=28,
        fontweight="bold",
        color=COLORS["blue"],
    )
    ax.text(
        0.5,
        0.32,
        label,
        ha="center",
        va="center",
        transform=ax.transAxes,
        fontsize=11,
        color=COLORS["muted"],
    )
    if note:
        ax.text(
            0.5,
            0.17,
            note,
            ha="center",
            va="center",
            transform=ax.transAxes,
            fontsize=8,
            color="#7d7872",
        )


def figure_overview(metrics: dict[str, Any]) -> None:
    fig = plt.figure(figsize=(18, 11.5), constrained_layout=True)
    fig.set_constrained_layout_pads(
        w_pad=6 / 72,
        h_pad=8 / 72,
        wspace=0.16,
        hspace=0.08,
    )
    grid = fig.add_gridspec(3, 4, height_ratios=[0.86, 0.08, 1.48])

    fig.suptitle(
        "OlympiadMAS — formal multi-agent benchmark snapshot",
        fontsize=22,
        fontweight="bold",
    )
    fig.text(
        0.5,
        0.943,
        "index_new.json primary session catalog + index_aux.json auxiliary corpora",
        ha="center",
        fontsize=11.5,
        color="#475569",
    )

    total_ids = len(metrics["primary"]) + len(metrics["auxiliary"])
    cards = [
        (f"{total_ids}", "Catalog dataset IDs", "34 primary + 6 auxiliary"),
        (f"{len(metrics['primary'])}", "Primary session datasets", f"{metrics['n_source_families']} source families"),
        (f"{metrics['primary_total']:,}", "Primary session records", "actual JSON rows"),
        (f"{metrics['auxiliary_total']:,}", "Auxiliary corpus rows", "different unit; shown separately"),
    ]
    for column, values in enumerate(cards):
        draw_stat_card(fig.add_subplot(grid[0, column]), *values)

    ax_role = fig.add_subplot(grid[2, 0])
    role_values = [len(metrics["primary"]), len(metrics["auxiliary"])]
    ax_role.bar(
        ["Primary\nsession IDs", "Auxiliary\ncorpora"],
        role_values,
        color=[COLORS["blue"], COLORS["gold"]],
        width=0.65,
    )
    for index, value in enumerate(role_values):
        ax_role.text(index, value + 0.7, str(value), ha="center", fontweight="bold")
    ax_role.set_title("Catalog roles", fontsize=11, pad=10)
    ax_role.set_ylabel("# dataset IDs")
    ax_role.set_ylim(0, max(role_values) * 1.2)
    ax_role.grid(axis="y")

    ax_type = fig.add_subplot(grid[2, 1])
    type_labels = ["Test-based", "Rubric-based"]
    type_values = [
        metrics["type_counts"]["test_based"],
        metrics["type_counts"]["rubric_based"],
    ]
    bars = ax_type.bar(
        type_labels,
        type_values,
        color=[COLORS["blue"], COLORS["orange"]],
        width=0.62,
    )
    for bar, value in zip(bars, type_values):
        ax_type.text(
            bar.get_x() + bar.get_width() / 2,
            value + 0.5,
            str(value),
            ha="center",
            fontweight="bold",
        )
    ax_type.set_title("Catalog evaluator type\n(primary)", fontsize=11, pad=10)
    ax_type.set_ylabel("# dataset IDs")
    ax_type.set_ylim(0, max(type_values) * 1.22)
    ax_type.grid(axis="y")

    ax_domain = fig.add_subplot(grid[2, 2])
    domain_counts = Counter(
        metric["coarse_domain"] for metric in metrics["tracks"].values()
    )
    domain_order = sorted(COARSE_DOMAINS, key=domain_counts.get)
    domain_values = [domain_counts[domain] for domain in domain_order]
    bars = ax_domain.barh(
        domain_order,
        domain_values,
        color=[COARSE_COLORS[domain] for domain in domain_order],
    )
    annotate_bars(ax_domain, bars)
    ax_domain.set_title(
        "Coarse-domain breadth\n(equal ID weight)",
        fontsize=11,
        pad=10,
    )
    ax_domain.set_xlabel("# primary dataset IDs")
    ax_domain.grid(axis="x")

    ax_status = fig.add_subplot(grid[2, 3])
    status_order = ["collected", "partial", "pipeline_working"]
    status_labels = ["Collected", "Partial", "Pipeline working"]
    status_values = [metrics["status_counts"][status] for status in status_order]
    bars = ax_status.barh(
        status_labels,
        status_values,
        color=[STATUS_COLORS[status] for status in status_order],
    )
    annotate_bars(ax_status, bars)
    ax_status.set_title(
        "Catalog collection status\n(primary)",
        fontsize=11,
        pad=10,
    )
    ax_status.set_xlabel("# dataset IDs")
    ax_status.grid(axis="x")

    save_figure(fig, "01_overview")


def figure_scale(metrics: dict[str, Any]) -> None:
    fig, (ax_primary, ax_aux) = plt.subplots(
        1,
        2,
        figsize=(17, 14),
        gridspec_kw={"width_ratios": [1.17, 0.83]},
        constrained_layout=True,
    )
    fig.suptitle(
        "Dataset scale: primary sessions vs auxiliary rows",
        fontsize=19,
        fontweight="bold",
    )

    primary_items = sorted(
        metrics["tracks"].values(), key=lambda metric: metric["count"]
    )
    labels = [metric["id"] for metric in primary_items]
    values = [metric["count"] for metric in primary_items]
    colors = [TYPE_COLORS[metric["type"]] for metric in primary_items]
    bars = ax_primary.barh(labels, values, color=colors)
    annotate_bars(ax_primary, bars)
    ax_primary.set_title(
        f"Primary: {metrics['primary_total']:,} session records across {len(labels)} dataset IDs"
    )
    ax_primary.set_xlabel("# session records")
    ax_primary.grid(axis="x")
    ax_primary.legend(
        handles=[
            Patch(color=TYPE_COLORS["test_based"], label="Test-based"),
            Patch(color=TYPE_COLORS["rubric_based"], label="Rubric-based"),
        ],
        loc="lower right",
    )

    auxiliary_items = sorted(
        (
            (entry["id"], len(metrics["auxiliary_rows"][entry["id"]]))
            for entry in metrics["auxiliary"]
        ),
        key=lambda item: item[1],
    )
    aux_labels = [item[0] for item in auxiliary_items]
    aux_values = [item[1] for item in auxiliary_items]
    bars = ax_aux.barh(aux_labels, aux_values, color=COLORS["gold"])
    ax_aux.set_xscale("log")
    for bar, value in zip(bars, aux_values):
        ax_aux.text(
            value * 1.05,
            bar.get_y() + bar.get_height() / 2,
            f"{value:,}",
            va="center",
            fontsize=9,
            color=COLORS["muted"],
        )
    ax_aux.set_title(
        f"Auxiliary: {metrics['auxiliary_total']:,} rows across {len(aux_labels)} corpora"
    )
    ax_aux.set_xlabel("# corpus rows (log scale)")
    ax_aux.grid(axis="x", which="both")

    save_figure(fig, "02_scale_by_track")


def figure_domain_type(metrics: dict[str, Any]) -> None:
    matrix = np.zeros((len(COARSE_DOMAINS), 2), dtype=int)
    types = ("test_based", "rubric_based")
    for metric in metrics["tracks"].values():
        row = COARSE_DOMAINS.index(metric["coarse_domain"])
        column = types.index(metric["type"])
        matrix[row, column] += 1

    fig, ax = plt.subplots(figsize=(10.5, 8), constrained_layout=True)
    image = ax.imshow(matrix, cmap="Blues", aspect="auto", vmin=0)
    ax.set_xticks(range(2), ["Test-based", "Rubric-based"])
    ax.set_yticks(range(len(COARSE_DOMAINS)), COARSE_DOMAINS)
    ax.set_title(
        "Primary domain × evaluator type\n(equal benchmark-ID weight)"
    )
    for row in range(matrix.shape[0]):
        for column in range(matrix.shape[1]):
            value = matrix[row, column]
            ax.text(
                column,
                row,
                str(value) if value else "—",
                ha="center",
                va="center",
                fontweight="bold" if value else "normal",
                color="white" if value >= matrix.max() * 0.55 else COLORS["ink"],
            )
    colorbar = fig.colorbar(image, ax=ax, shrink=0.8)
    colorbar.set_label("# primary dataset IDs")
    ax.set_xlabel("Catalog evaluator type")
    ax.set_ylabel(f"Coarse domain taxonomy ({TAXONOMY_VERSION})")
    save_figure(fig, "03_domain_type_heatmap")


def figure_team_size(metrics: dict[str, Any]) -> None:
    items = sorted(
        metrics["tracks"].values(),
        key=lambda metric: (
            max(metric["team_values"]) if metric["team_values"] else 99,
            metric["id"],
        ),
        reverse=True,
    )
    fig, ax = plt.subplots(figsize=(13.5, 14), constrained_layout=True)
    y_positions = np.arange(len(items))
    for y, metric in zip(y_positions, items):
        values = metric["team_values"]
        color = TYPE_COLORS[metric["type"]]
        size = 38 + 34 * math.sqrt(metric["count"])
        if not values:
            continue
        if metric["team_is_range"] and len(values) >= 2:
            left, right = min(values), max(values)
            ax.hlines(y, left, right, color=color, linewidth=2.5)
            ax.scatter([left, right], [y, y], s=size * 0.42, color=color, zorder=3)
        elif len(values) >= 2:
            ax.plot(
                values,
                [y] * len(values),
                color=color,
                linewidth=1.5,
                linestyle="--",
                alpha=0.7,
            )
            ax.scatter(values, [y] * len(values), s=size * 0.42, color=color, zorder=3)
        else:
            ax.scatter(values[0], y, s=size, color=color, alpha=0.88, edgecolor="white")

    ax.set_yticks(y_positions, [metric["id"] for metric in items])
    ax.set_xlabel(
        "Catalog-configured team / agent count\n"
        "Bubble area ∝ √(session records)"
    )
    ax.set_title(
        "Team size × session count"
    )
    ax.set_xlim(1.5, 16.2)
    ax.set_xticks(range(2, 17))
    ax.grid(axis="x")
    ax.legend(
        handles=[
            Patch(color=TYPE_COLORS["test_based"], label="Test-based"),
            Patch(color=TYPE_COLORS["rubric_based"], label="Rubric-based"),
            Line2D([0], [0], marker="o", color="none", markerfacecolor="#777", markersize=7, label="Exact value"),
            Line2D([0], [0], color="#777", marker="o", markersize=5, label="Range endpoints"),
            Line2D([0], [0], color="#777", marker="o", linestyle="--", markersize=5, label="Discrete alternatives"),
        ],
        loc="upper right",
    )
    save_figure(fig, "04_teamsize_scale_scatter")


def figure_completeness(metrics: dict[str, Any]) -> None:
    columns: list[tuple[str, Callable[[dict[str, Any], list[dict[str, Any]]], str]]] = [
        ("Catalog\ngold claim", lambda metric, rows: metric["catalog_gold"]),
        (
            "Embedded\nanswer",
            lambda metric, rows: field_state(
                rows, lambda row: nested(row, "gold_label", "expected_answer")
            ),
        ),
        (
            "Rubric",
            lambda metric, rows: field_state(
                rows, lambda row: nested(row, "gold_label", "grading_rubric")
            ),
        ),
        (
            "Human\nbaseline",
            lambda metric, rows: field_state(
                rows, lambda row: nested(row, "gold_label", "human_baseline")
            ),
        ),
        ("Source\nfield", lambda metric, rows: field_state(rows, lambda row: row.get("source_file"))),
        ("Source path\nresolves", lambda metric, rows: path_state(rows, "source_file")),
        ("Year", lambda metric, rows: field_state(rows, lambda row: row.get("year"))),
        ("Eval unit", lambda metric, rows: field_state(rows, lambda row: row.get("eval_unit"))),
        ("Row team\nsize", lambda metric, rows: field_state(rows, lambda row: row.get("team_size"))),
        ("Time\nlimit", lambda metric, rows: field_state(rows, lambda row: row.get("time_limit"))),
        ("Roles", lambda metric, rows: field_state(rows, lambda row: row.get("role_specification"))),
        (
            "Interaction",
            lambda metric, rows: field_state(rows, lambda row: row.get("interaction_protocol")),
        ),
        (
            "Shared\nartifact",
            lambda metric, rows: field_state(rows, lambda row: row.get("shared_artifact")),
        ),
        (
            "Aggregation",
            lambda metric, rows: field_state(rows, lambda row: row.get("aggregation_rule")),
        ),
    ]
    state_to_value = {"missing": 0, "partial": 1, "full": 2}
    ordered = sorted(
        metrics["tracks"].values(),
        key=lambda metric: (metric["coarse_domain"], metric["id"]),
    )
    matrix = np.zeros((len(ordered), len(columns)), dtype=int)
    labels: list[list[str]] = []
    for row_index, metric in enumerate(ordered):
        row_states: list[str] = []
        for column_index, (_, evaluator) in enumerate(columns):
            state = evaluator(metric, metric["rows"])
            matrix[row_index, column_index] = state_to_value[state]
            row_states.append(state)
        labels.append(row_states)

    cmap = ListedColormap(["#d8d5d1", "#df955d", "#397d62"])
    fig, ax = plt.subplots(figsize=(16, 14), constrained_layout=True)
    ax.imshow(matrix, cmap=cmap, vmin=-0.5, vmax=2.5, aspect="auto")
    ax.set_xticks(range(len(columns)), [label for label, _ in columns])
    ax.set_yticks(range(len(ordered)), [metric["id"] for metric in ordered])
    ax.tick_params(axis="x", labelrotation=0, labelsize=8)
    for row in range(matrix.shape[0]):
        for column in range(matrix.shape[1]):
            token = {"missing": "×", "partial": "◐", "full": "●"}[labels[row][column]]
            ax.text(
                column,
                row,
                token,
                ha="center",
                va="center",
                color="white" if matrix[row, column] >= 1 else "#6b6762",
                fontsize=8.5,
            )
    ax.set_title(
        "Benchmark readiness matrix\n"
        "fields, payloads, paths, and coordination metadata"
    )
    ax.set_ylabel("Primary dataset ID")
    ax.legend(
        handles=[
            Patch(color="#397d62", label="Full"),
            Patch(color="#df955d", label="Partial"),
            Patch(color="#d8d5d1", label="Missing"),
        ],
        loc="upper left",
        bbox_to_anchor=(1.005, 1),
    )
    save_figure(fig, "05_coverage_gold")


def figure_years(metrics: dict[str, Any]) -> None:
    with_years = [
        metric for metric in metrics["tracks"].values() if metric["years"]
    ]
    without_years = [
        metric["id"] for metric in metrics["tracks"].values() if not metric["years"]
    ]
    ordered = sorted(
        with_years,
        key=lambda metric: (min(metric["years"]), max(metric["years"]), metric["id"]),
    )
    fig, ax = plt.subplots(figsize=(15, 14), constrained_layout=True)
    for y, metric in enumerate(ordered):
        years = sorted(metric["years"])
        color = COARSE_COLORS[metric["coarse_domain"]]
        if len(years) > 1:
            ax.hlines(y, years[0], years[-1], color="#bbb6b0", linewidth=1.1, zorder=1)
        ax.scatter(
            years,
            [y] * len(years),
            s=27,
            color=color,
            edgecolor="white",
            linewidth=0.45,
            zorder=2,
        )
        ax.text(
            years[-1] + 0.35,
            y,
            f"{len(years)} year{'s' if len(years) != 1 else ''} / {metric['count']} rows",
            va="center",
            fontsize=7.5,
            color=COLORS["muted"],
        )
    ax.set_yticks(range(len(ordered)), [metric["id"] for metric in ordered])
    missing_year_note = ", ".join(without_years) if without_years else "none"
    ax.set_xlabel(
        "Nominal competition/archive year\n"
        f"Dots show observed years; lines are visual guides. Zero valid years: {missing_year_note}."
    )
    ax.set_title("Exact-year archive coverage")
    ax.grid(axis="x")
    ax.set_xlim(
        min(min(metric["years"]) for metric in ordered) - 1,
        max(max(metric["years"]) for metric in ordered) + 8,
    )
    ax.legend(
        handles=[
            Patch(color=COARSE_COLORS[domain], label=domain)
            for domain in COARSE_DOMAINS
        ],
        ncol=2,
        loc="upper left",
    )
    save_figure(fig, "06_year_coverage")


def weighting_views(metrics: dict[str, Any]) -> dict[str, dict[str, float]]:
    track_values = list(metrics["tracks"].values())
    views: dict[str, dict[str, float]] = {}

    equal_ids = Counter(metric["coarse_domain"] for metric in track_values)
    views["Equal dataset IDs"] = {
        domain: equal_ids[domain] for domain in COARSE_DOMAINS
    }

    session_rows = Counter()
    capped = Counter()
    for metric in track_values:
        session_rows[metric["coarse_domain"]] += metric["count"]
        capped[metric["coarse_domain"]] += min(metric["count"], 30)
    views["Raw session rows"] = {
        domain: session_rows[domain] for domain in COARSE_DOMAINS
    }
    views["Capped at 30 / ID"] = {
        domain: capped[domain] for domain in COARSE_DOMAINS
    }

    family_domains: dict[str, str] = {}
    for metric in track_values:
        family = metric["source_family"]
        domain = metric["coarse_domain"]
        previous = family_domains.setdefault(family, domain)
        if previous != domain:
            raise AssertionError(f"Source family {family} spans coarse domains")
    family_counts = Counter(family_domains.values())
    views["Equal source families"] = {
        domain: family_counts[domain] for domain in COARSE_DOMAINS
    }
    return views


def figure_weighting(metrics: dict[str, Any]) -> None:
    views = weighting_views(metrics)
    view_order = [
        "Raw session rows",
        "Equal dataset IDs",
        "Equal source families",
        "Capped at 30 / ID",
    ]
    matrix = np.zeros((len(COARSE_DOMAINS), len(view_order)))
    for column, view in enumerate(view_order):
        values = views[view]
        total = sum(values.values())
        for row, domain in enumerate(COARSE_DOMAINS):
            matrix[row, column] = 100 * values[domain] / total

    fig, ax = plt.subplots(figsize=(12, 8.8))
    fig.subplots_adjust(left=0.20, right=0.90, top=0.90, bottom=0.18)
    image = ax.imshow(matrix, cmap="YlGnBu", aspect="auto", vmin=0, vmax=matrix.max())
    display_labels = [
        "Raw session\nrows",
        "Equal dataset\nIDs",
        "Equal source\nfamilies",
        "Capped at 30\nper ID",
    ]
    ax.set_xticks(range(len(view_order)), display_labels)
    ax.set_yticks(range(len(COARSE_DOMAINS)), COARSE_DOMAINS)
    ax.tick_params(axis="x", labelrotation=0)
    for row in range(matrix.shape[0]):
        for column in range(matrix.shape[1]):
            value = matrix[row, column]
            ax.text(
                column,
                row,
                f"{value:.1f}%",
                ha="center",
                va="center",
                fontweight="bold",
                color="white" if value >= matrix.max() * 0.58 else COLORS["ink"],
            )
    ax.set_title(
        "Domain share under four weighting rules"
    )
    ax.set_xlabel("Portfolio weighting view")
    fig.text(
        0.5,
        0.035,
        f"Primary only · {len(metrics['primary'])} dataset IDs · "
        f"{metrics['n_source_families']} source families · "
        "four ARML variants merge to one family",
        ha="center",
        fontsize=9,
        color=COLORS["muted"],
    )
    colorbar = fig.colorbar(image, ax=ax, shrink=0.78)
    colorbar.set_label("Share within weighting view")
    save_figure(fig, "07_family_radar")


def figure_task_modes(metrics: dict[str, Any]) -> None:
    id_counts = Counter(metric["task_mode"] for metric in metrics["tracks"].values())
    row_counts = Counter()
    for metric in metrics["tracks"].values():
        row_counts[metric["task_mode"]] += metric["count"]
    order = [mode for mode, _ in id_counts.most_common()]

    fig, (ax_id, ax_rows) = plt.subplots(
        1, 2, figsize=(15, 7), constrained_layout=True
    )
    y = np.arange(len(order))
    id_values = [id_counts[mode] for mode in order]
    row_values = [row_counts[mode] for mode in order]
    bars = ax_id.barh(y, id_values, color=COLORS["blue"])
    ax_id.set_yticks(y, order)
    ax_id.invert_yaxis()
    annotate_bars(ax_id, bars)
    ax_id.set_title("Equal dataset-ID view")
    ax_id.set_xlabel("# primary dataset IDs")
    ax_id.grid(axis="x")

    bars = ax_rows.barh(y, row_values, color=COLORS["orange"])
    ax_rows.set_yticks(y, order)
    ax_rows.invert_yaxis()
    annotate_bars(ax_rows, bars)
    ax_rows.set_title("Raw session-row view")
    ax_rows.set_xlabel("# primary session records")
    ax_rows.grid(axis="x")
    fig.suptitle(
        "Task-mode mix: portfolio breadth vs archive volume",
        fontsize=18,
        fontweight="bold",
    )
    save_figure(fig, "08_task_types")


def figure_storyboard(metrics: dict[str, Any]) -> None:
    fig = plt.figure(figsize=(17, 13), constrained_layout=True)
    fig.set_constrained_layout_pads(
        w_pad=7 / 72,
        h_pad=8 / 72,
        wspace=0.22,
        hspace=0.18,
    )
    grid = fig.add_gridspec(2, 3)
    fig.suptitle(
        "OlympiadMAS formal benchmark — multi-dimensional statistical portrait",
        fontsize=19,
        fontweight="bold",
    )

    ax_scale = fig.add_subplot(grid[0, 0])
    scale_values = [metrics["primary_total"], metrics["auxiliary_total"]]
    bars = ax_scale.bar(
        ["Primary\nsession records", "Auxiliary\ncorpus rows"],
        scale_values,
        color=[COLORS["blue"], COLORS["gold"]],
    )
    ax_scale.set_yscale("log")
    for bar, value in zip(bars, scale_values):
        ax_scale.text(
            bar.get_x() + bar.get_width() / 2,
            value * 1.13,
            f"{value:,}",
            ha="center",
            fontweight="bold",
        )
    ax_scale.set_title("A. Dual-layer scale (log)", fontsize=12, pad=10)
    ax_scale.set_ylabel("rows")
    ax_scale.grid(axis="y", which="both")

    ax_domain = fig.add_subplot(grid[0, 1])
    domain_counts = Counter(
        metric["coarse_domain"] for metric in metrics["tracks"].values()
    )
    domain_order = sorted(COARSE_DOMAINS, key=domain_counts.get)
    bars = ax_domain.barh(
        domain_order,
        [domain_counts[domain] for domain in domain_order],
        color=[COARSE_COLORS[domain] for domain in domain_order],
    )
    annotate_bars(ax_domain, bars)
    ax_domain.set_title("B. Primary domain breadth", fontsize=12, pad=10)
    ax_domain.set_xlabel("# dataset IDs")
    ax_domain.grid(axis="x")

    ax_type = fig.add_subplot(grid[0, 2])
    values = [
        metrics["type_counts"]["test_based"],
        metrics["type_counts"]["rubric_based"],
    ]
    bars = ax_type.bar(
        ["Test-based", "Rubric-based"],
        values,
        color=[COLORS["blue"], COLORS["orange"]],
    )
    for bar, value in zip(bars, values):
        ax_type.text(
            bar.get_x() + bar.get_width() / 2,
            value + 0.5,
            str(value),
            ha="center",
            fontweight="bold",
        )
    ax_type.set_title("C. Catalog evaluator type", fontsize=12, pad=10)
    ax_type.set_ylabel("# dataset IDs")
    ax_type.grid(axis="y")

    ax_payload = fig.add_subplot(grid[1, 0])
    payload_values = [
        100 * metrics["embedded_answer_rows"] / metrics["primary_total"],
        100 * metrics["rubric_rows"] / metrics["primary_total"],
        100 * metrics["baseline_rows"] / metrics["primary_total"],
    ]
    payload_labels = ["Embedded answer", "Rubric", "Human baseline"]
    bars = ax_payload.barh(
        payload_labels,
        payload_values,
        color=[COLORS["blue"], COLORS["green"], COLORS["purple"]],
    )
    annotate_bars(ax_payload, bars, fmt=lambda value: f"{value:.1f}%")
    ax_payload.set_xlim(0, 112)
    ax_payload.set_title("D. Primary payload coverage", fontsize=12, pad=10)
    ax_payload.set_xlabel(f"% of {metrics['primary_total']:,} primary rows")
    ax_payload.grid(axis="x")

    ax_new = fig.add_subplot(grid[1, 1])
    new_ids = ["fyziklani", "hmmt_guts", "purple_comet"]
    sessions = [metrics["tracks"][dataset_id]["count"] for dataset_id in new_ids]
    internal_questions = [
        sum(
            int(row.get("question_count") or 0)
            for row in metrics["tracks"][dataset_id]["rows"]
        )
        for dataset_id in new_ids
    ]
    bars = ax_new.barh(new_ids, sessions, color=COLORS["green"])
    for bar, session_count, question_count in zip(
        bars, sessions, internal_questions
    ):
        ax_new.text(
            session_count,
            bar.get_y() + bar.get_height() / 2,
            f"  {session_count} / {question_count:,}",
            va="center",
            fontsize=9,
        )
    ax_new.set_xlim(0, max(sessions) * 1.34)
    ax_new.set_title(
        "E. Promoted archives\nsessions / internal questions",
        fontsize=12,
        pad=10,
    )
    ax_new.set_xlabel("# session records")
    ax_new.grid(axis="x")

    ax_aux = fig.add_subplot(grid[1, 2])
    aux_items = sorted(
        (
            (entry["id"], len(metrics["auxiliary_rows"][entry["id"]]))
            for entry in metrics["auxiliary"]
        ),
        key=lambda item: item[1],
        reverse=True,
    )
    bars = ax_aux.bar(
        [item[0] for item in aux_items],
        [item[1] for item in aux_items],
        color=COLORS["gold"],
    )
    ax_aux.set_yscale("log")
    ax_aux.tick_params(axis="x", labelrotation=35, labelsize=8)
    for label in ax_aux.get_xticklabels():
        label.set_ha("right")
    ax_aux.set_title("F. Auxiliary corpora (log)", fontsize=12, pad=10)
    ax_aux.set_ylabel("# rows")
    ax_aux.grid(axis="y", which="both")

    fig.text(
        0.5,
        0.005,
        "Primary and auxiliary layers are complementary but statistically non-exchangeable.",
        ha="center",
        fontsize=9,
        color="#78736e",
        style="italic",
    )
    save_figure(fig, "09_storyboard")


def figure_domains_pie(metrics: dict[str, Any]) -> None:
    id_counts = Counter(
        metric["coarse_domain"] for metric in metrics["tracks"].values()
    )
    row_counts = Counter()
    for metric in metrics["tracks"].values():
        row_counts[metric["coarse_domain"]] += metric["count"]

    domains = [
        domain
        for domain in COARSE_DOMAINS
        if id_counts[domain] or row_counts[domain]
    ]
    colors = [COARSE_COLORS[domain] for domain in domains]
    views = [
        (
            "Equal benchmark-ID weighting",
            [id_counts[domain] for domain in domains],
            f"{len(metrics['primary'])} primary benchmark IDs",
        ),
        (
            "Raw session-row weighting",
            [row_counts[domain] for domain in domains],
            f"{metrics['primary_total']:,} primary session records",
        ),
    ]

    fig, axes = plt.subplots(1, 2, figsize=(16, 8.5), constrained_layout=True)
    for ax, (title, values, subtitle) in zip(axes, views):
        wedges, _, autotexts = ax.pie(
            values,
            colors=colors,
            startangle=90,
            counterclock=False,
            autopct=lambda percentage: f"{percentage:.1f}%",
            pctdistance=0.70,
            wedgeprops={"edgecolor": "white", "linewidth": 1.4},
            textprops={"fontsize": 9},
        )
        for autotext in autotexts:
            autotext.set_color("white")
            autotext.set_fontweight("bold")
        ax.set_title(f"{title}\n{subtitle}", pad=12)
        ax.set_aspect("equal")

    fig.suptitle(
        "Domain composition under ID and row weighting",
        fontsize=19,
        fontweight="bold",
    )
    fig.legend(
        handles=[
            Patch(color=COARSE_COLORS[domain], label=domain)
            for domain in domains
        ],
        loc="lower center",
        ncol=4,
        bbox_to_anchor=(0.5, -0.01),
    )
    save_figure(fig, "10_domains_pie")


def figure_domain_weighting_divergence(metrics: dict[str, Any]) -> None:
    track_counts = Counter(metric["domain"] for metric in metrics["tracks"].values())
    row_counts = Counter()
    for metric in metrics["tracks"].values():
        row_counts[metric["domain"]] += metric["count"]
    domains = sorted(
        track_counts,
        key=lambda domain: (row_counts[domain] / metrics["primary_total"], domain),
    )
    track_shares = [
        100 * track_counts[domain] / len(metrics["primary"]) for domain in domains
    ]
    row_shares = [
        100 * row_counts[domain] / metrics["primary_total"] for domain in domains
    ]

    fig, ax = plt.subplots(figsize=(14, 11), constrained_layout=True)
    y = np.arange(len(domains))
    for position, left, right in zip(y, track_shares, row_shares):
        ax.hlines(
            position,
            min(left, right),
            max(left, right),
            color="#bbb6b0",
            linewidth=1.7,
        )
    ax.scatter(
        track_shares,
        y,
        color=COLORS["green"],
        s=54,
        label="Equal dataset-ID share",
        zorder=3,
    )
    ax.scatter(
        row_shares,
        y,
        color=COLORS["blue"],
        s=54,
        marker="s",
        label="Raw session-row share",
        zorder=3,
    )
    ax.set_yticks(y, domains)
    ax.set_xlabel("Share of primary portfolio (%)")
    ax.set_title(
        "Detailed-domain weighting divergence\n"
        "benchmark-ID share vs session-row share"
    )
    ax.grid(axis="x")
    ax.legend(loc="lower right")
    for position, track_share, row_share in zip(y, track_shares, row_shares):
        if max(track_share, row_share) >= 8:
            ax.text(
                max(track_share, row_share) + 0.3,
                position,
                f"{track_share:.1f}% IDs / {row_share:.1f}% rows",
                va="center",
                fontsize=7.5,
                color=COLORS["muted"],
            )
    save_figure(fig, "11_domain_weighting_divergence")


def figure_benchmark_profiles(metrics: dict[str, Any]) -> None:
    domain_rank = {domain: index for index, domain in enumerate(COARSE_DOMAINS)}
    tracks = sorted(
        metrics["tracks"].values(),
        key=lambda metric: (
            domain_rank[metric["coarse_domain"]],
            -metric["count"],
            metric["id"],
        ),
    )
    y = np.arange(len(tracks))

    def team_midpoint(metric: dict[str, Any]) -> float | None:
        values = metric["team_values"]
        return float(np.mean(values)) if values else None

    panels: list[tuple[str, list[float | None], str]] = [
        (
            "Session records",
            [float(metric["count"]) for metric in tracks],
            "log",
        ),
        (
            "Team size",
            [team_midpoint(metric) for metric in tracks],
            "linear",
        ),
        (
            "Observed years",
            [float(len(metric["years"])) for metric in tracks],
            "linear",
        ),
        (
            "Expected\nanswer",
            [
                100 * metric["expected_present"] / metric["count"]
                for metric in tracks
            ],
            "percent",
        ),
        (
            "Rubric",
            [
                100 * metric["rubric_present"] / metric["count"]
                for metric in tracks
            ],
            "percent",
        ),
        (
            "Human\nbaseline",
            [
                100 * metric["baseline_present"] / metric["count"]
                for metric in tracks
            ],
            "percent",
        ),
        (
            "Catalog\ngold",
            [
                float({"missing": 0, "partial": 1, "full": 2}[metric["catalog_gold"]])
                for metric in tracks
            ],
            "gold",
        ),
    ]

    fig, axes = plt.subplots(
        1,
        len(panels),
        figsize=(19, 16),
        sharey=True,
        gridspec_kw={"width_ratios": [1.25, 1, 1, 1, 1, 1, 1.15]},
    )
    fig.subplots_adjust(
        left=0.19,
        right=0.985,
        top=0.90,
        bottom=0.15,
        wspace=0.10,
    )
    fig.suptitle(
        "Per-benchmark multidimensional profiles",
        fontsize=19,
        fontweight="bold",
    )
    fig.text(
        0.5,
        0.925,
        "One row per benchmark; marker fill = domain, marker shape = evaluator type, outline = catalog status",
        ha="center",
        color=COLORS["muted"],
        fontsize=10,
    )

    for ax, (title, values, scale) in zip(axes, panels):
        for position, metric, value in zip(y, tracks, values):
            if value is None:
                ax.scatter(
                    0,
                    position,
                    marker="x",
                    s=34,
                    color=COLORS["gray"],
                    linewidth=1.2,
                    zorder=3,
                )
                continue
            marker = "o" if metric["type"] == "test_based" else "s"
            ax.scatter(
                value,
                position,
                marker=marker,
                s=52,
                facecolor=COARSE_COLORS[metric["coarse_domain"]],
                edgecolor=STATUS_COLORS[metric["status"]],
                linewidth=1.6,
                zorder=3,
            )

        ax.set_title(title, fontsize=11, pad=10)
        ax.grid(axis="x")
        ax.grid(axis="y", linestyle="-", alpha=0.22)
        if scale == "log":
            ax.set_xscale("log")
            ax.set_xlabel("# rows")
        elif scale == "percent":
            ax.set_xlim(-5, 105)
            ax.set_xticks([0, 50, 100])
            ax.set_xlabel("% rows")
        elif scale == "gold":
            ax.set_xlim(-0.45, 2.45)
            ax.set_xticks([0, 1, 2], ["None", "Partial", "Full"])
            ax.tick_params(axis="x", labelrotation=35)
        else:
            numeric = [value for value in values if value is not None]
            upper = max(numeric) if numeric else 1
            ax.set_xlim(-0.04 * upper, upper * 1.08)
            ax.set_xlabel("midpoint" if title == "Team size" else "# exact years")

    axes[0].set_yticks(y, [metric["id"] for metric in tracks], fontsize=8)
    axes[0].invert_yaxis()
    for ax in axes[1:]:
        ax.tick_params(axis="y", labelleft=False)

    domain_handles = [
        Patch(color=COARSE_COLORS[domain], label=domain)
        for domain in COARSE_DOMAINS
    ]
    encoding_handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            linestyle="",
            markerfacecolor=COLORS["gray"],
            markeredgecolor=COLORS["ink"],
            label="Test-based",
        ),
        Line2D(
            [0],
            [0],
            marker="s",
            linestyle="",
            markerfacecolor=COLORS["gray"],
            markeredgecolor=COLORS["ink"],
            label="Rubric-based",
        ),
        Line2D(
            [0],
            [0],
            marker="x",
            linestyle="",
            color=COLORS["gray"],
            label="Missing team-size value",
        ),
    ]
    status_handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            linestyle="",
            markerfacecolor="white",
            markeredgecolor=STATUS_COLORS[status],
            markeredgewidth=1.8,
            label=label,
        )
        for status, label in (
            ("collected", "Collected"),
            ("partial", "Partial"),
            ("pipeline_working", "Pipeline working"),
        )
    ]
    first_legend = fig.legend(
        handles=domain_handles,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.065),
        ncol=4,
    )
    fig.add_artist(first_legend)
    fig.legend(
        handles=encoding_handles + status_handles,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.025),
        ncol=6,
    )
    save_figure(fig, "12_benchmark_profiles")


def figure_question_distribution(metrics: dict[str, Any]) -> None:
    question_units = metrics["question_units_by_dataset"]
    explicit_questions = metrics["question_count_by_dataset"]
    if set(question_units) != set(metrics["tracks"]):
        raise AssertionError("Question-unit coverage does not match primary catalog")

    ordered_ids = sorted(
        question_units,
        key=lambda dataset_id: question_units[dataset_id],
        reverse=True,
    )
    total_units = sum(question_units.values())
    explicit_total = sum(explicit_questions.values())
    row_level_total = total_units - explicit_total

    domain_units: Counter[str] = Counter()
    for dataset_id, count in question_units.items():
        domain_units[metrics["tracks"][dataset_id]["coarse_domain"]] += count
    ordered_domains = sorted(
        domain_units,
        key=lambda domain: domain_units[domain],
        reverse=True,
    )

    fig = plt.figure(figsize=(19, 15.5))
    fig.patch.set_facecolor(COLORS["paper"])
    grid = fig.add_gridspec(
        2,
        2,
        left=0.12,
        right=0.965,
        top=0.86,
        bottom=0.14,
        width_ratios=[1.42, 1],
        height_ratios=[1.22, 0.72],
        wspace=0.34,
        hspace=0.43,
    )
    ax_benchmarks = fig.add_subplot(grid[:, 0])
    ax_domains = fig.add_subplot(grid[0, 1])
    ax_basis = fig.add_subplot(grid[1, 1])

    fig.suptitle(
        "Current primary question distribution",
        fontsize=22,
        fontweight="bold",
        y=0.965,
    )
    fig.text(
        0.5,
        0.915,
        (
            f"{total_units:,} catalog-visible question/task units across "
            f"{len(question_units)} primary benchmark IDs"
        ),
        ha="center",
        fontsize=11.5,
        color=COLORS["muted"],
    )

    values = [question_units[dataset_id] for dataset_id in ordered_ids]
    labels = [
        (
            f"{dataset_id}  [internal count]"
            if dataset_id in explicit_questions
            else dataset_id
        )
        for dataset_id in ordered_ids
    ]
    y = np.arange(len(ordered_ids))
    bar_colors = [
        COARSE_COLORS[metrics["tracks"][dataset_id]["coarse_domain"]]
        for dataset_id in ordered_ids
    ]
    for position, value, color in zip(y, values, bar_colors):
        ax_benchmarks.hlines(
            position,
            1,
            value,
            color=color,
            linewidth=4.5,
            alpha=0.64,
            zorder=2,
        )
        ax_benchmarks.scatter(
            value,
            position,
            s=55,
            color=color,
            edgecolor="white",
            linewidth=0.8,
            zorder=3,
        )
        label = (
            f"{value:,} ({value / total_units * 100:.1f}%)"
            if value >= 50
            else f"{value:,}"
        )
        ax_benchmarks.text(
            value * 1.13,
            position,
            label,
            va="center",
            fontsize=8.5,
            color=COLORS["muted"],
        )
    ax_benchmarks.set_xscale("log")
    ax_benchmarks.set_xlim(0.8, max(values) * 1.9)
    ax_benchmarks.set_xticks([1, 10, 100, 1000])
    ax_benchmarks.get_xaxis().set_major_formatter(
        mpl.ticker.StrMethodFormatter("{x:,.0f}")
    )
    ax_benchmarks.set_yticks(y, labels, fontsize=8.3)
    ax_benchmarks.invert_yaxis()
    ax_benchmarks.set_xlabel("Question/task units (log scale)")
    ax_benchmarks.set_title(
        "A. Distribution across all primary benchmarks",
        fontsize=13,
        pad=12,
    )
    ax_benchmarks.grid(axis="x")
    ax_benchmarks.grid(axis="y", visible=False)

    domain_values = [domain_units[domain] for domain in ordered_domains]
    domain_y = np.arange(len(ordered_domains))
    domain_bars = ax_domains.barh(
        domain_y,
        domain_values,
        color=[COARSE_COLORS[domain] for domain in ordered_domains],
        height=0.58,
    )
    ax_domains.set_yticks(domain_y, ordered_domains)
    ax_domains.invert_yaxis()
    ax_domains.set_xlabel("Question/task units")
    ax_domains.set_title(
        "B. Distribution after coarse-domain merge",
        fontsize=13,
        pad=12,
    )
    ax_domains.grid(axis="x")
    ax_domains.grid(axis="y", visible=False)
    domain_upper = max(domain_values) * 1.35
    ax_domains.set_xlim(0, domain_upper)
    for bar, value in zip(domain_bars, domain_values):
        ax_domains.text(
            value + domain_upper * 0.018,
            bar.get_y() + bar.get_height() / 2,
            f"{value:,}  ({value / total_units * 100:.1f}%)",
            va="center",
            fontsize=9,
            color=COLORS["muted"],
        )

    basis_values = [explicit_total, row_level_total]
    basis_labels = [
        "Explicit internal question_count",
        "One unit per primary row",
    ]
    basis_colors = [COLORS["blue"], COLORS["gray"]]
    left = 0
    for value, label, color in zip(basis_values, basis_labels, basis_colors):
        ax_basis.barh(
            0,
            value,
            left=left,
            color=color,
            height=0.48,
            label=label,
        )
        ax_basis.text(
            left + value / 2,
            0,
            f"{value:,}\n{value / total_units * 100:.1f}%",
            ha="center",
            va="center",
            fontsize=9,
            color="white" if color != COLORS["gray"] else COLORS["ink"],
            fontweight="bold",
        )
        left += value
    ax_basis.set_xlim(0, total_units)
    ax_basis.set_ylim(-1.0, 0.9)
    ax_basis.set_yticks([])
    ax_basis.tick_params(axis="x", bottom=False, labelbottom=False)
    ax_basis.set_title(
        "C. Counting basis",
        fontsize=13,
        pad=12,
    )
    ax_basis.grid(False)
    ax_basis.spines["bottom"].set_visible(False)
    ax_basis.text(
        0.5,
        0.12,
        (
            f"Blue: stored internal question_count from {len(explicit_questions)} "
            f"bundled archives\nGray: one catalog row per unit for "
            f"{len(question_units) - len(explicit_questions)} other benchmarks"
        ),
        transform=ax_basis.transAxes,
        ha="center",
        fontsize=9.5,
        color=COLORS["muted"],
    )

    fig.text(
        0.5,
        0.075,
        (
            "Current primary catalog only; auxiliary corpora are excluded. "
            "This chart describes catalog-visible units and does not estimate "
            "uncataloged questions."
        ),
        ha="center",
        fontsize=10,
        color=COLORS["muted"],
    )
    save_figure(fig, "13_question_distribution")


def write_summary(metrics: dict[str, Any]) -> None:
    domain_ids = Counter(metric["coarse_domain"] for metric in metrics["tracks"].values())
    domain_rows = Counter()
    task_ids = Counter(metric["task_mode"] for metric in metrics["tracks"].values())
    task_rows = Counter()
    for metric in metrics["tracks"].values():
        domain_rows[metric["coarse_domain"]] += metric["count"]
        task_rows[metric["task_mode"]] += metric["count"]

    year_values = metrics["all_primary_years"]
    question_counts = metrics["question_count_by_dataset"]
    question_count_rows = metrics["question_count_rows_by_dataset"]
    question_units = metrics["question_units_by_dataset"]
    question_domain_counts: Counter[str] = Counter()
    for dataset_id, count in question_counts.items():
        question_domain_counts[metrics["tracks"][dataset_id]["coarse_domain"]] += count
    question_unit_domain_counts: Counter[str] = Counter()
    for dataset_id, count in question_units.items():
        question_unit_domain_counts[
            metrics["tracks"][dataset_id]["coarse_domain"]
        ] += count
    summary = {
        "schema_version": "2.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "snapshot_date": SNAPSHOT_DATE,
        "taxonomy_version": TAXONOMY_VERSION,
        "sources": {
            "primary": "data/benchmarks/index_new.json",
            "auxiliary": "data/benchmarks/index_aux.json",
            "core_subset": "data/benchmarks/index.json",
        },
        "name": "OlympiadMAS",
        "n_primary_dataset_ids": len(metrics["primary"]),
        "n_primary_source_families": metrics["n_source_families"],
        "n_auxiliary_corpora": len(metrics["auxiliary"]),
        "n_total_catalog_ids": len(metrics["primary"]) + len(metrics["auxiliary"]),
        "n_primary_session_records": metrics["primary_total"],
        "n_auxiliary_rows": metrics["auxiliary_total"],
        "catalog_evaluator_type_primary": dict(metrics["type_counts"]),
        "catalog_status_primary": dict(metrics["status_counts"]),
        "record_status_primary": dict(metrics["row_status"]),
        "catalog_gold_claim_primary": dict(metrics["catalog_gold"]),
        "primary_payload_rows": {
            "embedded_expected_answer": metrics["embedded_answer_rows"],
            "rubric": metrics["rubric_rows"],
            "human_baseline": metrics["baseline_rows"],
        },
        "coarse_domains_primary_equal_ids": dict(domain_ids),
        "coarse_domains_primary_raw_rows": dict(domain_rows),
        "task_modes_primary_equal_ids": dict(task_ids),
        "task_modes_primary_raw_rows": dict(task_rows),
        "year_min": min(year_values) if year_values else None,
        "year_max": max(year_values) if year_values else None,
        "newly_promoted_archives": {
            dataset_id: {
                "sessions": metrics["tracks"][dataset_id]["count"],
                "internal_questions": sum(
                    int(row.get("question_count") or 0)
                    for row in metrics["tracks"][dataset_id]["rows"]
                ),
            }
            for dataset_id in ("hmmt_guts", "fyziklani", "purple_comet")
        },
        "question_level_observability": {
            "explicit_question_count_dataset_ids": len(question_counts),
            "missing_question_count_dataset_ids": (
                len(metrics["primary"]) - len(question_counts)
            ),
            "explicit_question_count_session_records": sum(
                question_count_rows.values()
            ),
            "missing_question_count_session_records": (
                metrics["primary_total"] - sum(question_count_rows.values())
            ),
            "measured_internal_questions": sum(question_counts.values()),
            "measured_internal_questions_by_dataset": dict(
                sorted(
                    question_counts.items(),
                    key=lambda item: item[1],
                    reverse=True,
                )
            ),
            "measured_internal_questions_by_coarse_domain": {
                domain: question_domain_counts[domain]
                for domain in COARSE_DOMAINS
                if question_domain_counts.get(domain, 0)
            },
        },
        "primary_question_unit_distribution": {
            "counting_rule": (
                "Use positive question_count when stored; otherwise count each "
                "primary benchmark row as one question/task unit."
            ),
            "catalog_visible_question_task_units": sum(question_units.values()),
            "explicit_internal_questions": sum(question_counts.values()),
            "row_level_question_task_units": (
                sum(question_units.values()) - sum(question_counts.values())
            ),
            "by_dataset": dict(
                sorted(
                    question_units.items(),
                    key=lambda item: item[1],
                    reverse=True,
                )
            ),
            "by_coarse_domain": {
                domain: question_unit_domain_counts[domain]
                for domain in sorted(
                    question_unit_domain_counts,
                    key=lambda item: question_unit_domain_counts[item],
                    reverse=True,
                )
            },
        },
        "figures": [
            {
                "png": f"{stem}.png",
                "description": description,
            }
            for stem, description in FIGURES
        ],
        "guardrails": [
            "Primary session records and auxiliary corpus rows are separate units.",
            "The primary catalog is index_new.json (index.json core + fork promotions).",
            "Catalog gold claims are distinct from embedded expected-answer payload coverage.",
            "Temporal dots show exact nominal archive years and do not imply annual continuity.",
            "Question_count exists only for the three newly promoted archives and is not a portfolio-wide field.",
            "The primary question distribution uses positive question_count where stored; every other primary row contributes one question/task unit.",
            "Equal dataset-ID weighting is sensitive to track splitting; the source-family view merges four ARML IDs.",
        ],
    }
    (OUTPUT / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    readme_lines = [
        "# Formal benchmark visualizations",
        "",
        f"Snapshot: **{SNAPSHOT_DATE}**  ",
        f"Taxonomy: **{TAXONOMY_VERSION}**  ",
        "Primary source: `data/benchmarks/index_new.json`  ",
        "Auxiliary source: `data/benchmarks/index_aux.json`",
        "",
        (
            f"Current scope: **{len(metrics['primary'])} primary dataset IDs / "
            f"{metrics['primary_total']:,} session records**, plus "
            f"**{len(metrics['auxiliary'])} auxiliary corpora / "
            f"{metrics['auxiliary_total']:,} rows**."
        ),
        "",
        "Reproduce from the repository root:",
        "",
        "Requires Python packages `matplotlib` and `numpy`.",
        "Generated format: PNG only.",
        "",
        "```powershell",
        "python data/viz/generate.py",
        "```",
        "",
    ]
    for stem, description in FIGURES:
        readme_lines.append(
            f"- **{description}** — [PNG]({stem}.png)"
        )
    readme_lines.extend(
        [
            "",
            "## Statistical guardrails",
            "",
            "- Do not pool primary session records with auxiliary question/challenge rows.",
            "- `index_new.json` (merged `index.json` + promotions) defines the primary scope here.",
            "- Catalog evaluator type and gold claims are metadata, not quality audits.",
            "- Embedded-answer, rubric, and human-baseline coverage are measured directly from JSON rows.",
            "- Equal-ID, source-family, capped, and raw-row views answer different questions.",
            "- Exact-year dots show nominal archive presence, not continuous evaluable coverage.",
            "- The primary question distribution uses positive `question_count` values where stored; every other primary row contributes one question/task unit.",
            "",
        ]
    )
    (OUTPUT / "README.md").write_text(
        "\n".join(readme_lines),
        encoding="utf-8",
    )


def main() -> int:
    configure_style()
    metrics = build_metrics()
    figure_overview(metrics)
    figure_scale(metrics)
    figure_domain_type(metrics)
    figure_team_size(metrics)
    figure_completeness(metrics)
    figure_years(metrics)
    figure_weighting(metrics)
    figure_task_modes(metrics)
    figure_storyboard(metrics)
    figure_domains_pie(metrics)
    figure_domain_weighting_divergence(metrics)
    figure_benchmark_profiles(metrics)
    figure_question_distribution(metrics)
    write_summary(metrics)
    print(
        json.dumps(
            {
                "primary_dataset_ids": len(metrics["primary"]),
                "primary_source_families": metrics["n_source_families"],
                "primary_session_records": metrics["primary_total"],
                "auxiliary_corpora": len(metrics["auxiliary"]),
                "auxiliary_rows": metrics["auxiliary_total"],
                "figures": len(FIGURES),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
