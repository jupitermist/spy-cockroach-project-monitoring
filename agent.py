"""Project assurance agent: decides its own next step with tools, under the gate's rules."""

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

import anthropic
from dotenv import load_dotenv

from audit import AuditLog, verify
from gate import DATA, Gate
from policy import SYSTEM_PROMPT

MODEL = "claude-haiku-5-5"  # provisional (仮)
PRICE_PER_MTOK = {"input": 0.10, "output": 0.50}  # Claude Haiku 5.5, prompts up to 100K tokens
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
    def __init__(self):
        self.projects = json.loads((DATA / "index.json").read_text(encoding="utf-8"))
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        self.dir = Path("runs") / self.run_id
        self.dir.mkdir(parents=True)
        self.audit = AuditLog(self.dir)
        self.gate = Gate(self.audit)
        self.assessments = {}

    def execute(self, name, args):
        project_ids = {p["id"] for p in self.projects}
        if "project" in args and args["project"] not in project_ids:
            raise ValueError(f"Unknown project: {args['project']}")

        if name == "list_projects":
            return json.dumps(self.projects, indent=2)
        if name == "read_status_report":
            self.audit.append("read_status_report", project=args["project"])
            text = (DATA / args["project"] / "status_report.md").read_text(encoding="utf-8")
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


def run_once(client, label):
    run = Run()
    run.audit.append("run_start", mode="agent", model=MODEL, label=label)

    messages = [{"role": "user", "content": "Review every project and submit an assessment for each."}]
    usage = {"input_tokens": 0, "output_tokens": 0}
    started = time.monotonic()

    for _ in range(MAX_TURNS):
        response = client.messages.create(
            model=MODEL, max_tokens=16000, system=SYSTEM_PROMPT, tools=TOOLS, messages=messages,
        )
        usage["input_tokens"] += response.usage.input_tokens
        usage["output_tokens"] += response.usage.output_tokens
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "refusal":
            raise RuntimeError("The model declined the request.")
        if response.stop_reason == "tool_use":
            results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                try:
                    content, is_error = run.execute(block.name, block.input), False
                except (PermissionError, ValueError) as e:
                    content, is_error = str(e), True
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": content, "is_error": is_error})
            messages.append({"role": "user", "content": results})
            continue

        if not run.remaining():
            break
        messages.append({"role": "user", "content": f"These projects have no assessment yet: {', '.join(run.remaining())}"})

    elapsed = round(time.monotonic() - started, 1)
    run.audit.append("run_end", assessed=list(run.assessments), interventions=run.gate.interventions,
                     gray_retrievals=run.gate.gray_retrievals)
    run.audit.close()

    cost = (usage["input_tokens"] * PRICE_PER_MTOK["input"] + usage["output_tokens"] * PRICE_PER_MTOK["output"]) / 1_000_000
    summary = {"run_id": run.run_id, "label": label, "mode": "agent", "model": MODEL, "elapsed_seconds": elapsed,
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
    args = parser.parse_args()

    load_dotenv()
    client = anthropic.Anthropic()
    for i in range(args.runs):
        print(f"\n--- run {i + 1}/{args.runs} ({args.label}) ---")
        run_once(client, args.label)


if __name__ == "__main__":
    main()
