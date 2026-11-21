# Azure Boards conventions for agents

Read this when a skill accesses Boards. Look for contributor guidance in root
Markdown files (case-insensitive `.md` or `.markdown`) and follow relevant links
for Boards connection settings, authentication, and traceability. Report gaps
and continue independent work; use the manual fallback for unavailable Boards
operations.

The work-item types, field mapping, and HTML format below are configured for this
repository's Boards project. Before using this file in another repository, 
confirm them for its project; do not assume its fields or forms match.

## Agent authentication and connection rules

Prerequisites: `az` with the `azure-devops` extension, signed in by the developer.

- Pass `--org <BOARDS_ORG_URL>` explicitly on `az boards work-item` commands. For other Azure DevOps commands, use their documented organization option. Never rely on `az devops configure` defaults or Git-remote detection; `az login` and `az account get-access-token` do not accept `--org`.
- Use the documented connection settings. If a value is missing, ambiguous, or contains `<`, do not run dependent Boards commands; ask the developer to supply it or use the manual fallback. Do not guess an organization or project.
- Never ask for credentials, accept them in chat, or put them in a command, file, commit, or environment variable. The developer authenticates in their own terminal; agents never run login commands.
- Before the first `az` call in a session, verify access with a harmless read of the work-item title:

  ```bash
  az boards work-item show --org <BOARDS_ORG_URL> --id <work-item-id> --fields System.Title --expand none -o tsv
  ```
- On `401`, `TF400813`, "not authorized", a login-required message, or a similar authentication error, stop. Tell the developer to run `az login` in their terminal and retry the same read. If access still fails, use the [manual fallback](#manual-fallback).
- If a command requires an organization or project, supply its supported explicit option rather than falling back to defaults.

## Manual fallback

When Azure DevOps is unavailable (for example in Genie Code), or connection
settings or access are missing:

- Collect work-item ID/type/title and requirement fields/numbered ACs through an export, paste, or in-chat interview. Retain a supplied work-item URL or construct it from known connection settings; otherwise report the URL as unavailable rather than guessing. Keep PO approval and readiness gates.
- Return field-labelled, copyable updates/comments for manual pasting. Before requirements handoff, require developer confirmation that concurrent edits were checked and updates saved correctly.
- Before spec confirmation or implementation, require confirmation that supplied requirements or the spec's ACs still match Boards. Boards remains authoritative; label checks as human-confirmed, not agent-verified.

These substitutions replace unavailable CLI/authentication and Boards read/write steps in the skills.

## Work item types

The skill workflow covers only these types. For a Task, Feature, Epic, Impediment, or another type, stop and tell the developer.

| `System.WorkItemType` | Label in names and commits |
|-----------------------|----------------------------|
| `Product Backlog Item` | `PBI` |
| `Bug` | `Bug` |

In the skills, "PBI" means the active work item of either type unless Bug-specific handling is stated. Follow the documented branch conventions and the [spec contract](skills/spec/SKILL.md#default-spec-contract), including repository-specific overrides; do not infer them from this table.

## Fields

Topic-to-field mapping for the requirements structure in `/grill-requirements`.
Each type has exactly these fields available. Do not use or invent others.

| Topic | Product Backlog Item | Bug | Owner | Written by |
|---------|----------------------|-----|-------|------------|
| Title | `System.Title` | `System.Title` | PO | nobody (read only for skills) |
| Problem, out of scope, open questions, background (PBI) | `System.Description` | not applicable | PO | `/grill-requirements` only |
| Steps to reproduce, expected, actual, impact, out of scope, open questions, background (Bug) | not applicable | `Microsoft.VSTS.TCM.ReproSteps` | PO | `/grill-requirements` only |
| Environment, version/build, client, data conditions | none | `Microsoft.VSTS.TCM.SystemInfo` | PO | `/grill-requirements` only |
| Acceptance criteria | `Microsoft.VSTS.Common.AcceptanceCriteria` | `Microsoft.VSTS.Common.AcceptanceCriteria` | PO | `/grill-requirements` only |
| Audit trail | Discussion (`--discussion`) | Discussion (`--discussion`) | anyone | any skill, for summaries and handoffs |
| Tags | `System.Tags` | `System.Tags` | PO | Skills never change tags. |

Never write `System.Description` on a Bug: it is not on the Bug form, so nobody would see it.

## Reading a PBI or Bug

Read in two steps because the fields depend on the type.

1. Type, title, state, and tags (this can also serve as the authentication check):

   ```bash
   az boards work-item show --org <BOARDS_ORG_URL> --id 1234 \
     --fields System.Title,System.WorkItemType,System.State,System.Tags \
     --expand none -o json
   ```

2. The requirement fields for that type:

   ```bash
   # Product Backlog Item
   az boards work-item show --org <BOARDS_ORG_URL> --id 1234 \
     --fields System.Description,Microsoft.VSTS.Common.AcceptanceCriteria \
     --expand none -o json

   # Bug
   az boards work-item show --org <BOARDS_ORG_URL> --id 1234 \
     --fields Microsoft.VSTS.TCM.ReproSteps,Microsoft.VSTS.TCM.SystemInfo,Microsoft.VSTS.Common.AcceptanceCriteria \
     --expand none -o json
   ```

Empty fields are omitted from the response; treat missing fields as empty. Always pass `--expand none` with `--fields`: the default `--expand all` is incompatible with `--fields`. For links or relations, use `--expand relations` without `--fields`.

Fields return HTML. Convert it to plain text or Markdown when reasoning; do not echo raw HTML to the person. Discussion comments are not included in `work-item show`; ask the developer to paste relevant comments when needed, and do not rely on them for anything essential.

## Writing the requirement fields

Only `/grill-requirements` writes requirement fields. Large text fields store HTML:

Group the confirmed topics into the fields above. Render acceptance criteria as
an HTML ordered list retaining stable `AC1:`, `AC2:` labels; preserve strikethrough
and retirement notes for existing ACs.

1. Convert Markdown to simple HTML: `<h3>`, `<p>`, `<ul>`, `<ol>`, `<li>`, `<strong>`, `<code>`, `<s>`, `<br>`.
2. Use no attributes or double quotes in the HTML. Use `&quot;` for literal quotes to avoid argument-parsing problems, especially in PowerShell.
3. Write HTML to a temporary file outside the repository before passing it in; never inline long content in the command.
4. Show the content to the person and obtain approval before writing to the shared work item.
5. Re-read immediately before writing. The CLI does not check revisions; if content changed, show the differences and agree a merge before proceeding.

Bash:

```bash
tmp="$(mktemp)"; cat > "$tmp" <<'EOF'
<h3>Problem</h3><p>...</p>
EOF
az boards work-item update --org <BOARDS_ORG_URL> --id 1234 --fields "System.Description=$(cat "$tmp")" -o none
```

PowerShell:

```powershell
$tmp = New-TemporaryFile
@'
<h3>Problem</h3><p>...</p>
'@ | Set-Content $tmp -Encoding utf8
$html = Get-Content $tmp -Raw
az boards work-item update --org <BOARDS_ORG_URL> --id 1234 --fields "System.Description=$html" -o none
```

Pass multiple `"Field=value"` arguments after `--fields` to update several fields. For Bugs, use Repro Steps and System Info from the [field mapping](#fields), not Description.

After writing, read the fields back and confirm they are not empty or truncated. If the organization switches these fields to Markdown mode, test on a scratch work item and update this convention if HTML renders as raw text.

## Tags

Skills never add, remove, or alter `System.Tags`. Existing tags are team-managed metadata, not prerequisites for the agent workflow. Check requirements using the documented readiness criteria.

## Discussion comments (audit trail)

Use short Discussion comments for confirmed requirement summaries, spec locations, and PR handoffs. Include the spec path without requiring a branch name:

```bash
az boards work-item update --org <BOARDS_ORG_URL> --id 1234 --discussion "<p>Technical spec: <code>path/to/spec.md</code>.</p>" -o none
```

Apply the same [HTML and safe-write rules](#writing-the-requirement-fields). Once the developer supplies the PR URL, add `Draft PR for this PBI: <PR URL>` as a Discussion comment, following the documented traceability rules.
