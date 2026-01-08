"""Outils Python du projet.

Ce package regroupe la logique "backend" du chatbot:
- Chunking: découpe des Markdown en morceaux indexables.
- Indexing: envoi des chunks dans Upstash Vector.
- RAG: recherche dans l'index et formatage de contexte.
- Agent: configuration openai-agents (persona + tool de retrieval).

Note: l'UI Streamlit est dans `streamlit_app.py` (hors package).
"""
