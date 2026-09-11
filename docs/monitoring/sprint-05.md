# Sprint 5 — Semaine 10 : Stabilisation & recette

**Objectif** : valider les 3 niveaux de bout en bout et sécuriser la qualité logicielle.

---

## US-31 : Tests unitaires (5 pts)

En tant qu'équipe, je veux des **tests unitaires sur les modules critiques** afin de sécuriser les évolutions.

**CA :**

- Couverture ≥ 60 % sur : parsing, génération JSON, anti-verbatim, anti-répétition, correction persistante (US-22), export.
- Tests exécutés automatiquement en CI à chaque push.

**Sous-tâches techniques :**

1. Choix du framework (`pytest`) et configuration de la couverture (`pytest-cov`).
2. Priorisation des modules à tester en premier : parsing (US-05/06/07), validation JSON (US-12), anti-verbatim (US-14/21), anti-répétition (US-27), export (US-28/29).
3. Mock systématique des appels Ollama dans les tests (jamais de dépendance à un serveur réel en CI).

**Cas à tester :** cas limites déjà identifiés dans les US précédentes (PDF scanné, JSON invalide, etc.) — bonne occasion de centraliser tous les tests déjà écrits au fil des sprints.

**Definition of Done :** couverture ≥ 60 % mesurée et affichée en CI, badge de couverture dans le README.

---

## US-32 : CI (2 pts)

En tant qu'équipe, je veux une **CI qui exécute lint + tests à chaque push** afin de détecter les régressions tôt.

**CA :**

- Pipeline CI bloquant en cas d'échec de lint ou de test.
- Temps d'exécution de la CI documenté et raisonnable (< 10 min).

**Sous-tâches techniques :**

1. Pipeline CI (GitHub Actions ou équivalent) : étape lint (`ruff`/`flake8`) + étape tests (`pytest`).
2. Configuration pour bloquer le merge en cas d'échec.
3. Mesure et affichage du temps d'exécution total de la pipeline.

**Cas à tester :** commit qui casse volontairement le lint (doit bloquer), commit qui casse un test (doit bloquer).

**Definition of Done :** pipeline complète et bloquante fonctionnelle, temps d'exécution < 10 min documenté.

---

## US-33 : Validation globale (5 pts)

En tant qu'équipe, je veux une **recette globale couvrant les 3 niveaux** afin de valider le produit avant la soutenance.

**CA :**

- Un scénario de recette couvre explicitement les 3 niveaux (génération de base, génération autonome multi-matières, correction persistante + anti-répétition).
- Au moins un support de test différent est utilisé par niveau.
- Un rapport de recette formalisé est produit et partagé avec l'équipe avant la soutenance.

**Sous-tâches techniques :**

1. Rédaction d'un scénario de recette écrit (document ou checklist) couvrant explicitement les 3 niveaux.
2. Sélection d'au moins un support de test distinct par niveau, différent de ceux utilisés en développement (éviter le biais de "sur-mesure").
3. Exécution manuelle du scénario par une personne qui n'a pas développé la fonctionnalité testée (validation croisée).
4. Rédaction du rapport de recette (succès/échec par critère, captures d'écran si pertinent).

**Cas à tester :** scénario complet niveau 3 avec correction + anti-répétition vérifiées sur un même support, dans la même session de test.

**Definition of Done :** rapport de recette rédigé et partagé avec l'équipe avant la soutenance.

---

**Démo de sprint** : recette formalisée présentée, couvrant les 3 niveaux de bout en bout.
