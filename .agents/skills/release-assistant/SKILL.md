---
name: release-assistant
description: "Prepare a supplied release version: update version/changelog, draft end-user release notes, and check readiness against the release checklist."
disable-model-invocation: true
argument-hint: "Provide the release version number, e.g. 3.6.0"
---

# Release assistant

Require a user-supplied release version. Prepare files/readiness only;
deployment, PR, and stakeholder actions remain manual.

## 1. Audit before editing

Read the current unreleased changelog and
[release checklist](../../../docs/guides/release.md#5-release-policy--checklist).
Check user-facing/internal changes, affected docs, stale removed/deprecated
features, three-file version consistency, and checklist status.

Read only supplied work-item IDs using [Boards conventions](../../azure-boards.md)
and manual fallback; never guess corrected IDs. Use descriptions/ACs for problem
and user outcome. If empty/unreadable, preserve existing/supplied wording; do not infer
scope from titles, code, or docs. Report unavailable access and include supplied
extra changes without invention. Inspect PR diff/source only for a named PR or
requested implementation evaluation; report material defects separately, not as
a broad review of a wording task.

Verify affected README, CONTRIBUTING, model docs, and operational notes yourself.
Report searches, stale references fixed/found or confirmed clean, gaps, and blockers.

Apply/report obvious low-risk consistency fixes locally only in README,
CONTRIBUTING, CHANGELOG, RELEASE_NOTES, pyproject, or deployment, contribution-workflow,
release, Power BI, and operations guides in `docs/guides/`. Report other gaps;
no unrelated edits without explicit permission.

## 2. Prepare release files

- **pyproject.toml:** change only `version = "X.Y.Z"`.
- **CHANGELOG.MD:** change the current `### [UNRELEASED - Sprint YYYY-number]`
  header to `### [vX.Y.Z - Sprint YYYY-number]`. Preserve entries and older sections.
- **RELEASE_NOTES.MD:** prepend the same version/sprint header and new notes;
  preserve existing release sections and unsupported wording as required above.

Follow the [release-note policy](../../../docs/guides/release.md#release-notes).

## 3. Report readiness

Check resulting version labels agree. Report actual checklist status, remaining
manual actions, documentation verification, blockers, and fixes; never mark
unperformed steps complete.

Return exactly four labeled blocks:

**pyproject.toml**
- Version-only update.

**CHANGELOG.MD**
- Finalized unreleased header.

**RELEASE_NOTES.MD**
- New top section, starting with `### [vX.Y.Z - Sprint YYYY-number]`.

**Release readiness**
- Checklist status, remaining actions, verification, blockers, and fixes.

Note documentation gaps under the relevant block.
