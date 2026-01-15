"""Outils Python du projet.

Ce package regroupe la logique "backend" du chatbot:
- Chunking: découpe des Markdown en morceaux indexables.
- Indexing: envoi des chunks dans Upstash Vector.
- RAG: recherche dans l'index et formatage de contexte.
- Agent: configuration openai-agents (persona + tool de retrieval).

Note: l'UI Streamlit est dans `streamlit_app.py` (hors package).

Cela permet d 'avoir un package et de pouvoir l'importer dans des scripts
de test ou d'indexation, ou dans l'application Streamlit.
"""
