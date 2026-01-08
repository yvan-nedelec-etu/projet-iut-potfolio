"""RAG helpers: retrieval from Upstash Vector and context formatting.

Objectif:
- Interroger Upstash Vector avec un texte (mode HYBRID)
- Retourner des extraits pertinents
- Fournir un contexte "neutre" à l'agent (sans références affichables)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from upstash_vector import Index
from upstash_vector.types import QueryMode

from .indexing import get_upstash_index


@dataclass(frozen=True)
class RetrievedChunk:
    """Résultat de recherche vectorielle (chunk)."""

    id: str
    score: float
    text: str
    metadata: dict


def search_portfolio(
    query: str,
    *,
    top_k: int = 5,
    namespace: str = "portfolio",
    index: Index | None = None,
) -> List[RetrievedChunk]:
    """Recherche des chunks pertinents pour une requête.

    Notes:
    - Utilise `QueryMode.HYBRID` (dense+sparse) pour coller au setup conseillé.
    - Retourne une liste vide si la requête est vide.
    """

    if not query or not query.strip():
        return []
    idx = index or get_upstash_index()
    results = idx.query(
        data=query,
        top_k=top_k,
        include_metadata=True,
        include_data=True,
        namespace=namespace,
        query_mode=QueryMode.HYBRID,
    )
    out: list[RetrievedChunk] = []
    for r in results:
        out.append(
            RetrievedChunk(
                id=r.id,
                score=r.score,
                text=r.data or "",
                metadata=r.metadata or {},
            )
        )
    return out


def format_context(chunks: List[RetrievedChunk], *, max_items: int = 5) -> str:
    """Formate un contexte compact pour l'agent.

    Important:
    - On n'inclut volontairement PAS les références (source/heading/score)
      pour éviter que l'agent les répète dans sa réponse.
    """

    if not chunks:
        return ""

    # Séparateur léger entre extraits pour aider l'agent sans exposer de références.
    excerpts: list[str] = []
    for c in chunks[:max_items]:
        txt = (c.text or "").strip()
        if txt:
            excerpts.append(txt)
    return "\n\n---\n\n".join(excerpts)
