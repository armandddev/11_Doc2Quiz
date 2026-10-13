"""TemplateProfil.py
Fichier contenant UNIQUEMENT les gabarits HTML bruts avec des marqueurs de variables.
"""

# Template 1 : En-tête du profil
TEMPLATE_ENTETE = """
<div class="card-profil entete-profil">
    <div class="avatar-profil">{initiales}</div>
    <div class="infos-utilisateur">
        <div class="nom-user">{nom}</div>
        <div class="filiere-user">{formation} - {etablissement}</div>
        <div class="meta-user">Membre depuis {date_inscription} - {nb_sessions} sessions</div>
    </div>
    <button class="btn-modifier-profil">Modifier</button>
</div>
"""

# Template 2 : Une ligne de compétence
TEMPLATE_LIGNE_COMPETENCE = """
<div class="item-competence">
    <div class="header-competence">
        <span class="titre-domaine">{domaine}</span>
        <span class="pct-domaine" style="color: {couleur};">{score} %</span>
    </div>
    <div class="barre-fond">
        <div class="barre-progression" style="width: {score}%; background-color: {couleur};"></div>
    </div>
</div>
"""

# Template 2 (conteneur global) : Section compétences
TEMPLATE_COMPETENCES_WRAPPER = """
<div class="card-profil">
    <div class="titre-section">Compétences par domaine</div>
    <div class="liste-competences">
        {lignes_competences}
    </div>
</div>
"""