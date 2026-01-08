"""Interface Streamlit (étape 6).

Objectifs UI demandés:
- Une interface plus "stylée" / originale (mais uniquement avec les composants natifs Streamlit)
- Un vrai chat (historique + input)
- Pas d'affichage de sources/références
- Réponses naturelles (small talk OK)

Note: Streamlit ne permet pas de charger une police JetBrains via `config.toml`.
Sans injection HTML/CSS (interdite ici), on utilise `font = "monospace"` côté thème.
"""

from __future__ import annotations

import os

import streamlit as st
from dotenv import load_dotenv

from agents import Runner

from portfolio.agent import build_portfolio_agent
from portfolio.rag import format_context, search_portfolio


APP_TITLE = "Chat — Yvan NEDELEC"
DEFAULT_NAMESPACE = "portfolio"
AGENT_VERSION = "2026-01-08-v3"


def _has_openai_key() -> bool:
    """Vérifie la présence de la clé OpenAI."""

    return bool(os.getenv("OPENAI_API_KEY"))


def _has_upstash_creds() -> bool:
    """Vérifie la présence des identifiants Upstash Vector."""

    return bool(os.getenv("UPSTASH_VECTOR_REST_URL")) and bool(os.getenv("UPSTASH_VECTOR_REST_TOKEN"))


def _init_session_state() -> None:
    """Initialise l'état Streamlit (messages + continuité de conversation)."""

    # Si on a changé la logique de l'agent, on reset la continuité pour éviter
    # de garder une ancienne personnalité via previous_response_id.
    if st.session_state.get("agent_version") != AGENT_VERSION:
        st.session_state.agent_version = AGENT_VERSION
        st.session_state.previous_response_id = None
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Salut, moi c'est Yvan. Tu peux me poser des questions sur mon alternance, mes projets, "
                    "mes compétences ou mes études."
                ),
            }
        ]

    if "previous_response_id" not in st.session_state:
        st.session_state.previous_response_id = None

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Salut, moi c'est Yvan. Tu peux me poser des questions sur mon alternance, mes projets, "
                    "mes compétences ou mes études."
                ),
            }
        ]

    if "pending_user_text" not in st.session_state:
        st.session_state.pending_user_text = None


def _reset_chat() -> None:
    """Réinitialise la conversation côté UI + côté agent."""

    st.session_state.previous_response_id = None
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Ok, on repart à zéro. Tu veux parler de quoi ?",
        }
    ]


def _expand_query_with_history(user_text: str) -> str:
    """Rend la requête RAG plus robuste sur les messages courts.

    Exemple: utilisateur -> "académiques" après "liste tous tes projets".
    """

    txt = (user_text or "").strip()
    if not txt:
        return ""

    # Si c'est très court, on le recolle au dernier message utilisateur.
    if len(txt) <= 20 or len(txt.split()) <= 2:
        for msg in reversed(st.session_state.get("messages", [])):
            if msg.get("role") == "user" and msg.get("content"):
                prev = str(msg["content"]).strip()
                if prev and prev != txt:
                    return f"{prev} {txt}".strip()
    return txt


def _inject_rag_context(user_text: str, *, namespace: str) -> str:
    """Ajoute un contexte RAG directement dans le prompt envoyé à l'agent.

    But: éviter les échecs de tool-calling et améliorer les réponses sur les relances courtes.
    """

    if not _has_upstash_creds():
        return user_text

    query = _expand_query_with_history(user_text)
    try:
        chunks = search_portfolio(query, top_k=8, namespace=namespace)
        ctx = format_context(chunks, max_items=8)
    except Exception:
        return user_text

    if not ctx.strip():
        return user_text

    return (
        "Infos sur moi (à utiliser si pertinent) :\n"
        f"{ctx}\n\n"
        "Question de l'utilisateur :\n"
        f"{user_text}"
    )


def main() -> None:
    # Charge .env (OPENAI_API_KEY + Upstash)
    load_dotenv(override=True)

    st.set_page_config(page_title=APP_TITLE, layout="centered")
    _init_session_state()

    # Sidebar = contrôle, sans polluer le chat.
    with st.sidebar:
        st.header("Réglages")
        namespace = st.text_input("Namespace Upstash", value=DEFAULT_NAMESPACE)

        response_style = st.selectbox(
            "Style de réponse",
            options=["concis", "détaillé"],
            index=0,
            help="Change le niveau de détails des réponses.",
        )

        st.divider()
        st.subheader("Questions rapides")
        quick_questions = [
            "C'est quoi tes projets ?",
            "Tu fais quoi à la MAIF ?",
            "Quelles sont tes compétences data ?",
            "Tu veux faire quel métier plus tard ?",
        ]

        for q in quick_questions:
            if st.button(q, use_container_width=True):
                st.session_state.pending_user_text = q

        cols = st.columns(2)
        with cols[0]:
            st.metric("OpenAI", "OK" if _has_openai_key() else "Manquant")
        with cols[1]:
            st.metric("Upstash", "OK" if _has_upstash_creds() else "Manquant")

        if st.button("Réinitialiser le chat", use_container_width=True):
            _reset_chat()

    # Bandeau haut
    with st.container(border=True):
        st.title(APP_TITLE)
        st.caption("Un chat sur mon profil — direct, sans références.")

        if not _has_openai_key():
            st.error("OPENAI_API_KEY manquant. Ajoute-le dans .env puis relance.")
            st.stop()

        if not _has_upstash_creds():
            st.info(
                "Upstash n'est pas configuré: je peux discuter, mais je ne pourrai pas récupérer mes infos automatiquement."
            )

    # Construction de l'agent. (Léger, ok à chaque rerun.)
    agent = build_portfolio_agent(namespace=namespace, response_style=response_style)

    # Affichage de l'historique
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Saisie utilisateur (toujours visible). Si une question rapide est cliquée,
    # on l'envoie automatiquement au prochain rerun.
    typed_text = st.chat_input("Écris ici…")
    user_text = st.session_state.pending_user_text or typed_text
    st.session_state.pending_user_text = None
    if not user_text:
        return

    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    # Réponse
    with st.chat_message("assistant"):
        with st.spinner("…"):
            agent_input = _inject_rag_context(user_text, namespace=namespace)
            result = Runner.run_sync(
                agent,
                agent_input,
                previous_response_id=st.session_state.previous_response_id,
                max_turns=6,
            )

        answer = (result.final_output or "").strip()
        st.markdown(answer if answer else "Je n'ai pas réussi à générer une réponse.")

    # Mise à jour de la continuité
    st.session_state.previous_response_id = result.last_response_id
    st.session_state.messages.append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    main()
