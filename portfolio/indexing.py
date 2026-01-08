"""Indexation des chunks dans Upstash Vector.

Ce module:
- Lit les identifiants Upstash via `.env`
- Transforme les chunks en `Vector`
- Upsert dans un namespace (par défaut `portfolio`)
"""

from __future__ import annotations

import os
from typing import Iterable, List

from dotenv import load_dotenv
from upstash_vector import Index, Vector

from .chunking import Chunk, chunk_markdown_files


def get_upstash_index() -> Index:
    """Construit un client Upstash Vector à partir des variables d'environnement."""
    # On charge `.env` à chaque appel pour rendre le module utilisable:
    # - en CLI
    # - en tests
    # - en Streamlit
    load_dotenv(override=True)
    url = os.getenv("UPSTASH_VECTOR_REST_URL")
    token = os.getenv("UPSTASH_VECTOR_REST_TOKEN")
    if not url or not token:
        raise RuntimeError("Missing UPSTASH_VECTOR_REST_URL or UPSTASH_VECTOR_REST_TOKEN")
    return Index(url=url, token=token)


def upsert_chunks(index: Index, chunks: Iterable[Chunk], *, namespace: str = "portfolio") -> List[str]:
    """Upsert une liste de chunks et retourne les IDs insérés.

    Note: `Index.upsert` retourne un statut; on renvoie plutôt la liste d'IDs
    pour faciliter les nettoyages/tests.
    """

    vectors = [Vector(id=c.id, data=c.text, metadata=dict(c.metadata)) for c in chunks]
    # Upstash upsert returns a string status; keep the IDs so callers can delete.
    # Les IDs sont stables (hash) -> l'upsert met à jour proprement quand un fichier change.
    index.upsert(vectors=vectors, namespace=namespace)
    return [c.id for c in chunks]


def index_data_dir(
    *,
    data_dir: str = "data",
    namespace: str = "portfolio",
    max_chars: int = 1000,
    overlap: int = 120,
    min_chars: int = 200,
) -> List[str]:
    """Découpe `data_dir` puis indexe dans Upstash (namespace)."""

    chunks = chunk_markdown_files(
        data_dir,
        max_chars=max_chars,
        overlap=overlap,
        min_chars=min_chars,
    )
    index = get_upstash_index()
    return upsert_chunks(index, chunks, namespace=namespace)
