import os
import uuid
from dotenv import load_dotenv
from upstash_vector import Index, Vector
import pytest

load_dotenv(override=True)

def test_upstash():
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