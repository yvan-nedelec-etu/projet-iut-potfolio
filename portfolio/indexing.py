"""Indexation des chunks dans Upstash Vector.

Ce module:
- Lit les identifiants Upstash via `.env`
- Transforme les chunks en `Vector`
- Upsert dans un namespace (par défaut `portfolio`)
"""

from __future__ import annotations

import os
from typing import Iterable, List, TypedDict, cast

from dotenv import load_dotenv
from upstash_vector import Index, Vector

from .chunking import chunk_markdown_files


class Chunk(TypedDict):
    """Structure minimale d'un chunk pour l'indexation.

    Args:
        id (str): Identifiant unique du chunk.
        text (str): Contenu textuel.
        metadata (dict): Métadonnées (source, titre, etc.).
    """

    id: str
    text: str
    metadata: dict


def get_upstash_index() -> Index:
    """Construit un client Upstash Vector à partir des variables d'environnement.

    Returns:
        Index: Client Upstash Vector prêt à l'emploi.
    """
    # On recharge le .env pour que ça marche partout (CLI, tests, Streamlit).
    load_dotenv(override=True)
    url, token = lire_config_upstash()
    if not url or not token:
        raise RuntimeError("Missing UPSTASH_VECTOR_REST_URL or UPSTASH_VECTOR_REST_TOKEN")
    return Index(url=url, token=token)


def lire_config_upstash() -> tuple[str | None, str | None]:
    """Lit les variables d'environnement nécessaires à Upstash.

    Returns:
        tuple[str | None, str | None]: URL et token Upstash.
    """
    url = os.getenv("UPSTASH_VECTOR_REST_URL")
    token = os.getenv("UPSTASH_VECTOR_REST_TOKEN")
    return url, token


def upsert_chunks(index: Index, chunks: Iterable[Chunk], *, namespace: str = "portfolio") -> List[str]:
    """Upsert une liste de chunks et retourne les IDs insérés.

    Args:
        index (Index): Client Upstash.
        chunks (Iterable[Chunk]): Chunks à indexer.
        namespace (str): Namespace Upstash.

    Returns:
        list[str]: Liste des identifiants insérés.
    """
    liste_chunks = list(chunks)
    vectors = construire_vecteurs(liste_chunks)

    # Les IDs sont stables, donc l'upsert met à jour proprement si un fichier change.
    index.upsert(vectors=vectors, namespace=namespace)
    return [c["id"] for c in liste_chunks]


def construire_vecteurs(chunks: Iterable[Chunk]) -> List[Vector]:
    """Transforme les chunks en objets `Vector` pour Upstash.

    Args:
        chunks (Iterable[Chunk]): Chunks à convertir.

    Returns:
        list[Vector]: Vecteurs prêts pour l'upsert.
    """
    return [
        Vector(id=c["id"], data=c["text"], metadata=dict(c["metadata"]))
        for c in chunks
    ]


def index_data_dir(
    *,
    data_dir: str = "data",
    namespace: str = "portfolio",
    max_chars: int = 1000,
) -> List[str]:
    """Découpe `data_dir` puis indexe dans Upstash (namespace).

    Args:
        data_dir (str): Dossier contenant les fichiers Markdown.
        namespace (str): Namespace Upstash.
        max_chars (int): Taille max d'un chunk.

    Returns:
        list[str]: IDs des chunks indexés.
    """
    chunks = cast(List[Chunk], chunk_markdown_files(
        data_dir,
        max_chars=max_chars,
    ))
    index = get_upstash_index()
    return upsert_chunks(index, chunks, namespace=namespace)
