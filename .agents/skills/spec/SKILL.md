---
name: spec
description: Design an Azure Boards PBI or Bug with confirmed requirements. Explore the code and bug root cause, propose a technical spec, and resolve decisions. Use e.g. /spec 1234.
argument-hint: <PBI or Bug id>
disable-model-invocation: true
---

# Spec

Agree the technical design with the implementing developer; write the handoff
for `/implement` in a fresh chat.

## 1. Load and investigate

- Look for contributor guidance in root Markdown files (case-insensitive `.md`
  or `.markdown`) and follow relevant links for workflow and spec rules.
- Report documentation gaps and assumptions; continue best effort using this
  skill's defaults and existing conventions. Do not invent policy.
- Follow [Azure Boards conventions](../../azure-boards.md), including the manual
  fallback. The developer owns Git/PR operations: use Git only for read-only branch
  preflight; never create/switch branches, push, merge, call `az repos`, or change
  work-item state.
- Run `git branch --show-current`; check the work-item ID and documented branch
  rules. On failure, detached HEAD, or a wrong/invalid branch, stop and ask the developer
  to select the correct branch. Confirm sprint carry-over if applicable.
- Read the work item and check readiness. Clarify missing PO confirmation;
  unresolved requirements block design.
- Find existing specs using the contract below. Ask the developer to resolve
  duplicates or select the correct workspace if an intended spec is missing.
  Revise drafts in place, addressing only changes; never revise implemented specs.
- Read accepted ADRs and trace affected entry points, interfaces, modules, and
  tests yourself. For Bugs, investigate reproduction, root cause, confidence,
  confirmation evidence, and same-cause occurrences. Execution may confirm the
  cause; do not fix code yet.

## 2. Design and confirm

Propose the repository's spec format or the template below. Cite evidence,
mark open assumptions, and use [grilling](../grilling/SKILL.md) for unresolved
decisions, scaled to uncertainty.

Cover every template topic plus rollout and performance/security/concurrency/
failure risks. Prefer existing stable test interfaces and the highest seams that
keep tests fast and reliable; use as many as coverage needs, not a fixed count.
Apply documented validation and ADR criteria; absent policies, use existing
test/build tooling and reserve ADRs for significant long-lived decisions.

For Bugs, agree the root cause or how implementation will confirm it before fixing.
Map AC1 to regression evidence and guard ACs to nearby behavior. Prefer root fixes;
justify containment and record excluded root fixes as technical out of scope.
Agree same-cause scope; refer excluded occurrences to the PO for a new Bug.
The PO owns data-repair scope; the developer owns its design.

Return missing/ambiguous requirements to the PO; with developer agreement, post
questions in Discussion, never requirement fields. Do not write with open product
questions. Discuss independently valuable splits with the PO if one PR is infeasible.

Draft qualifying settled ADRs in the existing format; otherwise list candidates.
Show the complete spec with one-line decision reasons, no open assumptions, and
modules/interfaces/contracts rather than code or exhaustive file lists.

Re-read Boards ACs immediately before confirmation. Show changes and ask whether
the design holds; iterate until the developer confirms the complete spec.

## 3. Write and hand off

After confirmation, write/amend per the contract and post the spec path in Boards
Discussion. Never edit requirement fields, state, or tags. Report written files
and `/implement <id>`; leave Git/PR operations to the developer.

Offer an optional early design look for new interfaces, contract/data changes,
or ADR candidates/drafts, naming the triggers. If requested, draft a spec-only PR
description with the full work-item URL, solution sketch, and code to follow in
the same PR.

## Default spec contract

Documented repository rules override these defaults: `docs/specs/`,
`PBI-<id>-<slug>.md` / `BUG-<id>-<slug>.md`; search with `*-<id>-*.md`.

The implementing developer owns and explicitly approves the complete design with
no open assumptions before writing. Fresh sessions verify recorded approval or
ask the developer; draft status is not approval. Review spec and code together.
Boards owns requirements: copy ACs verbatim and map every AC to verification.

Start with `Status: Draft`. After implementation and required checks, use
`Status: Implemented <yyyy-mm-dd>. Historical, may be outdated; ADRs and code are authoritative.`
Implemented specs are frozen: new work needs a new work item and spec linking to
the historical one. Before completion, revise affected sections with dated
*Amendments*.

## Default spec template

Use when no repository-specific format is documented.

```markdown
# <PBI|Bug> <id>: <title>

Status: Draft

- Work item: <link to the work item>
- Requirements source: <Boards read, or manual snapshot with date and developer confirmation of freshness>
- Historical spec: <link to the related implemented spec, if applicable>

## Acceptance criteria
<Copied verbatim from Boards, the source of truth.>

1. AC1: ...

## Root cause (Bug only; omit for a PBI)
<What causes the wrong behavior, where in the code, since when if known, and how it was confirmed; or how implementation will confirm it before fixing.>

## Solution sketch
<3-6 sentences: the shape of the change, where it lives, what it extends.>

## Implementation decisions
1. <Decision> - <why, one line>

## Seams
| Seam | Kind | Existing or new | Notes |
|------|------|-----------------|-------|
| <interface> | <public API / module interface / HTTP endpoint / message handler> | <existing / new> | <test-relevant details> |

## AC verification mapping
| AC | Interface or document | Check (what it proves) |
|----|-----------------------|------------------------|
| AC1 | <interface or document> | <Automated, manual, or documentation check; for a code bug, before-fix regression evidence.> |

## Contracts and data
<Schema changes, migrations, API/message contract changes, backwards compatibility; or "None".>

## Risks and mitigations
- <Risk> - <mitigation>

## ADR candidates
- <Decision meeting the contributor ADR criteria to confirm during implementation; or "None".>

## Technical out of scope
- <Refactorings, cleanups, optimizations deliberately excluded.>

## Amendments
<Dated entries added during implementation when the spec changes; or "None" until then.>
- <yyyy-mm-dd>: <what changed and why>
```
