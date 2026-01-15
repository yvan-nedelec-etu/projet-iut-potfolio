"""
Interface Streamlit
Chatbot conversationnel.
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
#                                 CONSTANTES
# ═══════════════════════════════════════════════════════════════════════════════

TITRE_APP = "yvan@portfolio:~$ ./chat"
NAMESPACE = "portfolio"
VERSION = "2026-01-15-v8"

LIENS = {
    "github": "https://github.com/yvan-nedelec-etu",
    "linkedin": "https://www.linkedin.com/in/yvan-nedelec-40b779214/",
}

ANECDOTES = [
    "💡 J'ai appris Python en autodidacte avant de commencer mon BUT !",
    "🎵 Je produis de la musique sur FL Studio à mes heures perdues.",
    "🏋️ Je fais de la musculation pour garder la forme.",
    "🚗 Je suis passionné par l'automobile, surtout les modèles anciens.",
    "💻 Mon premier projet était un site web en PHP/JavaScript.",
    "📊 À la MAIF, je migre des traitements SAS vers Python.",
    "🎯 Mon objectif : devenir expert en Machine Learning ou Data Engineering.",
]

QUIZ = [
    {"q": "Dans quelle entreprise je fais mon alternance ?", "opts": ["AXA", "MAIF", "Groupama", "Allianz"], "rep": 1},
    {"q": "Quel langage j'utilise le plus en data ?", "opts": ["Java", "C++", "Python", "Ruby"], "rep": 2},
    {"q": "Quelle formation je suis actuellement ?", "opts": ["Master IA", "BUT Science des Données", "École d'ingénieur", "Licence Info"], "rep": 1},
    {"q": "Quel outil j'utilise pour produire de la musique ?", "opts": ["Ableton", "FL Studio", "Logic Pro", "GarageBand"], "rep": 1},
]

MESSAGE_ACCUEIL = f"""```
> Connexion établie...
> Terminal Yvan NEDELEC v2.0
> Initialisation...
```

Salut ! 👋 Je suis **Yvan**, étudiant en **BUT Science des Données** et alternant **Data Analyst à la MAIF**.

### Ce que je peux faire :

🔹 Réponds à tes questions sur mes **projets**, mon **alternance**, mes **compétences**
🔹 Donne mes liens : **GitHub**, **LinkedIn**
🔹 Lance un **quiz** pour tester tes connaissances sur moi
🔹 Partage des **anecdotes** (fun fact)
🔹 Easter eggs : `42`, `matrix`, `hello world`, `konami`

---
*Exemples : "C'est quoi ton GitHub ?", "On fait un quiz ?", "Parle-moi de tes projets"*
"""

CSS_TERMINAL = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&display=swap');
* { font-family: 'Fira Code', monospace !important; }

.stApp, .main, [data-testid="stAppViewContainer"], [data-testid="stVerticalBlock"],
[data-testid="stMainBlockContainer"], .block-container {
    background: #0a0a0a !important;
}
.stApp {
    background-image: radial-gradient(ellipse at top, #0d1a0d 0%, #0a0a0a 50%),
        repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,255,65,0.02) 2px, rgba(0,255,65,0.02) 4px) !important;
}
.stBottom, [data-testid="stBottom"], [data-testid="stBottomBlockContainer"],
.stChatInputContainer, [data-testid="stChatInput"], [data-testid="stChatInput"] > div,
div[data-testid="stBottom"] > div {
    background: #0a0a0a !important; border: none !important;
}
section[data-testid="stSidebar"] { display: none !important; }
.stMarkdown, .stText, p, span, label, .stCaption, [data-testid="stMarkdownContainer"] p {
    color: #00ff41 !important; text-shadow: 0 0 3px rgba(0,255,65,0.4);
}
h1, h2, h3, h4 {
    color: #00ff41 !important;
    text-shadow: 0 0 10px rgba(0,255,65,0.7), 0 0 20px rgba(0,255,65,0.4) !important;
}
.stChatMessage {
    background: rgba(0,20,0,0.9) !important; border: 1px solid #00ff41 !important;
    border-radius: 0 !important; margin: 12px 0 !important; padding: 15px !important;
    box-shadow: 0 0 10px rgba(0,255,65,0.2);
}
.stChatMessage [data-testid="stMarkdownContainer"] p { margin-bottom: 8px !important; line-height: 1.6 !important; }
.stButton > button {
    background: transparent !important; border: 1px solid #00ff41 !important;
    color: #00ff41 !important; border-radius: 0 !important; text-transform: uppercase;
}
.stButton > button:hover {
    background: #00ff41 !important; color: #0a0a0a !important;
    box-shadow: 0 0 20px rgba(0,255,65,0.6);
}
.stChatInput, .stChatInput > div, [data-testid="stChatInputTextArea"], .stChatInput textarea,
.stChatInput input {
    background: #0a0a0a !important; border: 1px solid #00ff41 !important;
    border-radius: 0 !important; color: #00ff41 !important; caret-color: #00ff41 !important;
}
.stChatInput input::placeholder, .stChatInput textarea::placeholder { color: rgba(0,255,65,0.5) !important; }
a { color: #00ff41 !important; }
#MainMenu, footer, [data-testid="stToolbar"] { visibility: hidden; }
header[data-testid="stHeader"] { display: none !important; }
.stChatMessage img { border-radius: 4px !important; border: 1px solid #00ff41 !important; }
</style>
"""


# ═══════════════════════════════════════════════════════════════════════════════
#                              FONCTIONS UTILITAIRES
# ═══════════════════════════════════════════════════════════════════════════════

def charger_avatar() -> str | None:
    """Charge l'avatar PNG encodé en base64."""
    chemin = Path("assets/avatar.png")
    return base64.b64encode(chemin.read_bytes()).decode() if chemin.exists() else None


def initialiser_session() -> None:
    """Initialise les variables de session Streamlit."""
    defauts = {
        "version": None, "previous_response_id": None, "messages": [],
        "quiz_actif": False, "quiz_index": 0, "quiz_score": 0,
        "stats": {"questions": 0, "debut": datetime.now()},
    }
    for cle, val in defauts.items():
        if cle not in st.session_state:
            st.session_state[cle] = val
    
    if st.session_state.version != VERSION:
        st.session_state.version = VERSION
        st.session_state.previous_response_id = None
        st.session_state.messages = [{"role": "assistant", "content": MESSAGE_ACCUEIL}]


def obtenir_stats() -> str:
    """Retourne les statistiques de conversation formatées."""
    stats = st.session_state.stats
    duree = datetime.now() - stats["debut"]
    mins, secs = int(duree.total_seconds() // 60), int(duree.total_seconds() % 60)
    return f"💬 {len(st.session_state.messages)} messages • ❓ {stats['questions']} questions • ⏱️ {mins}m {secs}s"


# ═══════════════════════════════════════════════════════════════════════════════
#                           GESTION DES COMMANDES
# ═══════════════════════════════════════════════════════════════════════════════

def gerer_quiz(texte: str) -> str | None:
    """Gère les réponses au quiz en cours."""
    idx = st.session_state.quiz_index
    if idx >= len(QUIZ):
        st.session_state.quiz_actif = False
        return None
    
    q = QUIZ[idx]
    reponse = None
    
    for i, num in enumerate(["1", "2", "3", "4"]):
        if num in texte:
            reponse = i
            break
    if reponse is None:
        for i, opt in enumerate(q["opts"]):
            if opt.lower() in texte:
                reponse = i
                break
    
    if reponse is None:
        return f"🤔 Réponds avec **1**, **2**, **3** ou **4** !\n\n**Rappel :** {q['q']}"
    
    correct = reponse == q["rep"]
    if correct:
        st.session_state.quiz_score += 1
    feedback = "✅ **Bonne réponse !**" if correct else f"❌ **Raté !** C'était : **{q['opts'][q['rep']]}**"
    
    st.session_state.quiz_index += 1
    
    if st.session_state.quiz_index >= len(QUIZ):
        st.session_state.quiz_actif = False
        score, total = st.session_state.quiz_score, len(QUIZ)
        emoji = "🏆" if score == total else "🎉" if score >= 3 else "👍" if score >= 2 else "💪"
        return f"{feedback}\n\n---\n\n{emoji} **Quiz terminé ! Score : {score}/{total}**\n\n*Tape 'quiz' pour rejouer !*"
    
    nq = QUIZ[st.session_state.quiz_index]
    opts = "\n".join([f"**{i+1}.** {o}" for i, o in enumerate(nq["opts"])])
    return f"{feedback}\n\n---\n\n**Question {st.session_state.quiz_index + 1}/{len(QUIZ)} :**\n{nq['q']}\n\n{opts}"


def detecter_commande(texte: str) -> str | None:
    """Détecte et exécute les commandes spéciales."""
    t = texte.lower().strip()
    
    # Easter eggs
    if "42" in t:
        return "🌌 **42** — La réponse à la grande question sur la vie, l'univers et le reste !"
    if "matrix" in t:
        return "💊 **Pilule rouge** ou **bleue** ?\n\n```\nWake up, Neo...\nThe Matrix has you...\n```"
    if "hello world" in t:
        return "```python\nprint('Hello, World!')\n```\n\n👨‍💻 Mon premier hello world était en PHP en 2020."
    if "konami" in t:
        return "🎮 **↑ ↑ ↓ ↓ ← → ← → B A** — Tu connais le Konami Code !"
    
    # Commandes
    if t in ["help", "aide", "?"]:
        return MESSAGE_ACCUEIL
    if any(x in t for x in ["github", "git", "repo"]):
        return f"🐙 **Mon GitHub :** [{LIENS['github']}]({LIENS['github']})"
    if any(x in t for x in ["linkedin", "profil pro"]):
        return f"💼 **Mon LinkedIn :** [{LIENS['linkedin']}]({LIENS['linkedin']})"
    if any(x in t for x in ["liens", "réseaux", "contact"]):
        return f"🔗 **Mes liens :**\n\n- 🐙 [{LIENS['github']}]({LIENS['github']})\n- 💼 [{LIENS['linkedin']}]({LIENS['linkedin']})"
    if any(x in t for x in ["fun fact", "anecdote", "truc marrant"]):
        return f"🎲 **Fun fact :**\n\n{random.choice(ANECDOTES)}"
    if any(x in t for x in ["stats", "statistiques"]):
        return f"📊 **Stats :**\n\n{obtenir_stats()}"
    if any(x in t for x in ["reset", "recommencer", "effacer"]):
        st.session_state.previous_response_id = None
        st.session_state.messages = [{"role": "assistant", "content": MESSAGE_ACCUEIL}]
        st.session_state.stats = {"questions": 0, "debut": datetime.now()}
        st.session_state.quiz_actif = False
        st.rerun()
    if any(x in t for x in ["quiz", "quizz", "teste"]):
        st.session_state.quiz_actif, st.session_state.quiz_index, st.session_state.quiz_score = True, 0, 0
        q = QUIZ[0]
        opts = "\n".join([f"**{i+1}.** {o}" for i, o in enumerate(q["opts"])])
        return f"🎮 **Quiz lancé !**\n\n**Question 1/{len(QUIZ)} :**\n{q['q']}\n\n{opts}\n\n*Réponds avec 1, 2, 3 ou 4*"
    
    if st.session_state.get("quiz_actif"):
        return gerer_quiz(t)
    
    return None


def injecter_contexte_rag(texte: str) -> str:
    """Ajoute le contexte RAG à la question utilisateur."""
    try:
        chunks = search_portfolio(texte, top_k=8, namespace=NAMESPACE)
        ctx = format_context(chunks, max_items=8)
        return f"Infos sur moi:\n{ctx}\n\nQuestion:\n{texte}" if ctx.strip() else texte
    except Exception:
        return texte


# ═══════════════════════════════════════════════════════════════════════════════
#                                    MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    """Point d'entrée principal de l'application."""
    load_dotenv(override=True)
    
    st.set_page_config(page_title=TITRE_APP, page_icon="💻", layout="centered")
    initialiser_session()
    st.markdown(CSS_TERMINAL, unsafe_allow_html=True)
    
    st.markdown(f"# {TITRE_APP}")
    st.markdown("`[STATUS: ONLINE] [MODE: conversational]`")
    
    if not os.getenv("OPENAI_API_KEY"):
        st.error("OPENAI_API_KEY manquant dans `.env`")
        st.stop()
    
    agent = build_portfolio_agent(namespace=NAMESPACE, style_reponse="concis")
    avatar_b64 = charger_avatar()
    avatar_bot = f"data:image/png;base64,{avatar_b64}" if avatar_b64 else "🤖"
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar=avatar_bot if msg["role"] == "assistant" else "💻"):
            st.markdown(msg["content"])
    
    if texte := st.chat_input("Pose-moi une question, lance un quiz, demande mes liens..."):
        st.session_state.stats["questions"] += 1
        st.session_state.messages.append({"role": "user", "content": texte})
        
        with st.chat_message("user", avatar="💻"):
            st.markdown(texte)
        
        if reponse := detecter_commande(texte):
            with st.chat_message("assistant", avatar=avatar_bot):
                st.markdown(reponse)
            st.session_state.messages.append({"role": "assistant", "content": reponse})
            st.rerun()
        
        with st.chat_message("assistant", avatar=avatar_bot):
            with st.spinner("> processing..."):
                result = Runner.run_sync(
                    agent, injecter_contexte_rag(texte),
                    previous_response_id=st.session_state.previous_response_id, max_turns=6
                )
            reponse = (result.final_output or "").strip() or "Hmm, je n'ai pas compris. Tape `help` pour voir ce que je peux faire !"
            st.markdown(reponse)
        
        st.session_state.previous_response_id = result.last_response_id
        st.session_state.messages.append({"role": "assistant", "content": reponse})
        st.rerun()


if __name__ == "__main__":
    main()