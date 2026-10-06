"""The whole run, with Jev faked: what the judge is given and what the corpus gets.

Jev is faked by patching JevClient.decide; replace this with a Jev adapter once the Jev stage has a seam.
"""
import hashlib
import json

import jev_filter as jf
from conftest import page_markers, write_pdf

CRITERIA = "KEEP: own essays. DROP: notes."


def fake_jev(monkeypatch, matches=0.5):
    calls = []

    def decide(self, model, state, questions):
        calls.append(state["path"])
        return {"matches": matches, "own": 0.5, "kind": "own_prose", "kind_p": {}, "_cost": 0.0}

    monkeypatch.setattr(jf.JevClient, "decide", decide)
    monkeypatch.setenv("JEV_KEY", "test")
    return calls


def run(root, out):
    return jf.jev_filter(CRITERIA, root, out, log=lambda *a: None)


def queue_items(out):
    queues = sorted(q for q in out.glob("judge/*/queue_*.jsonl") if not q.name.endswith(".verdicts.jsonl"))
    return [json.loads(l) for q in queues for l in q.read_text().splitlines()]


def test_the_judge_is_given_every_page_of_a_pdf(tmp_path, monkeypatch):
    fake_jev(monkeypatch)
    root, out = tmp_path / "docs", tmp_path / "out"
    root.mkdir()
    write_pdf(root / "book.pdf", pages=12)

    run(root, out)

    [item] = queue_items(out)
    text = open(item["path"]).read()
    assert page_markers(text) == [f"PAGE{n:02d}" for n in range(1, 13)]
    assert item["words"] == len(text.split())


def test_a_judged_pdf_enters_the_corpus_whole_under_the_hash_of_its_bytes(tmp_path, monkeypatch):
    calls = fake_jev(monkeypatch)
    root, out = tmp_path / "docs", tmp_path / "out"
    root.mkdir()
    pdf = write_pdf(root / "book.pdf", pages=12)
    run(root, out)
    [item] = queue_items(out)
    [queue] = out.glob("judge/*/queue_01.jsonl")
    verdict = {"sha": item["sha"], "rel": item["rel"], "decision": "keep", "kind": "essay", "authorship": "own",
               "finished": "finished", "languages": "en", "sure": True, "reason": "own essay"}
    queue.with_name("queue_01.verdicts.jsonl").write_text(json.dumps(verdict) + "\n")

    run(root, out)

    [rec] = [json.loads(l) for l in (out / "corpus.jsonl").read_text().splitlines()]
    assert rec["id"] == hashlib.sha256(pdf.read_bytes()).hexdigest()
    assert page_markers(rec["text"]) == [f"PAGE{n:02d}" for n in range(1, 13)]
    assert rec["decided_by"] == "judge"
    assert len(calls) == 1  # the second run answered from the Jev cache
    assert queue_items(out) == []
