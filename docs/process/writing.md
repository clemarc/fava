# Writing standard: no AI slop

Apply this standard to specs, plans, tasks, process docs, decision records and
PR descriptions, whether written by a person or an agent.

Editing reference: Peter Yang's [No AI Slop](https://github.com/petergyang/no-ai-slop/blob/000650b156983f5159695b441477f4e63b25dc85/skills/no-ai-slop/SKILL.md).
The guidance below applies its editing patterns to Fava's SDD artifacts.

## Write what the reader needs

- Lead with the requirement, decision or action. Name the actor, trigger and
  observable result when they matter.
- Use plain words and active verbs. Replace vague claims such as "robust" or
  "seamless" with specific behavior, a measurable constraint or evidence.
- Cut stock contrasts ("It's not X. It's Y."), fake revelations, rhetorical
  questions answered immediately and dramatic fragments. State the point.
- Show consequences instead of announcing that something is important. Name
  sources for attributed claims; never invent sources, facts or measurements.
- Make the smallest useful edit. Preserve meaning and the writer's voice; keep
  technical terms consistent instead of cycling synonyms for variety.
- Remove throat-clearing, promotional language, generic background and closing
  summaries that repeat the text. A sentence should add a fact, instruction,
  rationale, requirement or useful reference.
- Scale detail to the problem. Use short paragraphs; use lists and tables for
  steps or comparisons. Avoid headings that contain only a restated heading.
  Remove decorative emphasis and punctuation; keep structure that helps readers.

## Keep one source of truth

- State a rule or requirement in its canonical document. Elsewhere, link it or
  cite its ID instead of copying whole sections. Include local context needed to
  act without reconstructing the entire project.
- Plans explain implementation choices and tests; tasks name work, files and
  dependencies. Neither needs to retell the full specification.
- Record durable decisions and their rationale. Keep review transcripts and
  repeated status updates in PR discussions; current guidance should describe
  the current process. Required append-only logs retain their history.
- Treat template examples as prompts. Remove drafting instructions and unused
  optional examples; preserve required headings, fields and machine-readable
  formats. Never invent content merely to fill a section.

## Preserve precision

Keep acceptance criteria, edge cases, failure behavior, constraints, IDs, approval
and test evidence, and explicit pending checks. Concision must preserve meaning
and testability. Do not shorten an approved contract or frozen feature history
as editorial cleanup; follow the existing approval and supersession rules.

Before review, ask:

- Does each section help the reader decide, implement or verify something?
- Can any text be removed or replaced with a reference without losing meaning?
- Are claims specific and supported, with unknowns and pending checks explicit?
- Are all required details, references and formats intact?

For example, replace "This section provides comprehensive guidance to ensure a
smooth publication process" with "Before publishing, run the checks below."

Review meaning and usefulness. Do not use AI detectors, word-count quotas or
keyword bans as approval gates.
