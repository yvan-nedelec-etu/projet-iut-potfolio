"""
Découpage des documents Markdown pour l'indexation RAG.

Ce module transforme des fichiers Markdown en morceaux de texte (chunks)
optimisés pour la recherche vectorielle.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path


def charger_fichiers_markdown(dossier: str = "data") -> list[Path]:
    """
    Récupère tous les fichiers Markdown d'un dossier.

    Args:
        dossier: Chemin vers le dossier contenant les fichiers .md.

    Returns:
        Liste triée des chemins vers les fichiers trouvés.
    """
    return sorted(Path(dossier).rglob("*.md"))


def generer_id(source: str, titre: str, index: int) -> str:
    """
    Génère un identifiant unique pour un chunk.

    Args:
        source: Chemin du fichier source.
        titre: Titre de la section.
        index: Numéro du chunk dans la section.

    Returns:
        Identifiant de 20 caractères.
    """
    texte = f"{source}|{titre}|{index}"
    return hashlib.sha1(texte.encode()).hexdigest()[:20]


def decouper_markdown(texte: str, source: str, max_chars: int = 1000) -> list[dict]:
    """
    Découpe un document Markdown en chunks.

    Args:
        texte: Contenu du fichier Markdown.
        source: Chemin relatif du fichier.
        max_chars: Taille maximale d'un chunk.

    Returns:
        Liste de dictionnaires avec id, text et metadata.
    """
    lignes = texte.splitlines()
    regex_titre = re.compile(r"^(#{1,6})\s+(.*)$")
    
    # Extraction des sections
    titres: list[str] = []
    buffer: list[str] = []
    sections: list[tuple[str, str]] = []

    for ligne in lignes:
        match = regex_titre.match(ligne)
        if match:
            if buffer:
                chemin = " > ".join(titres) if titres else "Introduction"
                sections.append((chemin, "\n".join(buffer).strip()))
                buffer = []
            niveau = len(match.group(1))
            titres = titres[:niveau-1] + [match.group(2).strip()]
        else:
            buffer.append(ligne)
    
    if buffer:
        chemin = " > ".join(titres) if titres else "Introduction"
        sections.append((chemin, "\n".join(buffer).strip()))

    # Création des chunks
    chunks: list[dict] = []
    
    for chemin_titre, contenu in sections:
        if not contenu.strip():
            continue
            
        paragraphes = [p.strip() for p in re.split(r"\n\s*\n", contenu) if p.strip()]
        bloc = ""
        index = 0
        
        for para in paragraphes:
            if bloc and len(bloc) + len(para) + 2 > max_chars:
                chunks.append({
                    "id": generer_id(source, chemin_titre, index),
                    "text": f"{chemin_titre}\n\n{bloc}",
                    "metadata": {"source": source, "heading": chemin_titre}
                })
                index += 1
                bloc = ""
            
            bloc = f"{bloc}\n\n{para}".strip() if bloc else para
        
        if bloc:
            chunks.append({
                "id": generer_id(source, chemin_titre, index),
                "text": f"{chemin_titre}\n\n{bloc}",
                "metadata": {"source": source, "heading": chemin_titre}
            })

    return chunks


def decouper_tous_les_fichiers(dossier: str = "data", max_chars: int = 1000) -> list[dict]:
    """
    Découpe tous les fichiers Markdown d'un dossier.

    Args:
        dossier: Chemin vers le dossier racine.
        max_chars: Taille maximale d'un chunk.

    Returns:
        Liste de tous les chunks (dictionnaires).
    """
    base = Path(dossier)
    chunks: list[dict] = []
    
    for fichier in charger_fichiers_markdown(dossier):
        texte = fichier.read_text(encoding="utf-8")
        source = str(fichier.relative_to(base)).replace("\\", "/")
        chunks.extend(decouper_markdown(texte, source, max_chars))
    
    return chunks


# Alias 
load_markdown_files = charger_fichiers_markdown
chunk_markdown = decouper_markdown
chunk_markdown_files = decouper_tous_les_fichiers