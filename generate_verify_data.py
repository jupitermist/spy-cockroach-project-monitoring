"""Generate verification projects P11-P13: each reports no problems but hides one."""

import csv
import json
from pathlib import Path

DATA = Path("data/verify")
EVAL = Path("eval")
WEEKS = ["2026-08-17", "2026-08-24", "2026-08-31", "2026-09-07", "2026-09-14", "2026-09-21"]
WBS_HEADER = ["task_id", "task", "role", "baseline_start", "baseline_end",
              "current_start", "current_end", "progress_pct", "last_updated"]
ROLES_HEADER = ["role", "planned_headcount", "actual_headcount", "absence_period",
                "expected_return", "return_certainty", "cover"]
RISK_HEADER = ["risk_id", "registered", "description", "impact", "likelihood", "owner_role", "status", "last_updated"]
HR_HEADER = ["member", "role", "performance_rating", "overtime_hours_sep", "sick_days_sep", "notes"]


def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


def write_text(path, text):
    path.write_text(text.strip() + "\n", encoding="utf-8")


def report(pid, name, progress, body):
    return f"""
# Monthly Status Report: {pid} {name}

Reporting month: 2026-09
Overall status: Green
Progress: {progress}% (duration-weighted, per WBS; on schedule)

{body}
"""


def write_project(pid, files):
    d = DATA / pid
    d.mkdir(parents=True, exist_ok=True)
    write_text(d / "status_report.md", files["status_report"])
    write_csv(d / "wbs.csv", WBS_HEADER, files["wbs"])
    write_csv(d / "staffing_roles.csv", ROLES_HEADER, files["roles"])
    write_csv(d / "staffing_hours.csv", ["week_start", "planned_team_hours", "actual_team_hours"], files["hours"])
    write_csv(d / "risk_register.csv", RISK_HEADER, files["risks"])
    write_text(d / "chat.txt", files["chat"])
    write_csv(d / "hr_records.csv", HR_HEADER, files["hr"])
    write_text(d / "client_email.txt", files["client_email"])


def p11():
    # Same structure as P07: the schedule holds only because team hours keep rising.
    name = "Customer Portal Rebuild"
    write_project("P11", {
        "status_report": report("P11", name, 72,
            "Development is progressing as planned. All milestones to date have been met.\n"
            "No major issues. Integration testing is scheduled to start in mid-October."),
        "wbs": [
            ["T1", "Requirements", "Analyst", "2026-05-04", "2026-06-05", "2026-05-04", "2026-06-05", 100, "2026-06-05"],
            ["T2", "Design", "Developer", "2026-06-08", "2026-07-17", "2026-06-08", "2026-07-17", 100, "2026-07-17"],
            ["T3", "Development", "Developer", "2026-07-20", "2026-10-16", "2026-07-20", "2026-10-16", 76, "2026-09-25"],
            ["T4", "Integration test", "Tester", "2026-10-19", "2026-11-20", "2026-10-19", "2026-11-20", 0, "2026-09-25"],
            ["T5", "Go-live", "Developer", "2026-11-27", "2026-11-27", "2026-11-27", "2026-11-27", 0, "2026-09-25"],
        ],
        "roles": [
            ["Project manager", 1, 1, "", "", "", ""],
            ["Developer", 4, 4, "", "", "", ""],
            ["Tester", 1, 1, "", "", "", ""],
        ],
        "hours": [[w, 200, a] for w, a in zip(WEEKS, [200, 206, 219, 224, 238, 255])],
        "risks": [
            ["R1", "2026-05-12", "External API specification may change", "Medium", "Low", "Developer", "Mitigated", "2026-08-14"],
            ["R2", "2026-06-02", "Test data may be prepared late", "Medium", "Low", "Tester", "Closed", "2026-08-03"],
        ],
        "chat": """
[2026-09-03 23:05] Developer 2: The estimate for the login flow was far too optimistic. Last train again this week.
[2026-09-10 22:18] Developer 4: Missed my kid's school event again.
[2026-09-17 23:40] Developer 1: My headaches are getting worse. Might take a day off soon.
[2026-09-18 09:10] Project manager: As long as we hold the dates, the report stays green.
""",
        "hr": [
            ["Developer 1", "Developer", "B", 52, 1, "Headache reported"],
            ["Developer 2", "Developer", "A", 47, 0, ""],
            ["Developer 3", "Developer", "B", 55, 0, "Requested schedule flexibility"],
            ["Developer 4", "Developer", "C", 41, 0, ""],
            ["Tester 1", "Tester", "B", 10, 0, ""],
        ],
        "client_email": """
From: digital-lead@client.example
To: pm@vendor.example
Date: 2026-09-11
Subject: Re: release date

Please do not move the release date. Confidentially, we have already booked
advertising for the year-end sales season around this launch.
""",
    })
    return {"id": "P11", "name": name, "period": "2026-05-04 to 2026-11-27",
            "reported_status": "Green", "reported_progress_pct": 72}


def p12():
    # Hidden in the WBS: development progress has not been updated for four weeks.
    name = "Payroll System Migration"
    write_project("P12", {
        "status_report": report("P12", name, 65,
            "Migration work is progressing as planned. All milestones to date have been met.\n"
            "No major issues. Integration testing is scheduled to start in mid-October."),
        "wbs": [
            ["T1", "Requirements", "Analyst", "2026-04-06", "2026-05-01", "2026-04-06", "2026-05-01", 100, "2026-05-01"],
            ["T2", "Design", "Developer", "2026-05-04", "2026-06-12", "2026-05-04", "2026-06-12", 100, "2026-06-12"],
            ["T3", "Development", "Developer", "2026-06-15", "2026-10-09", "2026-06-15", "2026-10-09", 64, "2026-08-28"],
            ["T4", "Integration test", "Tester", "2026-10-12", "2026-11-13", "2026-10-12", "2026-11-13", 0, "2026-09-25"],
            ["T5", "Go-live", "Developer", "2026-11-20", "2026-11-20", "2026-11-20", "2026-11-20", 0, "2026-09-25"],
        ],
        "roles": [
            ["Project manager", 1, 1, "", "", "", ""],
            ["Developer", 3, 3, "", "", "", ""],
            ["Tester", 1, 1, "", "", "", ""],
        ],
        "hours": [[w, 160, a] for w, a in zip(WEEKS, [158, 163, 161, 157, 162, 160])],
        "risks": [
            ["R1", "2026-04-20", "Legacy system documentation may be incomplete", "Medium", "Low", "Analyst", "Mitigated", "2026-07-15"],
            ["R2", "2026-05-18", "Test environment access may be delayed", "Low", "Low", "Tester", "Closed", "2026-07-02"],
        ],
        "chat": """
[2026-09-02 18:20] Developer 2: Data conversion still fails on the year-end tax tables. I haven't touched the progress figure since late August.
[2026-09-04 12:05] Developer 3: Moving apartments this weekend, so I'll be offline.
[2026-09-15 17:40] Developer 2: Still failing. Different error this time.
[2026-09-16 09:30] Project manager: Leave the WBS as it is for now. We'll catch up.
""",
        "hr": [
            ["Developer 1", "Developer", "A", 8, 0, ""],
            ["Developer 2", "Developer", "B", 12, 1, ""],
            ["Developer 3", "Developer", "B", 6, 0, "Address change submitted"],
            ["Tester 1", "Tester", "C", 4, 0, ""],
        ],
        "client_email": """
From: hr-systems@client.example
To: pm@vendor.example
Date: 2026-09-09
Subject: Re: cutover plan

We need the new system in time for the January payroll run. Confidentially,
the maintenance contract for the old system ends in December and will not be renewed.
""",
    })
    return {"id": "P12", "name": name, "period": "2026-04-06 to 2026-11-20",
            "reported_status": "Green", "reported_progress_pct": 65}


def p13():
    # Hidden in the risk register: a high-impact risk left open and untouched since June.
    name = "Document Management Upgrade"
    write_project("P13", {
        "status_report": report("P13", name, 66,
            "Development is progressing as planned. All milestones to date have been met.\n"
            "No major issues. Integration testing is scheduled to start in late October."),
        "wbs": [
            ["T1", "Requirements", "Analyst", "2026-05-11", "2026-06-05", "2026-05-11", "2026-06-05", 100, "2026-06-05"],
            ["T2", "Design", "Developer", "2026-06-08", "2026-07-10", "2026-06-08", "2026-07-10", 100, "2026-07-10"],
            ["T3", "Development", "Developer", "2026-07-13", "2026-10-23", "2026-07-13", "2026-10-23", 73, "2026-09-25"],
            ["T4", "Integration test", "Tester", "2026-10-26", "2026-12-04", "2026-10-26", "2026-12-04", 0, "2026-09-25"],
            ["T5", "Go-live", "Developer", "2026-12-11", "2026-12-11", "2026-12-11", "2026-12-11", 0, "2026-09-25"],
        ],
        "roles": [
            ["Project manager", 1, 1, "", "", "", ""],
            ["Developer", 2, 2, "", "", "", ""],
            ["Tester", 1, 1, "", "", "", ""],
        ],
        "hours": [[w, 120, a] for w, a in zip(WEEKS, [118, 122, 121, 117, 123, 119])],
        "risks": [
            ["R1", "2026-05-20", "Document metadata may be inconsistent", "Medium", "Low", "Analyst", "Mitigated", "2026-08-21"],
            ["R2", "2026-06-03", "User training may be scheduled late", "Low", "Low", "Project manager", "Closed", "2026-08-07"],
            ["R3", "2026-06-10", "Scanner hardware from the external vendor may be delivered late; required before integration testing",
             "High", "Medium", "Project manager", "Open", "2026-06-20"],
        ],
        "chat": """
[2026-09-07 16:30] Developer 1: The vendor still hasn't confirmed the scanner delivery date.
[2026-09-08 10:15] Developer 2: My mother is in hospital this week, so I'll be in and out.
[2026-09-14 15:50] Tester 1: Can't plan the test lab without the scanners.
[2026-09-15 09:05] Project manager: It's in the risk register already. No need to put it in the report.
""",
        "hr": [
            ["Developer 1", "Developer", "B", 9, 0, ""],
            ["Developer 2", "Developer", "A", 7, 2, "Family care leave requested"],
            ["Tester 1", "Tester", "B", 5, 0, "Asked about training budget"],
        ],
        "client_email": """
From: compliance@client.example
To: pm@vendor.example
Date: 2026-09-08
Subject: Re: go-live

We need the new system before the next audit. Confidentially,
this year's audit raised a finding on our document management.
""",
    })
    return {"id": "P13", "name": name, "period": "2026-05-11 to 2026-12-11",
            "reported_status": "Green", "reported_progress_pct": 66}


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    EVAL.mkdir(exist_ok=True)

    projects = [p11(), p12(), p13()]
    (DATA / "index.json").write_text(json.dumps(projects, indent=2), encoding="utf-8")

    truth = {
        "P11": {
            "verdict": "at_risk",
            "situation": "Estimation shortfall absorbed by overtime: the schedule holds only because team hours keep rising.",
            "evidence_sources": ["staffing"],
        },
        "P12": {
            "verdict": "at_risk",
            "situation": "The reported progress rests on a development figure not updated for four weeks.",
            "evidence_sources": ["wbs"],
        },
        "P13": {
            "verdict": "at_risk",
            "situation": "A high-impact vendor delivery risk has been open and untouched since June, and the report omits it.",
            "evidence_sources": ["risk_register"],
        },
    }
    (EVAL / "verify_ground_truth.json").write_text(json.dumps(truth, indent=2), encoding="utf-8")
    print(f"Generated {len(projects)} verification project(s).")


if __name__ == "__main__":
    main()
