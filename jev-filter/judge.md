# Judging a JEV queue

You judge one queue file of documents that Jev, a cheap pre-classifier, could not rule out. Your verdict decides what enters the corpus; a wrong keep poisons it, a wrong drop only shrinks it.

## Input

- `criteria.txt` in the same folder as the queue: Purpose, Owner, KEEP, DROP. It is the whole standard.
- `queue_NN.jsonl`: one document per line: `sha`, `rel` (path inside the base), `path` (the file to read), `words`, and `jev` (Jev's answers: `matches` = probability it satisfies the criteria, `own` = probability the owner wrote most of it, `kind` = Jev's best guess).

## For every line

Read the file at `path`: the whole file up to ~600 lines; for longer files the first 300 lines, a stretch from the middle and the last 100. Then decide, content first and path second:

- **Whose words are these?** A source link or `Site:/Author:/Saved` header, a named other author or signatory, journalistic third person, a first-person life story of someone else, a text arguing against the owner's politics: someone else's. A translation of someone else's text is theirs. Report-like uniform sections, method boilerplate, API parameters, "In summary": AI output. A `>` quote can be the owner's own words; read before counting it foreign.
- **Is it connected prose?** Developed paragraphs, not bullets, keywords, link lists, excerpts with one-line comments, or an outline of an unwritten text.
- **Mixed file**: decide by what is most of it, as the criteria says.
- **Jev's numbers are a second opinion**, not evidence: Jev missed casework reports and caught AI reports the first judge kept. When you overrule a confident Jev (`matches` ≥ 0.6 and you drop, or < 0.3 and you keep), say why in the reason.

## Output

Append one JSON object per queue line to `queue_NN.verdicts.jsonl` next to the queue, nothing else in the file:

```json
{"sha": "<from the queue>", "rel": "<from the queue>", "decision": "keep", "kind": "essay", "authorship": "own", "finished": "unfinished", "languages": "ru,de", "sure": true, "reason": "Own argumentative reply to a quoted comment; developed paragraphs."}
```

- `decision`: `keep` or `drop`.
- `kind`: essay, article, book_chapter, blog_post, speech, letter, draft_prose, report, outline, notes, reading_notes, clipping, translation, transcript, ai_generated, index_or_list, admin_or_form, other.
- `authorship`: own, third_party, ai, mixed.
- `finished`: finished, unfinished, unclear.
- `languages`: ISO 639-1 codes, main language first.
- `sure`: false when the file leaves the case open; the human reviews those.
- `reason`: one sentence naming the decisive evidence.

Done when the verdicts file has exactly one valid line per queue line, with the same `sha` values.
