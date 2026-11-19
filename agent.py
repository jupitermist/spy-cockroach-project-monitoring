"""Project assurance agent: decides its own next step with tools, under the gate's rules."""

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from audit import AuditLog, verify
from gate import DATASETS, Gate
from policy import SYSTEM_PROMPT
from providers import MODELS, make_provider

DEFAULT_MODEL = "claude-sonnet-5-5"  # provisional (仮)
MAX_TURNS = 60

TOOLS = [
    {
        "name": "list_projects",
        "description": "List all projects with their reported status and progress.",
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "read_status_report",
        "description": "Read the project manager's latest status report for a project.",
        "input_schema": {
            "type": "object",
            "properties": {"project": {"type": "string"}},
            "required": ["project"],
            "additionalProperties": False,
        },
    },
    {
        "name": "declare_needs",
        "description": "Declare what you need to know about a project, as information rather than data sources. "
                       "Required before view_catalog. When adding needs later, give the evidence that prompted them.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project": {"type": "string"},
                "needs": {"type": "array", "items": {"type": "string"}},
                "evidence": {"type": "string", "description": "Required when adding needs after reading data."},
            },
            "required": ["project", "needs", "evidence"],
            "additionalProperties": False,
        },
    },
    {
        "name": "view_catalog",
        "description": "See which data sources exist for a project, with descriptions. Contents are not shown.",
        "input_schema": {
            "type": "object",
            "properties": {"project": {"type": "string"}},
            "required": ["project"],
            "additionalProperties": False,
        },
    },
    {
        "name": "request_access",
        "description": "Request access to one data source. Reference the declared need IDs it serves. Returns a grant ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project": {"type": "string"},
                "source": {"type": "string"},
                "need_ids": {"type": "array", "items": {"type": "string"}},
                "reason": {"type": "string"},
            },
            "required": ["project", "source", "need_ids", "reason"],
            "additionalProperties": False,
        },
    },
    {
        "name": "read_data",
        "description": "Read a data source using a grant ID. Each grant can be used once.",
        "input_schema": {
            "type": "object",
            "properties": {"grant_id": {"type": "string"}},
            "required": ["grant_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "submit_assessment",
        "description": "Submit the final assessment for one project.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project": {"type": "string"},
                "verdict": {"type": "string", "enum": ["healthy", "at_risk", "undetermined"]},
                "situation": {"type": "string"},
                "evidence": {"type": "array", "items": {"type": "string"}},
                "missing_information": {"type": "string"},
                "not_retrieved": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {"source": {"type": "string"}, "reason": {"type": "string"}},
                        "required": ["source", "reason"],
                        "additionalProperties": False,
                    },
                },
                "referral": {"type": "string", "description": "Optional referral to another function, or empty."},
            },
            "required": ["project", "verdict", "situation", "evidence", "missing_information", "not_retrieved", "referral"],
            "additionalProperties": False,
        },
    },
]
for tool in TOOLS:
    tool["strict"] = True


class Run:
    def __init__(self, dataset):
        self.data = DATASETS[dataset]["data"]
        self.projects = json.loads((self.data / "index.json").read_text(encoding="utf-8"))
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        self.dir = Path("runs") / self.run_id
        self.dir.mkdir(parents=True)
        self.audit = AuditLog(self.dir)
        self.gate = Gate(self.audit, self.data)
        self.assessments = {}

    def execute(self, name, args):
        project_ids = {p["id"] for p in self.projects}
        if "project" in args and args["project"] not in project_ids:
            raise ValueError(f"Unknown project: {args['project']}")

        if name == "list_projects":
            return json.dumps(self.projects, indent=2)
        if name == "read_status_report":
            self.audit.append("read_status_report", project=args["project"])
            text = (self.data / args["project"] / "status_report.md").read_text(encoding="utf-8")
            return f"<data source=\"status_report\">\n{text}</data>"
        if name == "declare_needs":
            return json.dumps(self.gate.declare_needs(args["project"], args["needs"], args["evidence"]))
        if name == "view_catalog":
            return json.dumps(self.gate.view_catalog(args["project"]), indent=2)
        if name == "request_access":
            grant = self.gate.request_access(args["project"], args["source"], args["need_ids"], args["reason"])
            return f"Granted: {grant}"
        if name == "read_data":
            return self.gate.read_data(args["grant_id"])
        if name == "submit_assessment":
            self.assessments[args["project"]] = args
            self.gate.close_project(args["project"])
            self.audit.append("assessment", **args)
            return "Assessment recorded."
        raise ValueError(f"Unknown tool: {name}")

    def remaining(self):
        return [p["id"] for p in self.projects if p["id"] not in self.assessments]


def run_once(model, label, dataset):
    run = Run(dataset)
    run.audit.append("run_start", mode="agent", model=model, label=label, dataset=dataset)

    provider = make_provider(model, SYSTEM_PROMPT, TOOLS)
    provider.add_user("Review every project and submit an assessment for each.")
    usage = {"input_tokens": 0, "output_tokens": 0}
    started = time.monotonic()

    for _ in range(MAX_TURNS):
        turn = provider.step()
        usage["input_tokens"] += turn.input_tokens
        usage["output_tokens"] += turn.output_tokens

        if turn.refused:
            raise RuntimeError("The model declined the request.")
        if turn.calls:
            results = []
            for call_id, name, args in turn.calls:
                try:
                    content, is_error = run.execute(name, args), False
                except (PermissionError, ValueError) as e:
                    content, is_error = str(e), True
                results.append((call_id, content, is_error))
            provider.add_results(results)
            continue

        if not run.remaining():
            break
        provider.add_user(f"These projects have no assessment yet: {', '.join(run.remaining())}")

    elapsed = round(time.monotonic() - started, 1)
    run.audit.append("run_end", assessed=list(run.assessments), interventions=run.gate.interventions,
                     gray_retrievals=run.gate.gray_retrievals)
    run.audit.close()

    price_in, price_out = MODELS[model]["price"]
    cost = (usage["input_tokens"] * price_in + usage["output_tokens"] * price_out) / 1_000_000
    summary = {"run_id": run.run_id, "label": label, "dataset": dataset, "mode": "agent", "model": model, "elapsed_seconds": elapsed,
               **usage, "estimated_cost_usd": round(cost, 4),
               "interventions": run.gate.interventions, "gray_retrievals": run.gate.gray_retrievals,
               "reads": [{"project": p, "source": s} for p, s in run.gate.reads],
               "assessments": run.assessments}
    (run.dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    for a in run.assessments.values():
        print(f"{a['project']}: {a['verdict']}  read: {sorted({s for _, s in run.gate.reads})}")
    print(f"Interventions: {run.gate.interventions}  Gray: {run.gate.gray_retrievals}  "
          f"Time: {elapsed}s  Cost: ${cost:.4f}  {verify(run.dir)[1]}  Run: {run.dir}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--label", default="dev", help="Groups runs for scoring, e.g. stage1")
    parser.add_argument("--dataset", default="main", choices=DATASETS, help="Which project set to run: main or verify")
    parser.add_argument("--model", default=DEFAULT_MODEL, choices=MODELS, help="Which model runs the agent")
    args = parser.parse_args()

    load_dotenv()
    for i in range(args.runs):
        print(f"\n--- run {i + 1}/{args.runs} ({args.label}, {args.dataset}, {args.model}) ---")
        run_once(args.model, args.label, args.dataset)


if __name__ == "__main__":
    main()
