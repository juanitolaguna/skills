# JEV filter

Sorts a large pile of a person's documents by one plain-language criterion into a corpus, spending as little as possible: free rules first, then a cheap model that may only throw away, then a careful reader for everything left.

## Language

### Inputs

**Criteria**:
The one paragraph (Purpose, Owner, KEEP, DROP) that defines what belongs in the corpus; the whole standard every decision is made against.
_Avoid_: filter, query, prompt

**Owner**:
The person whose own writing the corpus collects.
_Avoid_: author, user

**Source document**:
One readable file in the scanned folder, as text, with an identity that changes only when the file changes.
_Avoid_: Doc, file, item

**Excerpt**:
The bounded sample of a source document that Jev reads instead of the whole text.
_Avoid_: snippet, preview

### Deciding

**Case**:
One source document's passage through the pipeline: the evidence each stage left and the outcome, with the stage that settled it and why.
_Avoid_: Doc, record, entry

**Jev**:
The cheap decision model that scores every source document the free rules did not settle; it may only drop, never keep.
_Avoid_: classifier, pre-filter

**Judge**:
The careful reader, Claude subagents, that reads every source document Jev let through and makes the final keep or drop.
_Avoid_: reviewer, LLM

**Queue**:
A batch of source documents waiting for the judge, sized to one subagent's reading load.
_Avoid_: batch, job

**Verdict**:
The judge's decision on one source document: keep or drop, its labels and the evidence for it.
_Avoid_: result, judgement, answer

**Override**:
A human's keep or drop for one source document, which wins over every other decision.
_Avoid_: correction, manual label

### Outputs

**Corpus**:
The kept source documents with their labels and full text, the interface for whatever analysis comes next.
_Avoid_: selection, dataset, output
