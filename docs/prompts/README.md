# VARUNA prompt sequence

This folder is Adeey's implementation playbook. It turns the architecture charter into bounded, reviewable Antigravity/Claude tasks without repeating safety rules in every prompt.

## How to use it

1. Work through `steps/` in numeric order unless Jay explicitly changes a dependency.
2. Confirm the prior step is `done`, reviewed, and committed before starting the next one.
3. Open the required step file and replace the `Current task` placeholder with one small, concrete request.
4. Start a fresh task in Antigravity or Claude and paste the whole step file, including its `Reads` list and the shared-rules reference.
5. Review the diff, run the verification commands, request review where a shared contract changes, then update the step status.
6. Commit only the completed step's relevant files. Do not combine several steps in one commit.

## Model allocation

- **Gemini 3.1 Pro / Claude:** architecture, schema/contract design, safety review, RAG evidence policy, code review.
- **Gemini 3.6 or 3.8 Flash:** bounded implementation, UI components, fixtures, tests, small debugging tasks.
- **Always:** use a stronger review pass for changes that affect verdict wording, evidence/citation linking, GeoJSON, or API contracts.

## Git rhythm

```text
git status
git add <only the files for this completed step>
git commit -m "feat(frontend): <small completed feature>"
git push
```

Use `docs:` for prompt/documentation-only work and `test:` for test-only changes. Open a PR when a change affects Jay's API/planner boundary or another teammate's contract.

## Progress tracker

| Step | Title | Status |
|---|---|---|
| 01 | Analyze Stitch references | not started |
| 02 | Approve frontend architecture plan | not started |
| 03 | Build frontend shell | not started |
| 04 | Define typed response contract | blocked on Jay's approval |
| 05 | Create validated mock fixtures | not started |
| 06 | Build verdict and action UI | not started |
| 07 | Build evidence and citation panel | not started |
| 08 | Build Leaflet map | not started |
| 09 | Integrate Planner API | blocked on Jay's endpoint specification |
| 10 | Integrate cited RAG answers | blocked on Prapti's retrieval metadata |
| 11 | Run safety and accessibility review | not started |
| 12 | Rehearse the demo | not started |

## References

- [Architecture charter](../ADEEY_ARCHITECTURE_ENGINEER.md)
- [Shared role and safety rules](_shared/role-and-safety-rules.md)
- [Project README](../../README.md)
- [Claude project context](../../CLAUDE.md)

