"""Interface Streamlit — Portfolio Yvan NEDELEC.

Version simplifiée et stable avec fonctionnalités bonus qui marchent.
"""

from __future__ import annotations

import os
import random
import base64
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from agents import Runner

from portfolio.agent import build_portfolio_agent
from portfolio.rag import format_context, search_portfolio


# ═══════════════════════════════════════════════════════════════════════════════
# 📌 CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

APP_TITLE = "yvan@portfolio:~$ ./chat"
DEFAULT_NAMESPACE = "portfolio"
AGENT_VERSION = "2026-01-15-v6"

# Timeline du parcours
TIMELINE_EVENTS = [
    {"year": "2022", "event": "🎓 Bac obtenu", "detail": "Début de l'aventure !"},
    {"year": "2022", "event": "📚 Entrée en BUT SD", "detail": "IUT - Science des Données"},
    {"year": "2024", "event": "💼 Alternance MAIF", "detail": "Data Engineering & Python"},
    {"year": "2025", "event": "🚀 Projets Data", "detail": "ML, Dashboard, ETL"},
    {"year": "2026", "event": "🎯 Aujourd'hui", "detail": "En recherche d'opportunités"},
]

# Liens sociaux
SOCIAL_LINKS = {
    "github": "https://github.com/yvan-nedelec-etu",
    "linkedin": "https://www.linkedin.com/in/yvan-nedelec-40b779214/",
}

FUN_FACTS = [
    "💡 J'ai appris Python en autodidacte avant de commencer mon BUT !",
    "🎵 Je produis de la musique sur FL Studio à mes heures perdues.",
    "🏋️ Je fais de la musculation pour garder la forme.",
    "🚗 Je suis passionné par l'automobile, surtout les modèles anciens.",
    "💻 Mon premier projet était un site web en PHP/JavaScript.",
    "📊 À la MAIF, je migre des traitements SAS vers Python.",
    "🎯 Mon objectif: devenir expert en Machine Learning ou Data Engineering.",
]

EASTER_EGGS = {
    "konami": "🎮 Tu connais le Konami Code ? Tu as bon goût !",
    "42": "🌌 La réponse à la grande question sur la vie, l'univers et le reste !",
    "hello world": "👨‍💻 print('Hello, World!') — Le classique des classiques !",
    "matrix": "💊 Tu prends la pilule rouge ou la pilule bleue ?",
}

# Quiz questions (corrigées)
QUIZ_QUESTIONS = [
    {"q": "Dans quelle entreprise je fais mon alternance ?", "options": ["AXA", "MAIF", "Groupama", "Allianz"], "answer": 1},
    {"q": "Quel langage j'utilise le plus en data ?", "options": ["Java", "C++", "Python", "Ruby"], "answer": 2},
    {"q": "Quelle formation je suis actuellement ?", "options": ["Master IA", "BUT Science des Données", "École d'ingénieur", "Licence Info"], "answer": 1},
    {"q": "Quel outil j'utilise pour produire de la musique ?", "options": ["Ableton", "FL Studio", "Logic Pro", "GarageBand"], "answer": 1},
]


# ═══════════════════════════════════════════════════════════════════════════════
# 🎨 STYLING
# ═══════════════════════════════════════════════════════════════════════════════

def apply_custom_css() -> None:
    """Applique le thème Terminal/Hacker."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&display=swap');
        
        /* === THÈME TERMINAL HACKER === */
        
        /* Font globale */
        * {
            font-family: 'Fira Code', 'Consolas', 'Monaco', monospace !important;
        }
        
        /* Background noir - TOUT */
        .stApp, .main, [data-testid="stAppViewContainer"], 
        [data-testid="stVerticalBlock"], [data-testid="stMainBlockContainer"],
        .block-container, .stMainBlockContainer {
            background: #0a0a0a !important;
            background-color: #0a0a0a !important;
        }
        
        /* Scanlines sur fond */
        .stApp {
            background-image: 
                radial-gradient(ellipse at top, #0d1a0d 0%, #0a0a0a 50%),
                repeating-linear-gradient(
                    0deg,
                    transparent,
                    transparent 2px,
                    rgba(0, 255, 65, 0.02) 2px,
                    rgba(0, 255, 65, 0.02) 4px
                ) !important;
        }
        
        /* Bottom bar / Footer area - NOIR */
        .stBottom, [data-testid="stBottom"], 
        [data-testid="stBottomBlockContainer"],
        .stChatInputContainer, [data-testid="stChatInput"] {
            background: #0a0a0a !important;
            background-color: #0a0a0a !important;
            border-top: 1px solid #00ff41 !important;
        }
        
        /* Sidebar terminal */
        section[data-testid="stSidebar"], 
        section[data-testid="stSidebar"] > div {
            background: linear-gradient(180deg, #0d1a0d 0%, #0a0a0a 100%) !important;
            border-right: 1px solid #00ff41 !important;
        }
        
        /* Texte vert phosphorescent */
        .stMarkdown, .stText, p, span, label, .stCaption,
        [data-testid="stMarkdownContainer"] p {
            color: #00ff41 !important;
            text-shadow: 0 0 3px rgba(0, 255, 65, 0.4);
        }
        
        /* Titres avec glow */
        h1, h2, h3, h4 {
            color: #00ff41 !important;
            text-shadow: 0 0 10px rgba(0, 255, 65, 0.7), 0 0 20px rgba(0, 255, 65, 0.4) !important;
            font-weight: 600 !important;
        }
        
        /* Chat messages style terminal */
        .stChatMessage {
            background: rgba(0, 20, 0, 0.9) !important;
            border: 1px solid #00ff41 !important;
            border-radius: 0px !important;
            margin: 12px 0 !important;
            padding: 15px !important;
            box-shadow: 0 0 10px rgba(0, 255, 65, 0.2), inset 0 0 30px rgba(0, 255, 65, 0.05);
        }
        
        /* Contenu du message - espacement */
        .stChatMessage [data-testid="stMarkdownContainer"] {
            padding: 5px 0 !important;
        }
        .stChatMessage [data-testid="stMarkdownContainer"] p {
            margin-bottom: 8px !important;
            line-height: 1.6 !important;
        }
        
        /* Avatar style */
        .stChatMessage [data-testid="stChatMessageAvatarUser"],
        .stChatMessage [data-testid="stChatMessageAvatarAssistant"] {
            background: #00ff41 !important;
        }
        
        /* Boutons style terminal */
        .stButton > button {
            background: transparent !important;
            border: 1px solid #00ff41 !important;
            color: #00ff41 !important;
            border-radius: 0px !important;
            font-family: 'Fira Code', monospace !important;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .stButton > button:hover {
            background: #00ff41 !important;
            color: #0a0a0a !important;
            box-shadow: 0 0 20px rgba(0, 255, 65, 0.6);
        }
        
        /* Input style terminal */
        .stChatInput, .stChatInput > div,
        [data-testid="stChatInputTextArea"],
        .stChatInput textarea {
            background: #0a0a0a !important;
            background-color: #0a0a0a !important;
            border: 1px solid #00ff41 !important;
            border-radius: 0px !important;
            color: #00ff41 !important;
        }
        .stChatInput input, .stChatInput textarea {
            color: #00ff41 !important;
            caret-color: #00ff41 !important;
            background: #0a0a0a !important;
        }
        .stChatInput input::placeholder, .stChatInput textarea::placeholder {
            color: rgba(0, 255, 65, 0.5) !important;
        }
        
        /* Selectbox */
        .stSelectbox > div > div,
        .stSelectbox [data-baseweb="select"] {
            background: #0a0a0a !important;
            border: 1px solid #00ff41 !important;
            color: #00ff41 !important;
        }
        .stSelectbox svg {
            fill: #00ff41 !important;
        }
        
        /* Dropdown menu */
        [data-baseweb="popover"], [data-baseweb="menu"] {
            background: #0a0a0a !important;
            border: 1px solid #00ff41 !important;
        }
        [data-baseweb="menu"] li {
            background: #0a0a0a !important;
            color: #00ff41 !important;
        }
        [data-baseweb="menu"] li:hover {
            background: #00ff41 !important;
            color: #0a0a0a !important;
        }
        
        /* Toggle */
        .stCheckbox label span, [data-testid="stCheckbox"] {
            color: #00ff41 !important;
        }
        .stToggle [data-baseweb="checkbox"] {
            background: #0a0a0a !important;
        }
        
        /* Progress bar */
        .stProgress > div > div {
            background: #00ff41 !important;
            box-shadow: 0 0 10px rgba(0, 255, 65, 0.5);
        }
        
        /* Metrics */
        [data-testid="stMetricValue"] {
            color: #00ff41 !important;
            text-shadow: 0 0 10px rgba(0, 255, 65, 0.5);
        }
        [data-testid="stMetricLabel"] {
            color: #00ff41 !important;
        }
        
        /* Info/Warning/Error boxes */
        .stAlert, [data-testid="stAlert"] {
            background: rgba(0, 20, 0, 0.9) !important;
            border: 1px solid #00ff41 !important;
            color: #00ff41 !important;
        }
        
        /* Expander */
        .streamlit-expanderHeader, [data-testid="stExpander"] summary {
            background: transparent !important;
            border: 1px solid #00ff41 !important;
            color: #00ff41 !important;
        }
        [data-testid="stExpander"] {
            background: rgba(0, 20, 0, 0.5) !important;
            border: 1px solid rgba(0, 255, 65, 0.3) !important;
        }
        
        /* Divider */
        hr, [data-testid="stDivider"] {
            border-color: #00ff41 !important;
            opacity: 0.3;
        }
        
        /* Links */
        a {
            color: #00ff41 !important;
        }
        
        /* Link buttons */
        .stLinkButton a {
            background: transparent !important;
            border: 1px solid #00ff41 !important;
            color: #00ff41 !important;
            border-radius: 0px !important;
        }
        .stLinkButton a:hover {
            background: #00ff41 !important;
            color: #0a0a0a !important;
        }
        
        /* Download button */
        .stDownloadButton > button {
            background: transparent !important;
            border: 1px solid #00ff41 !important;
            color: #00ff41 !important;
            border-radius: 0px !important;
        }
        .stDownloadButton > button:hover {
            background: #00ff41 !important;
            color: #0a0a0a !important;
        }
        
        /* Timeline */
        .timeline-item {
            border-left: 2px solid #00ff41;
            padding-left: 15px;
            margin-left: 10px;
            margin-bottom: 10px;
        }
        
        /* Spinner */
        .stSpinner > div {
            border-top-color: #00ff41 !important;
        }
        
        /* Toast */
        [data-testid="stToast"] {
            background: #0a0a0a !important;
            border: 1px solid #00ff41 !important;
            color: #00ff41 !important;
        }

        /* Masquer UI Streamlit */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        [data-testid="stToolbar"] {visibility: hidden;}
        header[data-testid="stHeader"] {display: none !important;}
        
        /* Cacher bouton collapse sidebar (flèche) */
        button[data-testid="stSidebarCollapseButton"] {display: none !important;}
        [data-testid="collapsedControl"] {display: none !important;}
        
        /* Sidebar plus large */
        section[data-testid="stSidebar"] {
            width: 350px !important;
            min-width: 350px !important;
        }
        section[data-testid="stSidebar"] > div {
            width: 350px !important;
        }
        
        /* Avatar rond */
        .stChatMessage img {
            border-radius: 4px !important;
            border: 1px solid #00ff41 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _get_avatar_base64() -> str | None:
    """Charge l'avatar assistant depuis assets/avatar.png."""
    avatar_path = Path("assets/avatar.png")
    if avatar_path.exists():
        data = avatar_path.read_bytes()
        return base64.b64encode(data).decode("utf-8")
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# 🔧 UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def _has_openai_key() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def _has_upstash_creds() -> bool:
    return bool(os.getenv("UPSTASH_VECTOR_REST_URL")) and bool(os.getenv("UPSTASH_VECTOR_REST_TOKEN"))


def _init_session_state() -> None:
    """Initialise l'état de session."""
    defaults = {
        "agent_version": None,
        "previous_response_id": None,
        "messages": [],
        "pending_user_text": None,
        "chat_stats": {"questions": 0, "start_time": datetime.now()},
        "quiz_score": 0,
        "quiz_current": 0,
        "quiz_active": False,
        "current_fun_fact": random.choice(FUN_FACTS),
        "recruiter_mode": False,
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    if st.session_state.agent_version != AGENT_VERSION:
        st.session_state.agent_version = AGENT_VERSION
        st.session_state.previous_response_id = None
        st.session_state.messages = [
            {"role": "assistant", "content": "> Connexion établie...\n\n> Bienvenue sur mon terminal ! Je suis **Yvan**.\n\n> Tape une commande ou pose-moi une question sur mes projets, mon alternance, mes compétences..."}
        ]


def _reset_chat() -> None:
    """Reset la conversation."""
    st.session_state.previous_response_id = None
    st.session_state.messages = [
        {"role": "assistant", "content": "> Session réinitialisée.\n\n> Prêt pour de nouvelles requêtes..."}
    ]
    st.session_state.chat_stats = {"questions": 0, "start_time": datetime.now()}
    st.session_state.quiz_active = False


def _get_chat_stats() -> dict:
    """Statistiques de la conversation."""
    stats = st.session_state.get("chat_stats", {"questions": 0, "start_time": datetime.now()})
    duration = datetime.now() - stats.get("start_time", datetime.now())
    minutes = int(duration.total_seconds() // 60)
    seconds = int(duration.total_seconds() % 60)
    return {
        "questions": stats.get("questions", 0),
        "duration": f"{minutes}m {seconds}s",
        "messages": len(st.session_state.get("messages", [])),
    }


def _export_conversation() -> str:
    """Export la conversation en texte."""
    lines = [
        "=" * 50,
        "💬 Conversation avec Yvan NEDELEC",
        f"📅 Exportée le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
        "=" * 50, "",
    ]
    for msg in st.session_state.get("messages", []):
        role = "🧑 Visiteur" if msg["role"] == "user" else "👨‍💻 Yvan"
        lines.append(f"{role}:\n{msg['content']}\n")
    return "\n".join(lines)


def _check_easter_egg(text: str) -> str | None:
    """Détecte les easter eggs."""
    lower = text.lower().strip()
    for key, response in EASTER_EGGS.items():
        if key in lower:
            return response
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# 🧩 QUIZ
# ═══════════════════════════════════════════════════════════════════════════════

def _render_quiz() -> None:
    """Affiche le quiz interactif."""
    if not st.session_state.get("quiz_active", False):
        return
    
    current = st.session_state.quiz_current
    if current >= len(QUIZ_QUESTIONS):
        score = st.session_state.quiz_score
        total = len(QUIZ_QUESTIONS)
        
        if score == total:
            st.success(f"🏆 Perfect ! Score: {score}/{total}")
        elif score >= total * 0.5:
            st.success(f"👍 Bien joué ! Score: {score}/{total}")
        else:
            st.info(f"💪 Score: {score}/{total} — Continue d'explorer !")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Recommencer", key="quiz_restart"):
                st.session_state.quiz_score = 0
                st.session_state.quiz_current = 0
                st.rerun()
        with col2:
            if st.button("❌ Fermer", key="quiz_close"):
                st.session_state.quiz_active = False
                st.rerun()
        return
    
    q = QUIZ_QUESTIONS[current]
    st.markdown(f"**Question {current + 1}/{len(QUIZ_QUESTIONS)}:** {q['q']}")
    
    cols = st.columns(2)
    for i, option in enumerate(q["options"]):
        with cols[i % 2]:
            if st.button(option, key=f"quiz_{current}_{i}", use_container_width=True):
                if i == q["answer"]:
                    st.session_state.quiz_score += 1
                    st.toast("✅ Bonne réponse !", icon="🎉")
                else:
                    st.toast(f"❌ C'était: {q['options'][q['answer']]}", icon="😅")
                st.session_state.quiz_current += 1
                st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# 🔍 RAG
# ═══════════════════════════════════════════════════════════════════════════════

def _inject_rag_context(user_text: str, *, namespace: str) -> str:
    """Injecte le contexte RAG dans le prompt."""
    if not _has_upstash_creds():
        return user_text
    
    prefix = "[Mode Recruteur] Réponse professionnelle. " if st.session_state.get("recruiter_mode") else ""
    
    try:
        chunks = search_portfolio(user_text, top_k=8, namespace=namespace)
        ctx = format_context(chunks, max_items=8)
    except Exception:
        return prefix + user_text
    
    if not ctx.strip():
        return prefix + user_text
    
    return f"{prefix}Infos sur moi:\n{ctx}\n\nQuestion:\n{user_text}"


# ═══════════════════════════════════════════════════════════════════════════════
# 🖼️ SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════

def _render_sidebar() -> tuple[str, str]:
    """Render la sidebar. Retourne (namespace, response_style)."""
    with st.sidebar:
        # Profil
        st.markdown(
            """
            <div style="text-align: center; padding: 15px 0;">
                <span style="font-size: 3.5em;">👨‍💻</span>
                <h3 style="margin: 10px 0 0 0;">Yvan NEDELEC</h3>
                <p style="opacity: 0.7; font-size: 0.85em;">Data Engineering • Python • ML</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        st.divider()
        
        # Liens
        st.markdown("### 🔗 Liens")
        col1, col2 = st.columns(2)
        with col1:
            st.link_button("🐙 GitHub", SOCIAL_LINKS["github"], use_container_width=True)
        with col2:
            st.link_button("💼 LinkedIn", SOCIAL_LINKS["linkedin"], use_container_width=True)
        
        st.divider()
        
        # Réglages
        st.markdown("### ⚙️ Réglages")
        response_style = st.selectbox("📝 Style de réponse", options=["concis", "détaillé"], index=0)
        st.session_state.recruiter_mode = st.toggle("💼 Mode Recruteur", value=st.session_state.get("recruiter_mode", False))
        
        st.divider()
        
        # Questions rapides
        st.markdown("### 💬 Questions rapides")
        quick_qs = [
            "🚀 C'est quoi tes projets ?",
            "🏢 Tu fais quoi à la MAIF ?",
            "💻 Quelles technos tu maîtrises ?",
            "🎯 Quel métier tu vises ?",
            "🎓 Parle-moi de ta formation",
            "🎸 T'as des passions ?",
        ]
        for q in quick_qs:
            if st.button(q, use_container_width=True, key=f"q_{q}"):
                st.session_state.pending_user_text = q[2:]  # Enlever l'emoji
                st.rerun()
        
        st.divider()
        
        # Quiz
        st.markdown("### 🎮 Quiz")
        if st.button("🧠 Teste tes connaissances !", use_container_width=True, key="start_quiz"):
            st.session_state.quiz_active = True
            st.session_state.quiz_current = 0
            st.session_state.quiz_score = 0
            st.rerun()
        
        st.divider()
        
        # Raccourcis clavier
        st.markdown("### ⌨️ Raccourcis")
        with st.expander(""):
            st.markdown("""
            **Navigation :**
            - `Enter` → Envoyer message
            - `Ctrl+L` → Focus sur le chat
            
            **Commandes spéciales :**
            - Tape `help` → Aide
            - Tape `42` → Easter egg
            - Tape `matrix` → Surprise !
            """)
        
        st.divider()
        
        # Stats
        st.markdown("### 📊 Stats")
        stats = _get_chat_stats()
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.metric("💬", stats["messages"], label_visibility="collapsed")
            st.caption("Messages")
        with col_s2:
            st.metric("⏱️", stats["duration"], label_visibility="collapsed")
            st.caption("Durée")
        
        col_s3, col_s4 = st.columns(2)
        with col_s3:
            st.caption(f"{'🟢' if _has_openai_key() else '🔴'} OpenAI")
        with col_s4:
            st.caption(f"{'🟢' if _has_upstash_creds() else '🔴'} Upstash")
        
        st.divider()
        
        # Fun Fact
        st.markdown("### 🎲 Fun Fact")
        if st.button("🎰 Nouveau fun fact", use_container_width=True, key="new_fact"):
            st.session_state.current_fun_fact = random.choice(FUN_FACTS)
            st.rerun()
        st.info(st.session_state.get("current_fun_fact", FUN_FACTS[0]))
        
        st.divider()
        
        # Actions
        st.markdown("### 🛠️ Actions")
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🔄 Reset", use_container_width=True, key="reset_btn"):
                _reset_chat()
                st.rerun()
        with col_b:
            st.download_button(
                "📥 Export",
                data=_export_conversation(),
                file_name=f"chat_yvan_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain",
                use_container_width=True,
            )
        
        return DEFAULT_NAMESPACE, response_style


# ═══════════════════════════════════════════════════════════════════════════════
# 🚀 MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    load_dotenv(override=True)
    
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="💬",
        layout="centered",
        initial_sidebar_state="expanded",
    )
    
    _init_session_state()
    apply_custom_css()
    
    # Sidebar
    namespace, response_style = _render_sidebar()
    
    # Header
    st.markdown("# " + APP_TITLE)
    mode_txt = " --recruiter" if st.session_state.get("recruiter_mode") else ""
    st.markdown(f"`[STATUS: ONLINE] [USER: visitor] [MODE: chat{mode_txt}]`")
    
    # Vérifications
    if not _has_openai_key():
        st.error("⚠️ OPENAI_API_KEY manquant. Ajoute-le dans `.env` puis relance.")
        st.stop()
    
    if not _has_upstash_creds():
        st.warning("📡 Upstash non configuré — je peux discuter, mais sans accès à ma mémoire.")
    
    # Quiz (si actif)
    if st.session_state.get("quiz_active", False):
        st.markdown("---")
        _render_quiz()
        st.markdown("---")
    
    # Agent
    agent = build_portfolio_agent(namespace=namespace, response_style=response_style)
    
    # Avatar custom
    avatar_b64 = _get_avatar_base64()
    assistant_avatar = f"data:image/png;base64,{avatar_b64}" if avatar_b64 else "🤖"
    
    # Historique des messages
    for msg in st.session_state.messages:
        if msg["role"] == "assistant":
            with st.chat_message("assistant", avatar=assistant_avatar):
                st.markdown(msg["content"])
        else:
            with st.chat_message("user", avatar="💻"):
                st.markdown(msg["content"])
    
    # Input utilisateur
    typed_text = st.chat_input("Écris ici... 💬")
    user_text = st.session_state.get("pending_user_text") or typed_text
    st.session_state.pending_user_text = None
    
    if not user_text:
        return
    
    # Stats
    st.session_state.chat_stats["questions"] = st.session_state.chat_stats.get("questions", 0) + 1
    
    # Message user
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user", avatar="💻"):
        st.markdown(user_text)
    
    # Easter egg
    easter_egg = _check_easter_egg(user_text)
    if easter_egg:
        with st.chat_message("assistant", avatar=assistant_avatar):
            st.markdown(easter_egg)
        st.session_state.messages.append({"role": "assistant", "content": easter_egg})
        st.rerun()
    
    # Réponse
    with st.chat_message("assistant", avatar=assistant_avatar):
        with st.spinner("> processing..."):
            agent_input = _inject_rag_context(user_text, namespace=namespace)
            result = Runner.run_sync(
                agent,
                agent_input,
                previous_response_id=st.session_state.previous_response_id,
                max_turns=6,
            )
        
        answer = (result.final_output or "").strip()
        if not answer:
            answer = "Hmm, je n'ai pas réussi à formuler une réponse. Tu peux reformuler ?"
        
        st.markdown(answer)
    
    st.session_state.previous_response_id = result.last_response_id
    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun()


if __name__ == "__main__":
    main()
