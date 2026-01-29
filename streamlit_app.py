"""
Interface Streamlit — Chatbot conversationnel portfolio.
Sans CSS ni HTML personnalisé, uniquement les composants natifs Streamlit.
"""

from __future__ import annotations
import json
import os
import random
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st
from dotenv import load_dotenv
from agents import Runner
from portfolio.agent import build_portfolio_agent
from portfolio.rag import format_context, search_portfolio


# Constantes de l'appli

TITRE_APP = "Portfolio Yvan NEDELEC"
NAMESPACE = "portfolio"
VERSION = "2026-01-15-v12"

LIENS = {
    "github": "https://github.com/yvan-nedelec-etu",
    "linkedin": "https://www.linkedin.com/in/yvan-nedelec-40b779214/",
    "email": "yvan.nedelec@etu.univ-poitiers.fr",
}

SUGGESTIONS = [
    "Quels sont tes projets ?",
    "Parle-moi de ton alternance",
    "Quelles compétences maîtrises-tu ?",
    "C'est quoi ton parcours ?",
]

MESSAGE_REMERCIEMENT = f"""---

**Merci d'avoir discuté avec moi !** 🙏

Si vous souhaitez en savoir plus ou me contacter :

• 🐙 GitHub : {LIENS['github']}
• 💼 LinkedIn : {LIENS['linkedin']}
• 📧 Email : {LIENS['email']}

---
"""

ANECDOTES = [
    "💡 J'ai appris Python en autodidacte avant de commencer mon BUT !",
    "🎵 Je produis de la musique électronique sur FL Studio à mes heures perdues.",
    "🏋️ Je pratique la musculation régulièrement pour garder un équilibre.",
    "🚗 Passionné d'automobile, j'apprécie particulièrement les modèles anciens.",
    "💻 Mon premier projet était un site web complet en PHP/JavaScript.",
    "📊 À la MAIF, je participe à la migration de traitements SAS vers Python.",
    "🎯 Objectif : devenir expert en Machine Learning ou Data Engineering.",
]

QUIZ = [
    {"q": "Dans quelle entreprise je fais mon alternance ?", "opts": ["AXA", "MAIF", "Groupama", "Allianz"], "rep": 1},
    {"q": "Quel langage j'utilise le plus en data ?", "opts": ["Java", "C++", "Python", "Ruby"], "rep": 2},
    {"q": "Quelle formation je suis actuellement ?", "opts": ["Master IA", "BUT Science des Données", "École d'ingénieur", "Licence Info"], "rep": 1},
    {"q": "Quel outil j'utilise pour coder ?", "opts": ["IntelliJ", "VS Code", "PyCharm", "Visual Studio"], "rep": 2},
]

MESSAGE_ACCUEIL = """Bonjour, je suis **Yvan NEDELEC**.

Étudiant en BUT Science des Données à l'IUT de Niort, je suis actuellement en alternance en tant que Data Analyst à la MAIF.

Posez-moi vos questions sur mon parcours, mes projets ou mes compétences.

Je peux aussi vous proposer un quiz pour tester vos connaissances sur moi ! Tapez 'quiz' pour commencer.


"""


# Sauvegarde simple des conversations (JSON local)

DATA_DIR = Path("data")
CONV_FILE = DATA_DIR / "conversations.json"


def charger_conversations() -> dict:
    """Charge toutes les conversations sauvegardées depuis le fichier JSON.

    Returns:
        dict: Dictionnaire des conversations indexées par identifiant.
    """
    DATA_DIR.mkdir(exist_ok=True)
    if CONV_FILE.exists():
        try:
            with CONV_FILE.open("r", encoding="utf-8") as f:
                convs = json.load(f)
            for conv in convs.values():
                stats = conv.get("stats")
                if stats and isinstance(stats.get("debut"), str):
                    try:
                        stats["debut"] = datetime.fromisoformat(stats["debut"])
                    except ValueError:
                        stats["debut"] = datetime.now()
            return convs
        except json.JSONDecodeError:
            return {}
    return {}


def sauver_conversations(convs: dict) -> None:
    """Sauvegarde toutes les conversations dans le fichier JSON.

    Args:
        convs (dict): Conversations à persister.

    Returns:
        None
    """
    DATA_DIR.mkdir(exist_ok=True)
    convs_serializables = {}
    for cid, conv in convs.items():
        stats = conv.get("stats", {})
        debut = stats.get("debut")
        stats_serializables = dict(stats)
        if isinstance(debut, datetime):
            stats_serializables["debut"] = debut.isoformat()
        convs_serializables[cid] = {
            "messages": conv.get("messages", []),
            "previous_response_id": conv.get("previous_response_id"),
            "stats": stats_serializables,
        }
    with CONV_FILE.open("w", encoding="utf-8") as f:
        json.dump(convs_serializables, f, ensure_ascii=False, indent=2)


def nouvelle_conversation_id() -> str:
    """Génère un identifiant simple pour une nouvelle conversation.

    Returns:
        str: Identifiant unique basé sur la date et l'heure.
    """
    return datetime.now().strftime("%Y%m%d-%H%M%S")


# Fonctions utilitaires

def initialiser_session() -> None:
    """Initialise les variables de session Streamlit.

    Returns:
        None
    """
    defauts = {
        "version": None,
        "previous_response_id": None,
        "messages": [],
        "quiz_actif": False,
        "quiz_index": 0,
        "quiz_score": 0,
        "stats": {"questions": 0, "debut": datetime.now()},
        "conversation_id": None,
    }
    for cle, val in defauts.items():
        if cle not in st.session_state:
            st.session_state[cle] = val
    
    if st.session_state.version != VERSION:
        st.session_state.version = VERSION
        st.session_state.previous_response_id = None
        st.session_state.messages = [{"role": "assistant", "content": MESSAGE_ACCUEIL}]
        if not st.session_state.conversation_id:
            st.session_state.conversation_id = nouvelle_conversation_id()


def obtenir_stats() -> str:
    """Retourne les statistiques de conversation formatées.

    Returns:
        str: Texte synthétique des stats de session.
    """
    stats = st.session_state.stats
    duree = datetime.now() - stats["debut"]
    mins = int(duree.total_seconds() // 60)
    secs = int(duree.total_seconds() % 60)
    nb_messages = len(st.session_state.messages)
    nb_questions = stats["questions"]
    return f"💬 {nb_messages} messages • ❓ {nb_questions} questions • ⏱️ {mins}m {secs}s"


# Gestion des commandes et du quiz

def gerer_quiz(texte: str) -> str | None:
    """Gère les réponses au quiz en cours.

    Args:
        texte (str): Message utilisateur (potentielle réponse).

    Returns:
        str | None: Réponse à afficher, ou None si le quiz est terminé.
    """
    idx = st.session_state.quiz_index
    if idx >= len(QUIZ):
        st.session_state.quiz_actif = False
        return None
    
    q = QUIZ[idx]
    reponse = None
    
    # Chercher un numéro dans la réponse
    for i, num in enumerate(["1", "2", "3", "4"]):
        if num in texte:
            reponse = i
            break
    
    # Sinon chercher le texte de l'option
    if reponse is None:
        for i, opt in enumerate(q["opts"]):
            if opt.lower() in texte:
                reponse = i
                break
    
    if reponse is None:
        return f"💬 *Répondez avec* **1**, **2**, **3** *ou* **4**\n\n**Rappel :** *{q['q']}*"
    
    # Vérifier si la réponse est correcte
    correct = reponse == q["rep"]
    if correct:
        st.session_state.quiz_score += 1
    
    feedback = "✅ **Correct !**" if correct else f"❌ **Incorrect** — La bonne réponse était : *{q['opts'][q['rep']]}*"
    
    st.session_state.quiz_index += 1
    
    # Quiz terminé ?
    if st.session_state.quiz_index >= len(QUIZ):
        st.session_state.quiz_actif = False
        score = st.session_state.quiz_score
        total = len(QUIZ)
        
        if score == total:
            appreciation = "🏆 **Parfait !** Vous me connaissez par cœur !"
        elif score >= 3:
            appreciation = "🎉 **Excellent !** Très bonne connaissance de mon profil."
        elif score >= 2:
            appreciation = "👍 **Bien joué !** Vous avez retenu l'essentiel."
        else:
            appreciation = "💪 **Continuez à explorer** mon portfolio pour en apprendre plus !"
        
        return f"{feedback}\n\n---\n\n**🎯 Quiz terminé**\n\n**Score final : {score}/{total}**\n\n{appreciation}\n\n---\n*Tapez 'quiz' pour rejouer*"
    
    # Question suivante
    question_suivante = QUIZ[st.session_state.quiz_index]
    options = "\n".join([f"  **{i+1}.** {o}" for i, o in enumerate(question_suivante["opts"])])
    return f"{feedback}\n\n---\n\n**Question {st.session_state.quiz_index + 1}/{len(QUIZ)}**\n\n*{question_suivante['q']}*\n\n{options}"


def detecter_commande(texte: str) -> str | None:
    """Détecte et exécute les commandes spéciales.

    Args:
        texte (str): Message utilisateur.

    Returns:
        str | None: Réponse si une commande est reconnue, sinon None.
    """
    t = texte.lower().strip()
    
    # Petites réponses fun
    if "42" in t:
        return "🌌 **42** — *La réponse à la grande question sur la vie, l'univers et le reste.*"
    
    if "matrix" in t:
        return "💊 *Wake up, Neo... The Matrix has you.* — Pilule rouge ou bleue ?"
    
    if "hello world" in t:
        return "👨‍💻 `print('Hello, World!')` — Mon tout premier programme était en PHP, en 2020."
    
    if "konami" in t:
        return "🎮 **↑ ↑ ↓ ↓ ← → ← → B A** — Le légendaire Konami Code !"
    
    # Commandes simples
    if t in ["help", "aide", "?"]:
        return MESSAGE_ACCUEIL
    
    if any(x in t for x in ["github", "git", "repo"]):
        return f"🐙 **GitHub** → {LIENS['github']}"
    
    if any(x in t for x in ["linkedin", "profil pro"]):
        return f"💼 **LinkedIn** → {LIENS['linkedin']}"
    
    if any(x in t for x in ["liens", "réseaux", "contact"]):
        return f"**🔗 Mes réseaux professionnels**\n\n• 🐙 GitHub : {LIENS['github']}\n• 💼 LinkedIn : {LIENS['linkedin']}"
    
    if any(x in t for x in ["fun fact", "anecdote", "truc marrant"]):
        return f"**✨ Le saviez-vous ?**\n\n{random.choice(ANECDOTES)}"
    
    if any(x in t for x in ["stats", "statistiques"]):
        return f"**📈 Statistiques de session**\n\n{obtenir_stats()}"
    
    if any(x in t for x in ["reset", "recommencer", "effacer"]):
        st.session_state.previous_response_id = None
        st.session_state.messages = [{"role": "assistant", "content": MESSAGE_ACCUEIL}]
        st.session_state.stats = {"questions": 0, "debut": datetime.now()}
        st.session_state.quiz_actif = False
        st.rerun()
    
    if any(x in t for x in ["quiz", "quizz", "teste"]):
        st.session_state.quiz_actif = True
        st.session_state.quiz_index = 0
        st.session_state.quiz_score = 0
        q = QUIZ[0]
        options = "\n".join([f"  **{i+1}.** {o}" for i, o in enumerate(q["opts"])])
        return f"🎯 **Quiz lancé !**\n\n---\n\n**Question 1/{len(QUIZ)}**\n\n*{q['q']}*\n\n{options}\n\n---\n💬 *Répondez avec 1, 2, 3 ou 4*"
    
    # Si un quiz est lancé, on traite la réponse
    if st.session_state.get("quiz_actif"):
        return gerer_quiz(t)
    
    return None


def injecter_contexte_rag(texte: str) -> str:
    """Ajoute le contexte RAG à la question utilisateur.

    Args:
        texte (str): Question de l'utilisateur.

    Returns:
        str: Question enrichie avec du contexte si disponible.
    """
    try:
        chunks = search_portfolio(texte, top_k=8, namespace=NAMESPACE)
        ctx = format_context(chunks, max_items=8)
        if ctx.strip():
            return f"Infos sur moi:\n{ctx}\n\nQuestion:\n{texte}"
        return texte
    except Exception:
        return texte


def sauvegarder_conversation_en_cours() -> None:
    """Sauvegarde la conversation en cours dans le JSON.

    Returns:
        None
    """
    convs = charger_conversations()
    convs[st.session_state.conversation_id] = {
        "messages": st.session_state.messages,
        "previous_response_id": st.session_state.previous_response_id,
        "stats": st.session_state.stats,
    }
    sauver_conversations(convs)


def appliquer_theme() -> None:
    """Applique le thème CSS de l'application.

    Returns:
        None
    """
    st.markdown("""
        <style>
        /* Fond général */
        .stApp { background: linear-gradient(180deg, #1f1f1f 0%, #171717 100%); }
        
        /* Bulles de chat */
        .stChatMessage {
            background: transparent !important;
            border: none !important;
            padding: 1rem 0 !important;
        }
        [data-testid="stChatMessageContent"] {
            background: #2d2d2d !important;
            border-radius: 18px !important;
            padding: 16px 20px !important;
            border: 1px solid #3d3d3d !important;
        }
        
        /* Input */
        .stChatInput > div {
            background: #2d2d2d !important;
            border-radius: 24px !important;
            border: 1px solid #3d3d3d !important;
        }
        .stChatInput input {
            background: transparent !important;
        }
        
        /* Titre et texte secondaire */
        h1 {
            font-weight: 400 !important;
            font-size: 1.8rem !important;
            color: #e3e3e3 !important;
        }
        .stCaption {
            color: #9aa0a6 !important;
            font-size: 0.85rem !important;
        }
        
        /* Liens */
        a { color: #8ab4f8 !important; }
        a:hover { color: #aecbfa !important; }
        
        /* On cache le branding Streamlit */
        #MainMenu, footer, header { visibility: hidden; }
        </style>
    """, unsafe_allow_html=True)


def afficher_sidebar_historique() -> None:
    """Affiche la sidebar et gère la reprise de conversations.

    Returns:
        None
    """
    with st.sidebar:
        st.subheader("Historique")
        convs = charger_conversations()

        if convs:
            choix = st.selectbox("Reprendre une conversation", ["(nouvelle)"] + list(convs.keys()))
            if choix != "(nouvelle)" and choix != st.session_state.conversation_id:
                st.session_state.conversation_id = choix
                st.session_state.messages = convs[choix]["messages"]
                st.session_state.previous_response_id = convs[choix].get("previous_response_id")
                st.session_state.stats = convs[choix].get("stats", st.session_state.stats)
                st.rerun()

        if st.button("Nouvelle conversation"):
            st.session_state.conversation_id = nouvelle_conversation_id()
            st.session_state.previous_response_id = None
            st.session_state.messages = [{"role": "assistant", "content": MESSAGE_ACCUEIL}]
            st.session_state.stats = {"questions": 0, "debut": datetime.now()}
            st.rerun()


def afficher_entete() -> None:
    """Affiche le titre et la description courte.

    Returns:
        None
    """
    st.title(TITRE_APP)
    st.caption("BUT Science des Données - Alternant Data Analyst MAIF")


def verifier_cle_api() -> None:
    """Arrête l'application si la clé API est absente.

    Returns:
        None
    """
    if not os.getenv("OPENAI_API_KEY"):
        st.error("OPENAI_API_KEY manquant dans le fichier .env")
        st.stop()


def afficher_messages() -> None:
    """Affiche l'historique des messages de la session.

    Returns:
        None
    """
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])


def afficher_remerciement_si_necessaire() -> None:
    """Affiche un message après un certain nombre de questions.

    Returns:
        None
    """
    nb_questions = st.session_state.stats["questions"]
    if nb_questions >= 5 and nb_questions % 5 == 0:
        st.markdown(MESSAGE_REMERCIEMENT)


def afficher_suggestions() -> None:
    """Affiche des suggestions si la conversation débute.

    Returns:
        None
    """
    if len(st.session_state.messages) <= 2:
        st.markdown("**💡 Suggestions :**")
        cols = st.columns(2)
        for i, suggestion in enumerate(SUGGESTIONS):
            if cols[i % 2].button(suggestion, key=f"sugg_{i}"):
                st.session_state.suggestion_cliquee = suggestion
                st.rerun()


def lire_message_utilisateur() -> str | None:
    """Lit le message de l'utilisateur ou une suggestion cliquée.

    Returns:
        str | None: Message à traiter, ou None si rien n'est saisi.
    """
    texte = st.chat_input("Pose-moi une question, lance un quiz, demande mes liens...")
    if st.session_state.get("suggestion_cliquee"):
        texte = st.session_state.suggestion_cliquee
        st.session_state.suggestion_cliquee = None
    return texte


def traiter_message_utilisateur(texte: str, agent: Any) -> None:
    """Traite un message utilisateur et met à jour l'UI.

    Args:
        texte (str): Message utilisateur.
        agent (Any): Agent de génération de réponses.

    Returns:
        None
    """
    st.session_state.messages.append({"role": "user", "content": texte})
    with st.chat_message("user"):
        st.markdown(texte)

    reponse_commande = detecter_commande(texte)
    if reponse_commande:
        with st.chat_message("assistant"):
            st.markdown(reponse_commande)
        st.session_state.messages.append({"role": "assistant", "content": reponse_commande})
        sauvegarder_conversation_en_cours()
        st.rerun()

    st.session_state.stats["questions"] += 1

    with st.chat_message("assistant"):
        with st.spinner("Je réfléchis..."):
            texte_enrichi = injecter_contexte_rag(texte)
            result = Runner.run_sync(
                agent,
                texte_enrichi,
                previous_response_id=st.session_state.previous_response_id,
                max_turns=6
            )

        reponse = (result.final_output or "").strip()
        if not reponse:
            reponse = "Hmm, je n'ai pas compris. Tape 'help' pour voir ce que je peux faire !"
        st.markdown(reponse)

    st.session_state.previous_response_id = result.last_response_id
    st.session_state.messages.append({"role": "assistant", "content": reponse})
    sauvegarder_conversation_en_cours()
    st.rerun()


# Point d'entrée

def main() -> None:
    """Point d'entrée principal de l'application.

    Returns:
        None
    """
    load_dotenv(override=True)
    
    st.set_page_config(
        page_title="Portfolio Yvan NEDELEC",
        page_icon="Y",
        layout="centered"
    )

    appliquer_theme()
    initialiser_session()
    afficher_sidebar_historique()
    afficher_entete()
    verifier_cle_api()

    agent = build_portfolio_agent(namespace=NAMESPACE, style_reponse="concis")

    afficher_messages()
    afficher_remerciement_si_necessaire()
    afficher_suggestions()

    texte = lire_message_utilisateur()
    if texte:
        traiter_message_utilisateur(texte, agent)


if __name__ == "__main__":
    main()
