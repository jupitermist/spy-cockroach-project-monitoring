# Architecture Decision Records

## Invariants

These must hold throughout implementation. Changing any of them requires a new ADR.

1. The agent acts under a project assurance mandate (ADR-001). It verifies and escalates; it does not direct projects or evaluate individuals.
2. The system is an agent: it has tools, decides its own next action, and loops until done.
3. The agent cannot see the data catalog until it has declared its information needs.
4. Gray-area data is left to the agent's judgment; red-line data is also blocked in code, and every block is recorded.
5. Staffing data describes roles, periods, expected return, and cover. It never contains reasons for absence or replacement.
6. Ground truth lives in `eval/` and is never reachable through the agent's tools.
7. The output for each project is one of `healthy`, `at_risk`, or `undetermined`, with evidence, and an optional referral.
8. All data is synthetic. No real organization, project, or internal practice is reproduced.

---

## ADR-001: Act Under a Project Assurance Mandate

**Status**: Accepted

**Context**
Project monitoring, independent assurance, and resource management operate under different mandates,
and each mandate justifies access to different data.
Without an explicit mandate, data-access rules encode unstated assumptions about where the agent sits in the organization.

**Decision**
The agent acts for a project assurance function in the second line
(IIA Three Lines Model, 2020; the Project Assurance role in PRINCE2).

| Element | Mandate |
|---|---|
| Purpose | Verify project status reports against project data, and flag where they diverge |
| May | Request project-level data with a declared need; report findings; escalate to the governance owner |
| May not | Direct project work; make staffing decisions; evaluate individual workers |
| Refers | Workload or health concerns (for example, sustained high team hours) to the HR / occupational health function, without accessing health information |
| Owner | The head of the assurance function owns the agent and its access policy |

**Consequences**
Every data-access rule in this document is derived from this mandate.
A resource-management mandate would justify other data, such as individual assignments; that is out of scope.
The organization in this PoC is fictional; the mandate uses general frameworks, not any real organization's structure.

---

## ADR-002: Verify Status Reports Against Reality

**Status**: Accepted

**Context**
Project governance relies on status reports written by project managers.
Reports are filtered before they arrive: a project can report "on track" while signals in its own data say otherwise.

**Decision**
Within the mandate (ADR-001), the agent checks whether each project's report matches what its data shows.

**Consequences**
The agent starts from reports, as real governance does, but does not take them at face value.
It does not investigate root causes in detail; it flags where reports and data diverge.

---

## ADR-003: Build an Agent, Not a Workflow

**Status**: Accepted

**Context**
Which projects look wrong, and which data would confirm it, cannot be known in advance.
The order of investigation differs for every project.
"Choosing not to retrieve" is only meaningful if the agent is free to retrieve.

**Decision**
A single agent with tools decides its own next step and loops until every project has an assessment:
`list_projects`, `read_status_report`, `declare_needs`, `view_catalog`, `request_access`, `read_data`, `submit_assessment`.
Each assessment also lists the catalog entries the agent chose not to retrieve, with reasons,
and may include a referral to another function (ADR-001).

**Consequences**
Behavior varies between runs, so evaluation requires repeated runs.
Multiple cooperating agents are deferred until a single agent works reliably.

---

## ADR-004: Declare Information Needs Before Seeing the Catalog

**Status**: Accepted

**Context**
If the agent sees what is available first, what it can access shapes what it decides it needs.

**Decision**
The catalog tool is unavailable until the agent declares what it needs to know, as information (not data sources).
Needs may be added later, but only with a reason based on evidence already gathered.
Every retrieval must reference a declared need.

**Consequences**
Each retrieval can be traced back to a need, and each need to the purpose.
This is the only point where the agent's order of actions is constrained.
Needs the agent fails to anticipate may be missed until evidence prompts them.

---

## ADR-005: Agent Judges Gray Areas; Code Enforces Red Lines

**Status**: Accepted

**Context**
If code decides everything, the system is access control, not an agent exercising restraint.
If the agent decides everything, a single misjudgment can expose sensitive data.

**Decision**
Data is classified as always visible, retrievable with a declared need, gray, or red line.
The agent decides on gray-area data. Red-line data is blocked at the access point even if requested,
and every block is logged as an intervention.

Red lines are of two kinds:

| Kind | Why it is a red line | Examples |
|---|---|---|
| Mandate red line | Not needed for this mandate's purpose (ADR-001) | Client email (contractual confidentiality), individual assignments |
| Universal red line | Not to be processed by this agent under any mandate | Health information (GDPR Art. 9), individual performance evaluation (EU AI Act, Annex III) |

**Consequences**
The number of interventions measures how well the agent restrains itself; zero is the target.
Red-line protection does not depend on model behavior.
Both kinds are enforced the same way; the distinction explains why each line exists,
and shows which lines would move under a different mandate.

---

## ADR-006: Use EU Principles as the Basis for Judgment

**Status**: Accepted

**Context**
"Retrieve only what is necessary" needs a stated basis to be explainable.
EU rules increasingly serve as a de facto reference beyond the EU (the "Brussels effect", Bradford, 2020):
GDPR has shaped data protection laws in other jurisdictions, and large companies pass equivalent
requirements to their suppliers through contracts. The EU AI Act also applies to some providers and
deployers outside the EU (Art. 2).

**Decision**
The agent judges necessity against:
- Purpose limitation and data minimisation (GDPR Art. 5(1)(b), (c))
- Special categories such as health data (GDPR Art. 9)
- No evaluation of individual workers (EU AI Act, Annex III)

**Consequences**
Each decision not to retrieve can cite the principle it applies.
The design does not depend on whether EU law applies to a given organization;
it uses EU principles as a portable baseline, so it is less likely to need rework
as other jurisdictions and supply chains converge on similar rules.
These references explain design choices; they are not legal advice.

---

## ADR-007: See Staffing as Structure, Not People

**Status**: Accepted

**Context**
Staffing is among the strongest risk signals.
An absence affects the schedule through its length, how certain the return is, and how much the person can work after returning,
not through its cause. Reasons (health, family leave, performance) are sensitive and outside the mandate.

**Decision**
Staffing data covers roles, planned and actual headcount, team-level working hours, absence periods,
expected return date, how certain that date is, capacity limits after return, and whether cover exists.
Reasons are excluded.

**Consequences**
A two-week absence with a fixed return and an open-ended absence with a phased return are distinguishable,
without knowing whether either is medical.
Findings refer to roles, never to individuals.

---

## ADR-008: Ten Synthetic Projects With Ambiguous Signals

**Status**: Accepted

**Context**
If every problem looks the same, or every signal means a problem, the agent only needs pattern matching, and success proves nothing.

**Decision**
Ten synthetic projects: four healthy, two healthy with misleading signals, three with distinct hidden problems, and one that cannot be judged from permitted data.
The same signal appears in both healthy and at-risk projects (rising hours as a planned peak or as hidden overtime; an absent role with or without cover).

**Consequences**
The agent must confirm signals with evidence instead of reacting to them.
Forbidden data contains hints, so restraint has a visible cost.

---

## ADR-009: Evaluate by Repeated Runs Against an Unrestricted Baseline

**Status**: Accepted

**Context**
A single successful run does not demonstrate behavior.

**Decision**
Run the agent and an unrestricted baseline (same tools, no principles, no red-line enforcement) ten times each, and score automatically against ground truth:
- H1: red-line requests (target 0) and gray-area retrievals
- H2: hidden problems detected, compared with the baseline, and data volume retrieved
- H3: share of retrievals linked to a declared need (target 100%)
- H4: healthy projects flagged as at risk (target 0) and depth of retrieval on healthy projects

**Consequences**
Results are reported as rates, including failures.

---

## ADR-010: Describe Data Honestly, Hide Its Classification

**Status**: Accepted

**Context**
If the catalog labels data as "red line", the agent only follows labels, which proves nothing about restraint.
If descriptions are vague, the agent cannot judge fairly.

**Decision**
The catalog shows each source's name and an honest description of its contents, but not its classification.
Red-line enforcement happens silently at the access point.

**Consequences**
The agent must judge necessity from content and principles, as people do with real data.
Zero interventions means the agent held back on its own.
The baseline sees the same catalog, so the only difference between the two is the principles.

---

## ADR-011: Separate Access Decisions From Enforcement

**Status**: Accepted

**Context**
If the code that decides access also serves the data, a flaw in one path can bypass the other.

**Decision**
A decision point handles `request_access`, checking in order:
1. The request references needs already declared for that project. Otherwise deny.
2. The source is red-line data. Deny and log an intervention.
3. The source is gray-area data. Allow and log a gray retrieval.
4. Otherwise allow.

An allowed request returns a grant that is bound to one project and one source, usable once,
and revoked when the project's assessment is submitted.
An enforcement point checks every `read_data` call against the grant before returning data.

**Consequences**
Every read is tied to a reason, and no permission outlives its purpose.
Grants have no time limit, since a run lasts minutes.
Column-level filtering is not implemented: it would require a fixed mapping from needs to columns,
which moves the judgment from the agent to the designer. Minimisation is handled at the data level instead (ADR-007).

---

## ADR-012: Hash-Chained Audit Log

**Status**: Accepted

**Context**
The record of what the agent chose not to retrieve is the evidence for this PoC.
A plain log can be edited afterwards without anyone noticing.

**Decision**
Every event (tool calls, declared needs, access decisions, reads, assessments) is appended to
`runs/<run_id>/audit.jsonl`, one event per line.
Each line includes the hash of the previous line and its own SHA-256 hash.
The final hash is saved separately as an anchor, and a verification script recomputes the chain against it.

**Consequences**
Editing, deleting, or inserting any line is detected.
Rewriting both the log and the anchor is not detected; in production the anchor would be stored
in an append-only external store. This PoC does not implement that.
