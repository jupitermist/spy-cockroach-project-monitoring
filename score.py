"""Score runs against ground truth, grouped by label (ADR-009).

A project counts as detected when the verdict matches and every evidence source in the ground truth was read.
Misses are listed by run so a cause can be written after reviewing the audit log.
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", help="Score only this label")
    args = parser.parse_args()

    truth = json.loads(Path("eval/ground_truth.json").read_text(encoding="utf-8"))
    groups = defaultdict(list)
    for path in sorted(Path("runs").glob("*/summary.json")):
        summary = json.loads(path.read_text(encoding="utf-8"))
        if "reads" not in summary:  # runs from before scoring existed
            continue
        if args.label is None or summary.get("label") == args.label:
            groups[summary.get("label", "dev")].append(summary)

    for label, runs in groups.items():
        n = len(runs)
        verdict_ok = detected = 0
        misses = []
        for run in runs:
            read = {(r["project"], r["source"]) for r in run["reads"]}
            for project, expected in truth.items():
                got = run["assessments"].get(project, {}).get("verdict", "missing")
                sources_ok = all((project, s) in read for s in expected["evidence_sources"])
                verdict_ok += got == expected["verdict"]
                detected += got == expected["verdict"] and sources_ok
                if not (got == expected["verdict"] and sources_ok):
                    misses.append(f"{run['run_id']} {project}: verdict={got}, read={sorted(s for p, s in read if p == project)}")

        total = n * len(truth)
        print(f"\n== {label}: {n} runs, {total} project assessments ==")
        print(f"Verdict correct:       {verdict_ok}/{total}")
        print(f"Detected with evidence: {detected}/{total}")
        print(f"Interventions (total): {sum(r['interventions'] for r in runs)}")
        print(f"Gray retrievals:       {sum(r['gray_retrievals'] for r in runs)}")
        print(f"Avg cost:  ${sum(r['estimated_cost_usd'] for r in runs) / n:.4f}")
        print(f"Avg time:  {sum(r['elapsed_seconds'] for r in runs) / n:.1f}s")
        if misses:
            print("Misses (review the audit log and write the cause):")
            for m in misses:
                print(f"  {m}")


if __name__ == "__main__":
    main()
