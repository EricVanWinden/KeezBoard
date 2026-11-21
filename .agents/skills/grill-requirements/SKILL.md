---
name: grill-requirements
description: Interview the Product Owner about an Azure Boards PBI or Bug, resolve problem/reproduction, acceptance criteria and scope, then write confirmed requirements back. No implementation design. Use e.g. /grill-requirements 1234.
argument-hint: <PBI or Bug id>
---

# Grill requirements

The PO owns product decisions; a developer facilitates. A Bug reporter may join
or stand in. Leave technical design and root-cause investigation to `/spec`.

## 1. Load and restate

- Look for contributor guidance in root Markdown files (case-insensitive `.md`
  or `.markdown`) and follow links for requirements/readiness rules.
- Report documentation gaps and assumptions; continue best effort using this
  skill's requirements structure and AC rules. Do not invent policy.
- Follow [Azure Boards conventions](../../azure-boards.md), including the manual
  fallback when access is unavailable. The developer handles Git and PR operations;
  never call `az repos` or change work-item state.

Ask for the work-item ID if absent. Read the type and requirements using the
Boards guide and report the type; stop unless PBI/Bug. Ask whether existing content
is a revision and amend rather than restart. Restate in 3-5 sentences, flag gaps
against the structure below, and let the PO correct it.

## 2. Interview

Use [grilling](../grilling/SKILL.md) to fill the structure below. For PBIs, also
probe roles, entry points, data states, missing/invalid data, permissions,
concurrency, empty/large cases, and how the PO/tester verifies outcomes.
For Bugs, include unaffected environments and nearby behavior; suggest a PBI
if this is a change request.

Resolve vague criteria/scope into PO-confirmed observable outcomes; unchosen
meanings and delegated product decisions remain open questions. Park technical
questions for `/spec`. Seek explicit exclusions and one reviewable PR; propose
independently valuable splits for the PO to decide.

## 3. Confirm and write

With no open questions, show complete Markdown requirements and get PO confirmation.
Immediately before writing, re-read fields; show concurrent changes and agree a
merge. Preserve wanted context under *Background*. Use the Boards guide's
topic-to-field mapping and safe-write rules; never guess fields or duplicate topics.

Post a Discussion summary: PO, date, AC count, open-question count. Read back and
verify stored content; empty/truncated/failed writes are not success. Hand off to
`/spec <id>` only after confirmation and successful read-back with no open questions;
otherwise name blockers and owners. Never change tags.

## Requirements structure

Use these headings; platform field names/serialization belong in the Boards guide.

### Product Backlog Item

- **Problem:** who has the problem, current behavior, and why it matters now;
  2-5 sentences.
- **Out of scope:** at least one explicitly excluded outcome.
- **Open questions:** unanswered product questions with their owners; empty
  before handoff.
- **Background:** preserve relevant existing links, context, and attachments;
  omit if none.
- **Acceptance criteria:** observable behaviors in precondition/action/result form.

### Bug

- **Steps to reproduce:** numbered, exact steps from a known user/role and data state.
- **Expected:** what should happen, confirmed by the PO.
- **Actual:** what happens instead, including error messages verbatim.
- **Impact:** who is affected, frequency, severity, workaround, and onset.
- **Out of scope:** related problems deliberately excluded; at least one item or "None".
- **Open questions:** unanswered questions with their owners; empty before handoff.
- **Background:** preserve the original report, screenshots, links, or other
  relevant existing context; omit if none.
- **Environment:** production/acceptance/test, version/build, client details
  (browser, OS, device, app version as relevant), and data conditions.
- **Acceptance criteria:** AC1 states that the repro now gives the expected,
  observable result; include at least one guard AC for nearby behavior to preserve.

### Acceptance-criteria rules

Each AC is independently checkable user/caller behavior, not implementation.
Use concrete outcomes, not "perform well" or "be secure". Keep stable `AC1:`,
`AC2:` labels; never renumber. Retire ACs with strikethrough and a note so spec/PR
references remain valid.
