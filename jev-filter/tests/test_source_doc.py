"""The Source document: one file read once, with one text per reader."""
import hashlib

from jev_filter import SourceDoc


def test_markdown_text_keeps_link_domains_and_id_hashes_the_source_bytes(tmp_path):
    raw = "See [the post](https://archive.is/x/https://tsargrad.tv/a) now.\n"
    (tmp_path / "a.md").write_text(raw)

    src = SourceDoc.read(tmp_path, tmp_path / "a.md")

    assert src.rel == "a.md"
    assert src.text == "See the post (→ archive.is → tsargrad.tv) now."
    assert src.id == hashlib.sha256(raw.encode()).hexdigest()


def test_markdown_full_text_is_the_source_itself(tmp_path):
    raw = "# Title\n\nSee [the post](https://tsargrad.tv/a) now.\n"
    (tmp_path / "a.md").write_text(raw)

    assert SourceDoc.read(tmp_path, tmp_path / "a.md").full_text() == raw


def test_pdf_text_is_a_sample_but_full_text_has_every_page(tmp_path):
    from conftest import page_markers, write_pdf

    write_pdf(tmp_path / "book.pdf", pages=12)

    src = SourceDoc.read(tmp_path, tmp_path / "book.pdf")

    assert src.pages == 12
    assert page_markers(src.text) == ["PAGE01", "PAGE02", "PAGE03", "PAGE04", "PAGE07", "PAGE12"]
    assert page_markers(src.full_text()) == [f"PAGE{n:02d}" for n in range(1, 13)]


def test_epub_full_text_is_not_cut_at_40k_characters(tmp_path):
    import zipfile

    with zipfile.ZipFile(tmp_path / "book.epub", "w", zipfile.ZIP_DEFLATED) as z:
        for n in (1, 2, 3):
            z.writestr(f"ch{n}.xhtml", f"<html><body><p>CHAP{n} " + "word " * 5000 + "</p></body></html>")

    src = SourceDoc.read(tmp_path, tmp_path / "book.epub")

    assert "CHAP3" not in src.text
    assert all(f"CHAP{n}" in src.full_text() for n in (1, 2, 3))


def test_features_see_the_clip_header_in_the_source(tmp_path):
    (tmp_path / "clip.md").write_text("> Site: example.org\n\n" + "word " * 100)

    feats = SourceDoc.read(tmp_path, tmp_path / "clip.md").features

    assert feats["clip_header"] is True
    assert feats["words"] == 103


def test_jev_excerpt_samples_head_three_middles_and_tail(tmp_path):
    (tmp_path / "a.txt").write_text("0123456789" * 10)

    src = SourceDoc.read(tmp_path, tmp_path / "a.txt")

    gap = "\n\n[...]\n\n"
    assert src.excerpt(40) == gap.join(["01234567890123456789", "8901", "7890", "5678", "456789"])
    assert src.excerpt(1000) == "0123456789" * 10


def test_a_broken_file_is_read_with_an_error_and_no_text(tmp_path):
    (tmp_path / "broken.docx").write_bytes(b"not a zip")

    src = SourceDoc.read(tmp_path, tmp_path / "broken.docx")

    assert src.error.startswith("BadZipFile")
    assert src.text == "" and src.full_text() == ""


def test_a_file_that_cannot_be_opened_is_read_with_an_error(tmp_path):
    locked = tmp_path / "locked.md"
    locked.write_text("text")
    locked.chmod(0)
    try:
        src = SourceDoc.read(tmp_path, locked)
    finally:
        locked.chmod(0o644)

    assert src.error.startswith("PermissionError")
    assert src.text == "" and src.full_text() == ""


def test_the_same_text_as_md_and_txt_has_one_text_sha(tmp_path):
    (tmp_path / "a.md").write_text("Plain words only.\n")
    (tmp_path / "a.txt").write_text("Plain words only.\n")

    md, txt = (SourceDoc.read(tmp_path, tmp_path / n) for n in ("a.md", "a.txt"))

    assert md.text_sha == txt.text_sha


def test_the_judge_reads_markdown_where_it_is(tmp_path):
    (tmp_path / "a.md").write_text("words\n")

    src = SourceDoc.read(tmp_path, tmp_path / "a.md")

    assert src.judge_path(tmp_path / "text") == tmp_path / "a.md"
    assert not (tmp_path / "text").exists()


def test_the_judge_reads_every_page_of_a_pdf_and_its_verdict_key_follows_them(tmp_path):
    from conftest import page_markers, write_pdf

    write_pdf(tmp_path / "book.pdf", pages=12)
    src = SourceDoc.read(tmp_path, tmp_path / "book.pdf")

    path = src.judge_path(tmp_path / "text")

    assert path.parent == tmp_path / "text"
    assert page_markers(path.read_text()) == [f"PAGE{n:02d}" for n in range(1, 13)]
    assert src.full_sha == hashlib.sha256(path.read_text().encode()).hexdigest()


def test_docx_text_is_its_paragraphs(tmp_path):
    import zipfile

    body = "<w:p><w:r><w:t>First</w:t></w:r><w:r><w:t> line.</w:t></w:r></w:p><w:p></w:p><w:p><w:r><w:t>Second.</w:t></w:r></w:p>"
    with zipfile.ZipFile(tmp_path / "a.docx", "w") as z:
        z.writestr("word/document.xml", f"<w:document><w:body>{body}</w:body></w:document>")

    src = SourceDoc.read(tmp_path, tmp_path / "a.docx")

    assert src.text == src.full_text() == "First line.\n\nSecond."


def test_html_text_drops_scripts_and_tags(tmp_path):
    (tmp_path / "a.html").write_text("<script>x()</script><h1>Title</h1><p>One &amp; two</p>")

    assert SourceDoc.read(tmp_path, tmp_path / "a.html").text == "Title\nOne & two"
