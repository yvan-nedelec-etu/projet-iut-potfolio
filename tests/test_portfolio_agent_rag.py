"""Test d'intégration: l'agent sait appeler un outil de retrieval.

Ignoré automatiquement sans `OPENAI_API_KEY` et/ou identifiants Upstash.
"""

import os
import time
import uuid

import pytest
from dotenv import load_dotenv

from agents import Agent, ModelSettings, Runner, function_tool
from upstash_vector import Vector

from portfolio.indexing import get_upstash_index
from portfolio.rag import format_context, search_portfolio


load_dotenv(override=True)


@pytest.mark.integration
def test_agent_can_use_retrieval_tool():
    """Vérifie que l'agent récupère le contexte et renvoie le token attendu."""

    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY non défini; test agent RAG ignoré.")
    if not os.getenv("UPSTASH_VECTOR_REST_URL") or not os.getenv("UPSTASH_VECTOR_REST_TOKEN"):
        pytest.skip("Identifiants Upstash manquants; test agent RAG ignoré.")

    index = get_upstash_index()
    namespace = f"test-agent-{uuid.uuid4()}"

    token = f"TOKEN-{uuid.uuid4()}"
    vector_id = f"test-{uuid.uuid4()}"
    index.upsert(
        vectors=[
            Vector(
                id=vector_id,
                data=f"Info portfolio: {token}",
                metadata={"source": "agent.md", "heading": "Agent"},
            )
        ],
        namespace=namespace,
    )

    @function_tool(name_override="retrieve_portfolio")
    def retrieve_portfolio(query: str, top_k: int = 3) -> str:
        """Outil de test: renvoie un contexte formaté depuis un index isolé."""

        return format_context(search_portfolio(query, top_k=top_k, namespace=namespace, index=index))

    agent = Agent(
        name="rag-smoke",
        instructions=(
            "Tu DOIS appeler retrieve_portfolio avant de répondre. "
            "Si le contexte contient 'TOKEN-', réponds uniquement avec la ligne qui contient 'TOKEN-'. "
            "Sinon réponds 'absent'."
        ),
        model="gpt-4.1-nano",
        model_settings=ModelSettings(temperature=0),
        tools=[retrieve_portfolio],
    )

    try:
        # Retry to reduce flakiness (indexing + tool call scheduling).
        out = ""
        for _ in range(6):
            out = Runner.run_sync(agent, f"Trouve le token: {token}").final_output
            if out and "TOKEN-" in out:
                break
            time.sleep(0.5)

        assert "TOKEN-" in out
    finally:
        index.delete(ids=[vector_id], namespace=namespace)

