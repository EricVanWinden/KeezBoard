---
name: implement
description: Implement an approved technical spec, verify acceptance criteria, and prepare a PR handoff. Use /implement <work item id or spec path>.
argument-hint: <work item id or spec path>
disable-model-invocation: true
---

# Implement

Build from the approved spec with the developer present. The spec leads technical
implementation; do not quietly redesign it.

## 1. Load

- Find workflow guidance in root Markdown files (case-insensitive `.md` or
  `.markdown`) and follow relevant links. Use it for validation, deviations,
  documentation, ADRs, and PR conventions. Report gaps and assumptions; continue
  best effort using the spec and existing conventions, without inventing policy.
- Read the unique active spec, including amendments, using the
  [spec contract](../spec/SKILL.md#default-spec-contract) and documented overrides.
  Stop if missing, ambiguous, implemented, or unapproved. Confirm approval with
  the developer if not recorded; draft status is not approval.
- Check current requirements and readiness using the
  [Boards conventions and manual fallback](../../azure-boards.md).
  Resolve open requirements or AC differences before coding. Read relevant
  accepted ADRs.
- Run `git branch --show-current`; check the work-item ID and documented branch
  rules. Stop on failure, detached HEAD, or a wrong/invalid branch; ask the
  developer to select the correct branch. Confirm sprint carry-over if applicable.
- Show a short chat-only plan covering ACs, checks, affected files, and conflicts.
  It is not another approval gate.

## 2. Build and verify

Follow the contributor workflow in AC order using the spec's verification mapping.
Without validation guidance, use the spec's checks and existing test/build tooling.
For code bugs, capture before/after regression evidence; investigate an unexpected
reproduction before fixing.

Apply documented deviation rules. If absent, get developer agreement before
changing scope, interfaces, contracts/data, or dependencies; AC changes need the
requirements owner first. Amend the spec with a dated entry after agreement.
Record internal-only deviations in the handoff. If unsure, ask rather than redesign.

## 3. Review and hand off

Complete applicable documentation and ADR updates, then set spec status per its
contract only after implementation and required checks are complete.
Review changed files without Git: check AC evidence, scope, deviations, validation,
and documentation. Fix introduced failures; report baseline failures and blocked
checks honestly. This does not replace human review.

Summarize results and provide a copyable PR title/description following repository
conventions: work-item URL, spec path, AC evidence, amendments/deviations, ADRs,
remaining checks, and reviewer focus.

## Limits

The developer owns Git and PR operations. Use Git only for read-only branch
preflight; never create/switch branches, push, merge, call `az repos`, or change
work-item state. Stop at the PR handoff; do not release or deploy to test/production.
Any development deployment must follow repository policy.
