import os
from dotenv import load_dotenv
import pytest

from agents import Agent, Runner, ModelSettings

load_dotenv(override=True)

def test_openai_agent_runs_ping_pong():
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY non défini; test OpenAI ignoré.")

    agent = Agent(
        name="ping-agent",
        instructions="Réponds uniquement avec le mot 'pong' (minuscules), sans ponctuation ni autre texte.",
        model="gpt-4.1-nano",
        model_settings=ModelSettings(temperature=0),
    )

    result = Runner.run_sync(agent, "ping")
    assert result.final_output.strip() == "pong"
    
