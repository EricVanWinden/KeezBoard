---
name: sprint-planning-mail
description: Draft the recurring English sprint-planning announcement email for Big Chemistry from a shared Azure DevOps backlog or sprint board browser page
disable-model-invocation: true
argument-hint: "Share the Azure DevOps backlog/sprint board browser page for the sprint"
---

# Sprint-planning mail

Draft the email in chat; sending it and creating/updating work items are out of scope.

## Sources and links

Require a shared Azure DevOps backlog/sprint-board page; request it if absent.
Read sprint number, goals, and items with browser tools, not Azure DevOps MCP.
Only when unavailable (e.g. Genie Code), accept an export/table with sprint
year/number, exact IDs/titles, and goals/grouping. Clarify missing/unclear data;
never invent hidden data.

Read the latest/topmost version from [RELEASE_NOTES.MD](../../../RELEASE_NOTES.MD),
not Boards; ask if undetermined.

Substitute release version and confirmed sprint year/number in these team links;
never output unresolved placeholders.

```yaml
changelog_url: "https://dev.azure.com/akzonobeldw/Foundational%20work%20AI%20and%20ML/_git/AN.AFDS.ComputationalChemistry?path=/CHANGELOG.MD&version=GBrelease/v<X.Y.Z>&_a=preview"
release_notes_url: "https://dev.azure.com/akzonobeldw/Foundational%20work%20AI%20and%20ML/_git/AN.AFDS.ComputationalChemistry?path=/RELEASE_NOTES.MD&version=GBrelease/vX.Y.Z&_a=preview"
backlog_hierarchy_url: "https://dev.azure.com.mcas.ms/akzonobelpc/AFDS/_backlogs/backlog/Molecule%20Similarity%20Modeling/Initiative"
backlog_pbi_list_url: "https://dev.azure.com.mcas.ms/akzonobelpc/AFDS/_sprints/taskboard/RD-Innovate/AFDS/RD-Innovate/<Year>/<Year>-<Sprint_nr>"
```

## Filter and group

1. Keep only `[BigChem]` PBIs/Bugs. Exclude `[REL]` or "Prepare Release for Sprint ..."
   items everywhere, including inferred goals.
2. Preserve exact IDs and functional titles; strip all leading `[TAG]` blocks.
   Do not translate titles.
3. Preserve visible global goals/grouping. If absent, infer 2-5 concrete goals
   from filtered titles and README, RELEASE_NOTES, CONTRIBUTING context; no
   unrelated themes. Preserve item order where possible. Confirm unclear grouping;
   if safe inference is impossible, use `Sprint Backlog` and explain the limitation.
4. Include global goals without IDs and matching goal-to-PBI groups. Use English
   business wording: target 3-7 words, maximum 9, preferably `Verb + theme`, not
   implementation details or generic headings. Group headings match goals or
   refine them slightly. Clarify conflicting source wording; do not silently rewrite.

## Render

Use this template verbatim, substituting values and expanding loops. Keep inline
`Changelog<...>` / `Release Notes<...>` links. One blank line separates sections;
none separates a goal heading from its items. Each global goal is a `- ` bullet;
each PBI is its own `#<id>: <title>` line.

```
Hi all,

Here is the sprint planning for sprint {{sprint_number}}.

Sprint Review
Link to the Changelog<{{changelog_url}}> and the Release Notes<{{release_notes_url}}>. We are currently on version {{version}}.

Product backlog:
Here you can find the current backlog of Big Chemistry:
Hierarchical structure: {{backlog_hierarchy_url}}
List of PBIs: {{backlog_pbi_list_url}}

Sprint Goals (global)
{{#each global_goals}}
- {{goal}}
{{/each}}

Sprint Goals & Backlog
{{#each goals}}
{{goal_title}}
{{#each pbis}}#{{id}}: {{title}}
{{/each}}
{{/each}}
```

Print the finished English draft for review without extra commentary, emoji,
or sign-off inside the mail. Report source/configuration limitations separately;
do not deliver a half-filled mail.
