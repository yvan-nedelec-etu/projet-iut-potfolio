"""
- Interroger Upstash Vector avec un texte
- Retourner des extraits pertinents
- Fournir un contexte neutre à l'agent
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from upstash_vector import Index
from upstash_vector.types import QueryMode

from .indexing import get_upstash_index


@dataclass(frozen=True)
class RetrievedChunk:
    """Résultat de recherche vectorielle.

    Args:
        id (str): Identifiant du chunk.
        score (float): Score de pertinence.
        text (str): Texte du chunk.
        metadata (dict): Métadonnées associées.
    """

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

    Args:
        query (str): Texte de recherche.
        top_k (int): Nombre maximal de résultats.
        namespace (str): Namespace Upstash.
        index (Index | None): Index Upstash optionnel.

    Returns:
        list[RetrievedChunk]: Liste des chunks pertinents.
    """
    if est_requete_vide(query):
        return []

    idx = index or get_upstash_index()

    # Mode hybride = dense + sparse, pratique pour les noms propres et requêtes courtes.
    results = idx.query(
        data=query,
        top_k=top_k,
        include_metadata=True,
        include_data=True,
        namespace=namespace,
        query_mode=QueryMode.HYBRID,
    )
    return convertir_resultats(results)


def format_context(chunks: List[RetrievedChunk], *, max_items: int = 5) -> str:
    """Formate un contexte compact pour l'agent.

    Args:
        chunks (list[RetrievedChunk]): Chunks à formatter.
        max_items (int): Limite du nombre d'extraits.

    Returns:
        str: Contexte prêt à être injecté dans le prompt.
    """
    if not chunks:
        return ""

    # On garde le texte brut et on sépare légèrement les extraits.
    extraits = [
        (c.text or "").strip()
        for c in chunks[:max_items]
        if (c.text or "").strip()
    ]
    return "\n\n---\n\n".join(extraits)


def est_requete_vide(query: str) -> bool:
    """Vérifie si une requête est vide ou composée d'espaces.

    Args:
        query (str): Texte fourni par l'utilisateur.

    Returns:
        bool: True si la requête est vide, sinon False.
    """
    return not query or not query.strip()


def convertir_resultats(results: Iterable) -> List[RetrievedChunk]:
    """Convertit les résultats Upstash en objets `RetrievedChunk`.

    Args:
        results (Iterable): Résultats bruts de la recherche Upstash.

    Returns:
        list[RetrievedChunk]: Résultats normalisés.
    """
    chunks: list[RetrievedChunk] = []
    for r in results:
        chunks.append(
            RetrievedChunk(
                id=r.id,
                score=r.score,
                text=r.data or "",
                metadata=r.metadata or {},
            )
        )
    return chunks
