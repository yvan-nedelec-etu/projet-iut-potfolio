"""Découpage (chunking) des documents Markdown.

Objectif: produire des morceaux courts, cohérents et stables pour l'indexation RAG.

Principes:
- Découpage par titres Markdown (#, ##, ...)
- Regroupement par paragraphes
- Respect d'une taille max par chunk, avec recouvrement optionnel (overlap)
- Identifiants stables (hash) pour faciliter upsert/update dans Upstash
"""

from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List


_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)\s*$")


@dataclass(frozen=True)
class Chunk:
    id: str
    text: str
    metadata: dict


def load_markdown_files(data_dir: str | os.PathLike = "data") -> List[Path]:
    """Retourne la liste triée des fichiers `.md` dans `data_dir` (récursif)."""

    base = Path(data_dir)
    return sorted([p for p in base.rglob("*.md") if p.is_file()])


def _stable_id(*parts: str) -> str:
    """Génère un identifiant stable (hash) à partir de plusieurs chaînes."""

    h = hashlib.sha1()
    for part in parts:
        h.update(part.encode("utf-8"))
        h.update(b"\0")
    return h.hexdigest()[:20]


def chunk_markdown(
    markdown_text: str,
    *,
    source: str,
    max_chars: int = 1000,
    overlap: int = 120,
    min_chars: int = 200,
) -> List[Chunk]:
    """Découpe un document Markdown en chunks cohérents.

    Stratégie:
    - Découpage en sections selon les titres Markdown.
    - À l'intérieur d'une section, on regroupe par paragraphes et on découpe si nécessaire.
    """

    if max_chars < 200:
        raise ValueError("max_chars too small")
    if overlap < 0:
        raise ValueError("overlap must be >= 0")

    lines = markdown_text.splitlines()

    # On construit une liste de sections (chemin de titres + texte associé).
    heading_stack: list[str] = []
    current_buf: list[str] = []
    sections: list[tuple[str, str]] = []  # (heading_path, section_text)

    def flush_section():
        nonlocal current_buf
        text = "\n".join(current_buf).strip()
        if text:
            heading_path = " > ".join(heading_stack) if heading_stack else "(no heading)"
            sections.append((heading_path, text))
        current_buf = []

    for line in lines:
        m = _HEADING_RE.match(line)
        if m:
            flush_section()
            level = len(m.group(1))
            title = m.group(2).strip()
            # Ajuste le niveau courant des titres.
            heading_stack = heading_stack[: level - 1]
            heading_stack.append(title)
            continue

        current_buf.append(line)

    flush_section()

    chunks: list[Chunk] = []

    def emit_chunk(heading_path: str, body: str, idx: int):
        body = body.strip()
        if not body:
            return
        prefix = f"{heading_path}\n\n"
        if len(body) < min_chars and chunks:
            # Si le chunk est trop petit, on tente de le fusionner au précédent
            # quand cela reste cohérent (même source + même heading).
            prev = chunks[-1]
            if prev.metadata.get("source") == source and prev.metadata.get("heading") == heading_path:
                prev_text = prev.text or ""
                prev_body = prev_text[len(prefix) :] if prev_text.startswith(prefix) else prev_text
                merged_body = (prev_body + "\n\n" + body).strip()
                merged_text = (prefix + merged_body).strip()
                new_id = _stable_id(source, heading_path, merged_body)
                chunks[-1] = Chunk(
                    id=new_id,
                    text=merged_text,
                    metadata={**prev.metadata, "chunk_index": prev.metadata.get("chunk_index", 0)},
                )
                return
        chunk_id = _stable_id(source, heading_path, body)
        chunks.append(
            Chunk(
                id=chunk_id,
                text=(prefix + body).strip(),
                metadata={
                    "source": source,
                    "heading": heading_path,
                    "chunk_index": idx,
                },
            )
        )

    for heading_path, section_text in sections:
        # Découpe en paragraphes (séparés par ligne(s) vide(s)) pour préserver la structure.
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", section_text) if p.strip()]
        buf: list[str] = []
        buf_len = 0
        idx = 0

        def flush_buf():
            nonlocal buf, buf_len, idx
            if not buf:
                return
            emit_chunk(heading_path, "\n\n".join(buf), idx)
            idx += 1
            buf = []
            buf_len = 0

        for para in paragraphs:
            para_len = len(para) + (2 if buf else 0)
            if buf_len + para_len <= max_chars:
                buf.append(para)
                buf_len += para_len
                continue

            # flush current chunk
            flush_buf()

            # Paragraphe trop gros -> découpe brute avec recouvrement.
            if len(para) > max_chars:
                start = 0
                while start < len(para):
                    end = min(len(para), start + max_chars)
                    piece = para[start:end]
                    emit_chunk(heading_path, piece, idx)
                    idx += 1
                    if end >= len(para):
                        break
                    start = max(0, end - overlap)
                continue

            buf.append(para)
            buf_len = len(para)

        flush_buf()

    return chunks


def chunk_markdown_files(
    data_dir: str | os.PathLike = "data",
    *,
    max_chars: int = 1000,
    overlap: int = 120,
    min_chars: int = 200,
) -> List[Chunk]:
    """Découpe tous les fichiers Markdown d'un dossier et concatène les chunks."""

    base = Path(data_dir)
    chunks: list[Chunk] = []
    for md_path in load_markdown_files(data_dir):
        text = md_path.read_text(encoding="utf-8")
        source = str(md_path.relative_to(base)).replace("\\", "/")
        chunks.extend(
            chunk_markdown(
                text,
                source=source,
                max_chars=max_chars,
                overlap=overlap,
                min_chars=min_chars,
            )
        )
    return chunks
