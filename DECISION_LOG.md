# Decision Log

The premise of this PoC: project monitoring exists to catch risk before it materializes.

This log records how the decisions were reached. `DESIGN.md` is the current design, not final. Validation findings are recorded here first, as they come, even if fragmentary.

| # | Date | Situation | Decision | Reason |
|---|---|---|---|---|
| 1 | 10/10 | | Tested a minimal prototype (one project's data). | To see how it works in the smallest form. |
| 2 | 10/13 | There was no basis anywhere for taking or not taking data. | Every data source not read must have a recorded reason. | Without a basis, it cannot be treated as a judgment. |
| 3 | 10/13 | Show the data catalog first, or have the agent state its needs first? | Needs first, accepting the risk of missing something. | It fits purpose limitation: take it if needed, otherwise don't. |
| 4 | 10/13 | Mid-design, the approach drifted toward investigating delays after they surface. | Fixed early detection as a premise. | Reconfirmed the main purpose of monitoring (acting before risk materializes) and fixed it as a premise. |
| 5 | 10/13 | Staffing data was being treated as off-limits. | Needed, but seen as structure (roles, absence periods, cover), not as people. | What to take, and how far, is a hard question. Staffing affects quality, budget and schedule, so it is taken. The scope is fixed for now as Invariant 5, but open to review (any change will be recorded in an ADR). |
| 6 | 10/14 | Data generated before the design was sufficient packed every problem into one project, in a form that could not happen in reality. | Rejected. | It could not happen in reality. |
| 7 | 10/14 | The prototype was a fixed sequence of steps. | Make it an agent. | So that the AI itself judges what to verify and what not to take. With a fixed sequence, as in the prototype, the judgment belongs not to the AI but to whoever set the sequence. |
| 8 | 10/17 | | Reduce the projects from 20 to 10. Vary the delays so that no two cases are alike. All data is synthetic. | 10, because 20 was judged too many and 5 too few. |
| 9 | 10/19 | | Wrote the design document based on the issues the prototype revealed. | |
| 10 | 10/21 | How to handle health information? | Keep no reasons for absence, only the period and the cover. | What matters is the effect on the project, not the person's circumstances. Fixed for now as Invariant 5, but open to review (any change will be recorded in an ADR). |
| 11 | 10/22 | | Use EU principles not as a legal duty, but as the direction the world is moving. | They may affect real projects, so they were set as a premise. |
| 12 | 10/22 | If only one person holds a role, the role is that person. | Open. | With one person, an absent role identifies the individual. How to handle that is not yet decided, so it is on hold. |
| 13 | 10/25 | | Tested a second prototype built on the design document. | To check that it works as designed. |
| 14 | 10/27 | The data gave the answer away (P07 showed a 14-day slip). | Fixed it. Added scoring and a three-stage evaluation plan. | If the signal is obvious, the test means nothing. |
| 15 | 11/01 | First evaluation (10 runs). Correct verdict 1/10; correct with evidence 0/10. The staffing data was never read. | Kept the result as is. | To compare what improves after changes. |
| 16 | 11/03 | The 10/24 decision to build one project first was missing from this log. | Recorded it: build only P07 first, and the other nine later. | To check that the design works before building all ten. |
| 17 | 11/05 | In Evaluation 1, no declared need mentioned staffing in any of the 10 runs. The status report only claims progress and schedule. | Open. | Cannot tell whether it comes from the P07 data or from how the agent works. |
| 18 | 11/05 | In 7 of the 10 runs, the agent stated that staffing was not checked, yet concluded `healthy`. | Open. | Cause unknown. |
| 19 | 11/12 | Cannot tell whether staffing goes unread because of the P07 data or because of how the agent works (17, 18). | Build three verification projects. Each reports no problems, with one hidden in staffing (same structure as P07), the WBS, or the risk register. P07 is not changed. | To check whether the agent finds hidden problems, and why it does not read the data. |
| 20 | 11/16 | | Built verification data: P11 (staffing), P12 (WBS), P13 (risk register). | |
| 21 | 11/18 | 10 runs, correct: P11 0/10, P12 9/10, P13 8/10. Staffing was never read. | (1) Changed the prompt. (2) Reduced runs to 5. | (1) The review covered only issues in the report. (2) Five runs are enough to see the response, at lower cost. |
| 22 | 11/18 | 5 runs, correct: P11 1/5, P12 5/5, P13 5/5. | Make the P12 and P13 data harder. | Their problems were too plain to see. |
