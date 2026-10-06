---
name: jev-filter
description: Sort a large pile of documents (a notes export, a Studies or research folder, an archive) by a plain-language criterion, cheaply, with Jev — TypeSafe's decision model on OpenRouter (`~typesafe/jev-latest`) as pre-classifier. Use when asked to gather, collect, pick out or separate texts from many files ("all my essays, not the notes"), or to build a corpus for style analysis.
---

# JEV filter

`jev_filter.py` (next to this file) reads every document under a folder and sorts it by one **criteria** string. The criteria is the whole interface: the grill exists to make it sharp, because the models decide nothing the criteria leaves open.

The pipeline runs cheapest first and settles each file as early as it can:

| Stage | Who | Settles |
|---|---|---|
| 0 local | the script, free | unreadable, under `--min-words`, exact duplicates, web clips (`> Site:` / `> Saved` header) |
| 1 jev | Jev, 12k-char excerpt | drops the least probable (criteria answer < 0.15) |
| 2 judge | Claude Code subagents, the whole file | every file Jev lets through |

**Jev** (`~typesafe/jev-latest`, TypeSafe) is a decision model, not a chat model: it takes a `state` and typed questions on `POST /api/alpha/decisions` and returns probabilities, no text. The chat endpoint refuses it. The script asks it three questions per file: does it satisfy the criteria (`noul`, the score), what kind of file is it (`choice`), and did the owner write most of it (`noul`). Input costs $0.042/M tokens, output is free: a full pass over 375 files costs about $0.05, and Jev is the only thing this skill spends OpenRouter money on. Docs: `https://openrouter.ai/docs/guides/community/jev.md`. Every run writes `OUT/jev_stats.json` and a line in the report: how long Jev took, on how many files, how many it dropped, how many tokens and words it read, latency and cost. `--fresh-jev` re-asks Jev instead of using the cache, to time it.

Jev may only throw away; a keep always needs the judge, because a wrong keep poisons the corpus and a wrong drop only shrinks it. The judge is Claude Code itself, on the user's subscription: the script writes the survivors to queue files, subagents judge them by [`judge.md`](judge.md), and the next run reads the verdicts back. Jev and a judge catch different errors: Jev caught an AI report and a saved newspaper article a chat-model judge kept; the judge read authorship Jev missed. `--trust-jev` keeps files scored ≥ `--keep-at` unread, when the judge's time matters more than purity. Jev answers are cached in `OUT/.jev_cache.jsonl` and verdicts in `OUT/judge/<criteria-hash>/`, both by file content, so a rerun only does what is new. The key has a spending limit: `curl -s https://openrouter.ai/api/v1/key -H "Authorization: Bearer $(cat .openrouter_jev)"` shows what is left.

## 1. Grill

One round, at most five questions, through `AskUserQuestion`, recommended answer first. Ask only what the request leaves open; facts about the folder (languages, layout, sizes) come from the dry run in step 3, never from the user. The branches that decide every filter of this kind:

- **Kinds**: which forms count (essay, article, chapter, blog post, speech, letter, statement) and which are out (notes, outlines, reading notes, lists, transcripts, paperwork).
- **Authorship**: own text only, or also the owner's translations of others, co-written texts, AI-drafted texts he edited. For style analysis the default is own and unassisted.
- **Unfinished**: a draft counts when what exists is developed paragraphs; an outline of an unwritten text is a plan, not a draft. Confirm where the line is.
- **Mixed files**: a daily note or research file with one real passage inside. Keep whole, drop, or keep only when the owner's prose is most of it.
- **Purity or speed**: precise (default, every keep judged) or fast (`--trust-jev`).

Done when every branch is answered by the request or the user.

## 2. Write the criteria

Compress the answers into one paragraph of at most 120 words and save it as `OUT/criteria.txt`. Shape:

```
Purpose: <what the kept set is for, e.g. "a corpus for analysing his writing style">.
Owner: <who wrote the texts we want: name, languages, politics or field: one line that lets the model spot foreign text by stance>.
KEEP: <forms>, in <languages>. Unfinished: <rule>. Mixed: <rule>.
DROP: <every excluded form, named>.
```

Each line has a job. The purpose decides the forms nobody listed: a list of forms alone ("essays, articles, letters") drops the owner's discussion replies, casework reports and critiques of other texts, though a style corpus wants every connected paragraph he wrote. The owner line lets a pro-war clipping in a left activist's base read as foreign. And every excluded form gets named, because a form the criteria never names gets judged by the model's taste.

## 3. Dry run, then calibrate

```bash
uv run --script .claude/skills/jev-filter/jev_filter.py ROOT --criteria @OUT/criteria.txt --out OUT --dry-run
uv run --script .claude/skills/jev-filter/jev_filter.py ROOT --criteria @OUT/criteria.txt --out OUT --sample 40
```

The dry run prints how many files reach Jev and what that costs. The sample run is the calibration: judge its queue yourself (it is small), rerun to read the verdicts back, then read the top of every keep and of every file Jev dropped with a score ≥ 0.1.

The Jev threshold moves with the criteria: 0.3 lost nothing under one wording and three real texts under the next. After any criteria change, sweep it. With a set of known keeps (a reviewed earlier run, or the sample read by hand), count for each threshold how many files reach the judge and how many known keeps fall below; take the highest threshold that loses none. `--sweep REVIEWED.jsonl` prints that table from the last run's verdicts without any API call.

A miss has one of three causes, each with its own fix:

- the model could not see the evidence → fix extraction in the script (this is how link domains came back into the excerpt);
- the criteria left the case open → add the case, or the purpose that settles it, to the criteria;
- the evidence is structural and certain → add a local rule (free, like the web-clip rule).

Calibration is done when one sample run comes back with no miss you can name. Changed criteria invalidate the cache, so settle them here, on 40 files, not on 600.

## 4. Full run, judge, review

```bash
uv run --script .claude/skills/jev-filter/jev_filter.py ROOT --criteria @OUT/criteria.txt --out OUT
```

The run ends with the files Jev let through split into `OUT/judge/<hash>/queue_NN.jsonl`, each about 20k words of reading. Dispatch one `general-purpose` subagent per queue file, all in one message, with no `model` parameter so each runs on the session's model. Each prompt names its queue file and says: read `.claude/skills/jev-filter/judge.md` and follow it for this queue. When they are back, rerun the same command: it reads the verdicts and writes new queues only for what is still pending (a malformed or missing line). Repeat until the run reports 0 pending.

The run writes `OUT/README.md`, which lists every output and the schema of `corpus.jsonl`: one JSON line per kept document with the judge's labels and the full text. That file is the interface for whatever comes next; `selected/` holds the same texts for reading, `report.md` is for people.

Review the report's review list: files where the judge was unsure or disagrees with Jev. Read each, decide, and write the decision into `OUT/overrides.txt`, one per line, `+ rel/path` to keep or `- rel/path` to drop. Rerun; overrides apply on top of everything at no cost. Show the user the cases that need their judgement, as a short list with one line of evidence each.

Done when the run reports 0 pending, every review case is decided, and the user has the path to `OUT`.

## 5. Hand-off

The next step works on `corpus.jsonl`, and `OUT/README.md` says how: an operation that runs over every document (counts, splits by language, sentence measures, n-grams, samples) is a script over the JSONL, deterministic and free to rerun; the model reads texts only where judgement is needed, on a sample or on what a script picked out. When you hand over to another agent or session, give it the path to `OUT/README.md`.

## Python

```python
from jev_filter import jev_filter
docs = jev_filter(criteria="...", root=Path("~/Documents/Studies"), out=Path("profile/korpus"))
```
