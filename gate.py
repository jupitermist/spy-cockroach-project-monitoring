"""Access decision point (PDP) and enforcement point (PEP), with purpose-bound grants (ADR-011)."""

import itertools
from pathlib import Path

from audit import sha256
from policy import CATALOG, GRAY, RED_LINES

DATA = Path("data/projects")


class Gate:
    def __init__(self, audit):
        self.audit = audit
        self.needs = {}    # project -> {need_id: description}
        self.grants = {}   # grant_id -> {"project", "source", "used", "revoked"}
        self.closed = set()
        self.need_ids = itertools.count(1)
        self.grant_ids = itertools.count(1)
        self.interventions = 0
        self.gray_retrievals = 0
        self.reads = []    # (project, source) actually read

    def declare_needs(self, project, needs, evidence=""):
        added = {}
        for description in needs:
            need_id = f"N{next(self.need_ids)}"
            added[need_id] = description
        self.needs.setdefault(project, {}).update(added)
        self.audit.append("declare_needs", project=project, needs=added, evidence=evidence)
        return added

    def view_catalog(self, project):
        if not self.needs.get(project):
            self.audit.append("catalog_refused", project=project, reason="no declared needs")
            raise PermissionError("Declare your information needs for this project before viewing its catalog.")
        self.audit.append("view_catalog", project=project)
        return {name: item["description"] for name, item in CATALOG.items()}

    def request_access(self, project, source, need_ids, reason):
        """PDP: decide in the order defined by ADR-011."""
        if project in self.closed:
            decision, detail = "deny", "assessment already submitted for this project"
        elif source not in CATALOG:
            decision, detail = "deny", "unknown source"
        elif not need_ids or not set(need_ids) <= set(self.needs.get(project, {})):
            decision, detail = "deny", "request does not reference needs declared for this project"
        elif source in RED_LINES:
            decision, detail = "intervention", RED_LINES[source]
            self.interventions += 1
        else:
            decision = "allow"
            detail = "gray area: allowed by the agent's judgment" if source in GRAY else "permitted"
            if source in GRAY:
                self.gray_retrievals += 1

        grant_id = None
        if decision == "allow":
            grant_id = f"G{next(self.grant_ids)}"
            self.grants[grant_id] = {"project": project, "source": source, "used": False, "revoked": False}
        self.audit.append("access_decision", project=project, source=source, need_ids=need_ids,
                          reason=reason, decision=decision, detail=detail, grant=grant_id)
        if decision != "allow":
            raise PermissionError(f"Access denied: {detail}")
        return grant_id

    def read_data(self, grant_id):
        """PEP: check the grant before returning any data."""
        grant = self.grants.get(grant_id)
        if grant is None or grant["used"] or grant["revoked"]:
            self.audit.append("read_refused", grant=grant_id)
            raise PermissionError("Invalid, used, or revoked grant.")
        grant["used"] = True
        parts = []
        for name in CATALOG[grant["source"]]["files"]:
            text = (DATA / grant["project"] / name).read_text(encoding="utf-8")
            parts.append(f"<data source=\"{grant['source']}\" file=\"{name}\">\n{text}</data>")
        content = "\n".join(parts)
        self.reads.append((grant["project"], grant["source"]))
        self.audit.append("read_data", grant=grant_id, project=grant["project"],
                          source=grant["source"], fingerprint=sha256(content))
        return content

    def close_project(self, project):
        self.closed.add(project)
        for grant in self.grants.values():
            if grant["project"] == project and not grant["used"]:
                grant["revoked"] = True
