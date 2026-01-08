"""Test d'intégration simple pour valider l'accès Upstash.

Ignoré automatiquement si les identifiants Upstash manquent.
"""

import os
import uuid

import pytest
from dotenv import load_dotenv
from upstash_vector import Index, Vector

load_dotenv(override=True)


def test_upstash():
    """Upsert/Delete d'un vecteur pour vérifier la connectivité Upstash."""

    if not os.getenv("UPSTASH_VECTOR_REST_URL") or not os.getenv("UPSTASH_VECTOR_REST_TOKEN"):
        pytest.skip("Identifiants Upstash manquants; test Upstash ignoré.")
    index = Index(
        url=os.getenv("UPSTASH_VECTOR_REST_URL"),
        token=os.getenv("UPSTASH_VECTOR_REST_TOKEN")
    )

    vector_id = f"test-index-{uuid.uuid4()}"

    result = index.upsert(
        vectors=[
            Vector(
                id=vector_id,
                data="exemple de texte index",
                metadata={"test": "index"},
            )
        ]
    )
    assert result is not None

    index.delete(ids=[vector_id])