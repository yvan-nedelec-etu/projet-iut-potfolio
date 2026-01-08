"""CLI d'indexation.

Usage:
`python -m portfolio.index_data --data-dir data --namespace portfolio`
"""

from __future__ import annotations

import argparse

from .indexing import index_data_dir


def main() -> int:
    """Point d'entrée CLI."""

    parser = argparse.ArgumentParser(description="Chunk and index portfolio markdown files into Upstash Vector")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--namespace", default="portfolio")
    parser.add_argument("--max-chars", type=int, default=1000)
    parser.add_argument("--overlap", type=int, default=120)
    parser.add_argument("--min-chars", type=int, default=200)
    args = parser.parse_args()

    # Paramètres de chunking:
    # - max_chars: taille max d'un chunk (plus petit => plus précis, mais plus de chunks)
    # - overlap: recouvrement lors d'un découpage "brut" (paragraphe très long)
    # - min_chars: évite d'avoir des chunks trop petits (fusion dans la même section)
    ids = index_data_dir(
        data_dir=args.data_dir,
        namespace=args.namespace,
        max_chars=args.max_chars,
        overlap=args.overlap,
        min_chars=args.min_chars,
    )
    # Important: si tu modifies les fichiers Markdown dans `data/`, relance cette commande
    # pour mettre l'index Upstash à jour.
    print(f"Indexed {len(ids)} chunks into namespace '{args.namespace}'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
