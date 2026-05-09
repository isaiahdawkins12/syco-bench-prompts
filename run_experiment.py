"""Driver for the system-prompts-vs-sycophancy experiment.

Iterates over (model, system_prompt) cells, calls run_all_tests.py for each,
and records each cell's output directory in experiment_manifest.csv. Resumable:
re-running skips cells already marked completed.

See EXPERIMENT_PLAN.md for the full design.
"""
import argparse
import csv
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


MODELS = [
    "anthropic/claude-haiku-4.5",
    "x-ai/grok-3-mini-beta",
    "qwen/qwen-2.5-72b-instruct",
]

# None = no --system arg (the `none` baseline). Other entries are paths to
# system-prompt files.
PROMPTS = [
    None,
    "system-prompts/agreeable.txt",
    "system-prompts/direct.txt",
    "system-prompts/principle.txt",
    "system-prompts/role.txt",
    "system-prompts/reasoning.txt",
]

PROMPT_NAMES_KNOWN = {"agreeable", "direct", "principle", "role", "reasoning"}

RESULTS_ROOT = "experiment_results"
MANIFEST_PATH = f"{RESULTS_ROOT}/manifest.csv"
LOG_DIR = f"{RESULTS_ROOT}/logs"
CELLS_DIR = f"{RESULTS_ROOT}/cells"
EST_COST_PER_CELL = 1.10  # rough; see EXPERIMENT_PLAN §4.4
DOTENV_PATH = ".env"


def load_dotenv() -> None:
    """Read KEY=VALUE lines from .env into os.environ (no overwrite)."""
    if not os.path.exists(DOTENV_PATH):
        return
    with open(DOTENV_PATH) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if k and k not in os.environ:
                os.environ[k] = v


def cell_id(model: str, prompt: str | None) -> str:
    pname = "none" if prompt is None else Path(prompt).stem
    return f"{model.replace('/', '_')}__{pname}"


def load_manifest() -> dict:
    if not os.path.exists(MANIFEST_PATH):
        return {}
    with open(MANIFEST_PATH, newline="") as f:
        return {row["cell_id"]: row for row in csv.DictReader(f)}


def save_manifest(manifest: dict) -> None:
    fieldnames = [
        "cell_id", "model", "prompt", "output_dir",
        "status", "started_at", "ended_at",
    ]
    with open(MANIFEST_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in manifest.values():
            writer.writerow(row)


def snapshot_output_dirs() -> set[str]:
    if not os.path.exists(CELLS_DIR):
        return set()
    return set(os.listdir(CELLS_DIR))


def find_new_output_dir(before: set[str], after: set[str],
                        model: str, prompt: str | None) -> str | None:
    new_dirs = after - before
    if not new_dirs:
        return None
    model_token = model.replace("/", "_")
    candidates = [d for d in new_dirs if model_token in d]
    if prompt is None:
        # Baseline cell: dir name must NOT contain any known prompt name
        candidates = [
            d for d in candidates
            if not any(pn in d for pn in PROMPT_NAMES_KNOWN)
        ]
    else:
        pname = Path(prompt).stem
        candidates = [d for d in candidates if pname in d]
    if not candidates:
        return None
    candidates.sort()  # timestamp-prefixed names sort chronologically
    return os.path.join(CELLS_DIR, candidates[-1])


def run_cell(model: str, prompt: str | None, limit: int | None,
             log_path: str) -> bool:
    cmd = [sys.executable, "-u", "run_all_tests.py", "--model", model, "--lang", "en"]
    if prompt is not None:
        cmd += ["--system", prompt]
    if limit is not None:
        cmd += ["--limit", str(limit)]
    env = {**os.environ, "SYCO_OUTPUT_DIR": CELLS_DIR}
    with open(log_path, "w") as logf:
        proc = subprocess.run(cmd, stdout=logf, stderr=subprocess.STDOUT, env=env)
    return proc.returncode == 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Per-test item limit (use small value for smoke test).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="List cells that would run, then exit.",
    )
    parser.add_argument(
        "--retry-failed", action="store_true",
        help="Re-attempt cells previously marked failed.",
    )
    parser.add_argument(
        "--yes", action="store_true",
        help="Skip the cost-confirmation prompt.",
    )
    args = parser.parse_args()

    load_dotenv()
    os.makedirs(RESULTS_ROOT, exist_ok=True)
    os.makedirs(CELLS_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    manifest = load_manifest()
    cells = [(m, p) for m in MODELS for p in PROMPTS]
    print(f"Total cells in design: {len(cells)}")

    to_run = []
    for model, prompt in cells:
        cid = cell_id(model, prompt)
        existing = manifest.get(cid)
        if existing and existing["status"] == "completed":
            print(f"  SKIP (done):    {cid}")
            continue
        if existing and existing["status"] == "failed" and not args.retry_failed:
            print(f"  SKIP (failed; --retry-failed to retry): {cid}")
            continue
        to_run.append((model, prompt, cid))

    print(f"Cells to run: {len(to_run)}")
    if args.dry_run:
        for _, _, cid in to_run:
            print(f"  -> {cid}")
        return
    if not to_run:
        print("Nothing to do.")
        return

    if not os.getenv("OPENROUTER_API_KEY"):
        print("ERROR: OPENROUTER_API_KEY is not set. Export it and re-run.")
        sys.exit(1)

    if args.limit is None:
        est = EST_COST_PER_CELL * len(to_run)
        print(f"Estimated API spend: ~${est:.2f} (full item counts)")
    else:
        # Roughly proportional to item count; full design has ~140 items.
        scale = args.limit / 35.0  # avg per-test items in full design
        est = EST_COST_PER_CELL * len(to_run) * scale
        print(f"Estimated API spend: ~${est:.2f} (--limit {args.limit})")
    if not args.yes:
        resp = input("Proceed? [y/N] ").strip().lower()
        if resp != "y":
            print("Aborted.")
            return

    for i, (model, prompt, cid) in enumerate(to_run, 1):
        print(f"\n=== Cell {i}/{len(to_run)}: {cid} ===")
        log_path = os.path.join(LOG_DIR, f"{cid}.log")
        before = snapshot_output_dirs()
        started = datetime.now().isoformat(timespec="seconds")
        ok = run_cell(model, prompt, args.limit, log_path)
        ended = datetime.now().isoformat(timespec="seconds")
        after = snapshot_output_dirs()
        out_dir = find_new_output_dir(before, after, model, prompt)

        manifest[cid] = {
            "cell_id": cid,
            "model": model,
            "prompt": "none" if prompt is None else Path(prompt).stem,
            "output_dir": out_dir or "",
            "status": "completed" if (ok and out_dir) else "failed",
            "started_at": started,
            "ended_at": ended,
        }
        save_manifest(manifest)
        if ok and out_dir:
            print(f"  -> OK: {out_dir}")
        else:
            print(f"  -> FAILED (log: {log_path})")

    completed = sum(1 for r in manifest.values() if r["status"] == "completed")
    print(f"\nDone. Completed cells in manifest: {completed}/{len(cells)}")


if __name__ == "__main__":
    main()
