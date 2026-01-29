"""CLI d'indexation.

Usage:
`python -m portfolio.index_data --data-dir data --namespace portfolio`
"""

from __future__ import annotations

import argparse

from .indexing import index_data_dir


def construire_parser() -> argparse.ArgumentParser:
    """Construit le parser d'arguments.

    Returns:
        argparse.ArgumentParser: Parser configuré pour la CLI.
    """
    parser = argparse.ArgumentParser(
        description="Chunk and index portfolio markdown files into Upstash Vector"
    )
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--namespace", default="portfolio")
    parser.add_argument("--max-chars", type=int, default=1000)
    return parser


def main() -> int:
    """Point d'entrée CLI.

    Returns:
        int: Code de sortie.
    """
    parser = construire_parser()
    args = parser.parse_args()

    # max_chars : taille max d'un chunk (plus petit = plus précis, mais plus de chunks)
    ids = index_data_dir(
        data_dir=args.data_dir,
        namespace=args.namespace,
        max_chars=args.max_chars,
    )

    # Si relance de data, relancer cette commande pour mettre l'index à jour.
    print(f"Indexed {len(ids)} chunks into namespace '{args.namespace}'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
