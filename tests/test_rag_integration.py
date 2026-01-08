import os
import time
import uuid

import pytest
from dotenv import load_dotenv

from upstash_vector import Vector

from portfolio.indexing import get_upstash_index
from portfolio.rag import search_portfolio


load_dotenv(override=True)


@pytest.mark.integration
def test_upstash_index_and_query_roundtrip():
    if not os.getenv("UPSTASH_VECTOR_REST_URL") or not os.getenv("UPSTASH_VECTOR_REST_TOKEN"):
        pytest.skip("Identifiants Upstash manquants; test d'intégration ignoré.")

    index = get_upstash_index()
    namespace = f"test-portfolio-{uuid.uuid4()}"

    token = f"TOKEN-{uuid.uuid4()}"
    vector_id = f"test-{uuid.uuid4()}"

    index.upsert(
        vectors=[
            Vector(
                id=vector_id,
                data=f"Mon portfolio contient le token unique: {token}.",
                metadata={"source": "test.md", "heading": "Test"},
            )
        ],
        namespace=namespace,
    )

    try:
        # Upstash indexing can be eventually-consistent; retry a few times.
        results = []
        for _ in range(10):
            results = search_portfolio(token, top_k=3, namespace=namespace, index=index)
            if results:
                break
            time.sleep(0.5)

        assert results, "Expected at least one search result"
        assert any(token in r.text for r in results)
    finally:
        index.delete(ids=[vector_id], namespace=namespace)
