"""Tests unitaires du module de chunking."""

from portfolio.chunking import chunk_markdown


def test_chunking_splits_by_heading_and_size():
    """Vérifie que le chunking découpe par titres et respecte la taille max."""

    md = """# Expérience

J'ai travaillé sur un projet de data engineering.

## Détails

""" + ("Texte long. " * 200)

    chunks = chunk_markdown(md, source="example.md", max_chars=400, overlap=50, min_chars=50)
    assert len(chunks) >= 2
    for c in chunks:
        assert c.id
        assert c.text.strip()
        assert c.metadata["source"] == "example.md"
        assert "heading" in c.metadata
