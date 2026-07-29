"""Download the competition data folders (art/ and olympiad/) from Hugging Face.

The raw data files are NOT stored in this git repo (some exceed GitHub's 100 MB
limit). They live in the private HF dataset repo `akaaafk/multiagent_bench`.

Team-focused local mirrors also live under the workspace `benchmark/` folder
(24 multi-agent / team contests; solo Origin=1 packs were removed).

Usage:
    pip install -U huggingface_hub
    hf auth login          # or: set HF_TOKEN env var (repo is private)
    python download_data.py [--only art|olympiad]
"""


import argparse
from pathlib import Path

from huggingface_hub import snapshot_download

REPO_ID = "akaaafk/multiagent_bench"
REPO_ROOT = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--only",
        choices=["art", "olympiad"],
        help="download just one folder instead of both",
    )
    args = parser.parse_args()

    patterns = [f"{args.only}/*"] if args.only else ["art/*", "olympiad/*"]

    snapshot_download(
        repo_id=REPO_ID,
        repo_type="dataset",
        local_dir=REPO_ROOT,
        allow_patterns=patterns,
        max_workers=8,
    )
    print(f"Done. Data downloaded into: {REPO_ROOT}")


if __name__ == "__main__":
    main()
