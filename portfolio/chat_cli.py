"""Runner terminal (CLI) pour discuter avec l'agent.

Deux modes:
- interactif (boucle input)
- one-shot via `--question`
"""

from __future__ import annotations

import argparse
import os

from dotenv import load_dotenv
from agents import Runner

from .agent import build_portfolio_agent


def main() -> int:
    """Point d'entrée CLI."""

    # Charge les variables d'environnement depuis `.env` (si présent) pour:
    # - OPENAI_API_KEY
    # - identifiants Upstash (si tu utilises l'outil RAG)
    load_dotenv(override=True)

    parser = argparse.ArgumentParser(description="Chat in the terminal with the portfolio RAG agent")
    parser.add_argument("--namespace", default="portfolio", help="Upstash Vector namespace used for retrieval")
    parser.add_argument(
        "--style",
        default="concis",
        choices=["concis", "détaillé"],
        help="Niveau de détails des réponses",
    )
    parser.add_argument("--question", default=None, help="Ask a single question and exit")
    args = parser.parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY non défini (mets-le dans .env).")
        return 2

    # Le CLI est volontairement minimal: on fait un appel par message.
    # Si tu veux une continuité conversationnelle en CLI, tu peux ajouter
    # `previous_response_id` comme dans Streamlit.
    agent = build_portfolio_agent(namespace=args.namespace, response_style=args.style)

    def run_once(user_text: str) -> None:
        """Exécute un tour de conversation et affiche la réponse."""
        # Appel simple (one-shot). La continuité est gérée côté Streamlit.
        result = Runner.run_sync(agent, user_text)
        print(result.final_output)

    if args.question:
        run_once(args.question)
        return 0

    print("Portfolio agent (RAG) — tape 'exit' pour quitter")
    while True:
        try:
            user_text = input("\nYou> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbye")
            return 0

        if not user_text:
            continue
        if user_text.lower() in {"exit", "quit"}:
            return 0

        run_once(user_text)


if __name__ == "__main__":
    raise SystemExit(main())
