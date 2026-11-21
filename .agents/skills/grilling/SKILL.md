---
name: grilling
description: Interview technique used by grill-requirements and spec. Relentlessly questions a plan in dependency-ordered rounds until nothing is left assumed. Use when stress-testing a plan or when another skill asks for a grilling session.
---

# Grilling

Interview the person relentlessly until you reach a shared understanding. Model the topic as a **design tree**: every decision branches into the decisions that depend on it.

## Rounds

Work the tree in **rounds**. The **frontier** is every open decision whose prerequisites are already settled, meaning the questions you can ask *now* without guessing answers you haven't heard yet.

- Ask the whole frontier in one round, **at most 5 questions**. If the frontier is larger, ask the most fundamental five first.
- Number the questions across the whole session (Q1, Q2, … continuing into later rounds) so the person can answer by number.
- Give your recommended answer for every question, with a one-line reason.
- A question whose answer depends on another question still open in this round belongs in a *later* round.
- At each question or confirmation round, STOP work. Print the complete round
  directly in chat, with each recommendation and reason beside its question.
  Then STOP the turn and wait for the user's chat reply. Do not call ask-user
  or any question/form tool to collect answers.

Format:

```
❓ **Q1 - <short title>**: <the question, with options (a)/(b)/(c) when there are real alternatives>

➡️ <recommended answer> - <why>

---

❓ **Q2 - ...**
```

After each round, recompute the frontier: settled decisions unblock new questions, and some answers make whole branches irrelevant. Say briefly which branches closed.

## Facts vs decisions

- **Facts are your job.** If a question can be answered by reading the code, the work item, the ADRs or running a command, go and find out. Never ask the person for something you could look up.
- **Decisions are theirs.** Put each one to them and wait. Don't mark a decision settled because the person didn't object.
- **Push back.** If an answer contradicts an earlier answer, an ADR or the code, say so directly before moving on.

## Keeping track

Keep a running list of settled decisions in your own working context: question, decision, and one-line reason. The skill that invoked grilling turns this into its output.

## Done

The session is done when the frontier is empty: every branch visited, nothing silently assumed. Then:

1. Summarize the settled decisions as a numbered list.
2. List anything explicitly **deferred** or **out of scope**.
3. Ask the person to confirm that this is the shared understanding. Don't write anything anywhere until they confirm.
