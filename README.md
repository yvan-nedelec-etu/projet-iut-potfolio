# Portfolio IA — Chatbot RAG (Streamlit)

Ce projet est un chatbot conversationnel qui présente mon portfolio. L’app s’appuie sur une base vectorielle Upstash pour retrouver les infos et répondre comme si Yvan parlait directement.

## Ce que fait l’application

- Chat en temps réel via Streamlit
- RAG sur des fichiers Markdown du dossier [data/](data/)
- Quiz intégré et petites commandes (liens, stats, easter eggs)
- Sauvegarde locale des conversations dans [data/conversations.json](data/conversations.json)

## Contenu principal du projet

- Interface Streamlit : [streamlit_app.py](streamlit_app.py)
- Agent et logique RAG : [portfolio/agent.py](portfolio/agent.py) et [portfolio/rag.py](portfolio/rag.py)
- Chunking et indexation : [portfolio/chunking.py](portfolio/chunking.py), [portfolio/indexing.py](portfolio/indexing.py)
- Script CLI d’indexation : [portfolio/index_data.py](portfolio/index_data.py)

## Pré-requis

- Python 3.12+ recommandé
- Un compte Upstash Vector configuré en mode Hybrid
- Une clé OpenAI dans un fichier .env

Variables attendues dans .env :

- OPENAI_API_KEY
- UPSTASH_VECTOR_REST_URL
- UPSTASH_VECTOR_REST_TOKEN

## Mise en place rapide

1. Installer les dépendances
    - pip install -r requirements.txt

2. Créer un .env à partir de .env.example

3. Indexer les documents (si besoin)
    - python -m portfolio.index_data --data-dir data --namespace portfolio

4. Lancer l’application
    - streamlit run streamlit_app.py

## Structure des données

Le dossier [data/](data/) contient les fichiers Markdown décrivant les sections du portfolio (projets, compétences, parcours, etc.). L’indexation découpe ces fichiers en chunks pour la recherche vectorielle.

## Notes

- Si tu modifies un fichier dans [data/](data/), relance l’indexation.
- L’historique de conversation est sauvegardé localement, sans service externe.