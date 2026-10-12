# Sprint 5 — Semaine 10 : Stabilisation & recette

**Objectif** : valider l'ensemble du produit de bout en bout et sécuriser la qualité logicielle avant la soutenance.

---

## US-28 : Tests unitaires (5 pts)

En tant qu'équipe, je veux des **tests unitaires sur les modules critiques** afin de sécuriser les évolutions.

**CA :**

- Couverture ≥ 60 % sur : parsing, génération JSON, anti-verbatim, anti-répétition, stockage des retours (US-20), résumé LLM (US-21), export.
- Tests exécutés automatiquement en CI à chaque push.

**Sous-tâches techniques :**

1. Framework `pytest` + couverture `pytest-cov`.
2. Modules prioritaires : parsing (US-05/06/07), validation JSON (US-12), anti-verbatim pipeline, anti-répétition (US-26), stockage feedback (US-20), résumé et injection contexte (US-21), export GIFT/XML (US-23).
3. Mock systématique des appels Ollama (jamais de dépendance à un serveur réel en CI).
4. Mock MongoDB (ex. `mongomock`) pour les tests de persistance.

**Cas à tester :** tous les cas limites identifiés au fil des sprints (PDF scanné, JSON invalide, profil sans retours, résumé LLM vide, etc.).

**Definition of Done :** couverture ≥ 60 % mesurée en CI, badge de couverture dans le README.

---

## US-29 : CI (2 pts)

En tant qu'équipe, je veux une **CI qui exécute lint + tests à chaque push** afin de détecter les régressions tôt.

**CA :**

- Pipeline CI bloquante en cas d'échec de lint ou de test.
- Temps d'exécution documenté et < 10 min.

**Sous-tâches techniques :**

1. Pipeline CI (GitHub Actions) : étape lint (`ruff`) + étape tests (`pytest`).
2. Blocage du merge en cas d'échec.
3. Mesure du temps d'exécution total.

**Definition of Done :** pipeline complète et bloquante, temps < 10 min documenté.

---

## US-30 : Optimisation par parallélisation des appels LLM (5 pts)

En tant qu'équipe, je veux **identifier et paralléliser les appels LLM séquentiels** afin de réduire significativement le temps de génération d'un QCM complet.

**CA :**

- Un benchmark mesure le temps de génération bout en bout avant et après optimisation, sur au moins 3 supports de tailles différentes.
- Les appels qui peuvent être parallélisés le sont (résumé de section, génération de question par section, vérification anti-verbatim) — en conservant les appels qui doivent rester séquentiels (ex. résumé global avant injection).
- Le gain de temps est documenté (objectif indicatif : ≥ 30 % de réduction sur un support de 10+ sections).
- Aucune régression fonctionnelle introduite par la parallélisation (les résultats restent valides et complets).
- La parallélisation est configurable (paramètre `max_concurrent_calls` dans le fichier de config) pour ne pas saturer une instance Ollama sous-dimensionnée.

**Sous-tâches techniques :**

1. **Audit du pipeline actuel** : cartographier tous les appels LLM et identifier les dépendances entre eux (lesquels peuvent partir en parallèle, lesquels attendent un résultat précédent).
2. **Parallélisation avec `asyncio.gather`** : remplacer les boucles séquentielles sur les sections (résumé, génération, anti-verbatim) par des groupes d'appels concurrents.
3. **Paramètre `max_concurrent_calls`** dans `config.yaml` (valeur par défaut : 4) — limiter le nombre de requêtes simultanées vers Ollama pour éviter la surcharge.
4. **Benchmark automatisé** : script `bench.py` qui mesure le temps de génération complet (wall time) avant et après, sur 3 supports, et produit un tableau comparatif.
5. **Tests de non-régression** : vérifier que les résultats produits en parallèle sont identiques en structure à ceux produits en séquentiel (validation du schéma JSON, absence de réponses tronquées).
6. **Gestion des erreurs en contexte concurrent** : une section qui échoue ne doit pas annuler les autres — isolation des exceptions par tâche (`asyncio` try/except par gather item).

**Cas à tester :** support à 20 sections (gain attendu maximal), instance Ollama lente simulée (vérifier que le backoff et les retries fonctionnent correctement en contexte concurrent), `max_concurrent_calls=1` (doit se comporter comme l'ancien séquentiel).

**Definition of Done :** benchmark documenté dans le README avec tableau avant/après, aucune régression sur les tests unitaires existants, paramètre `max_concurrent_calls` fonctionnel et testé.

---

## US-31 : Validation globale (5 pts)

En tant qu'équipe, je veux une **recette globale couvrant l'ensemble des fonctionnalités** afin de valider le produit avant la soutenance.

**CA :**

- Le scénario de recette couvre explicitement : génération de base, utilisation du contexte pédagogique, injection du résumé de retours en en-tête, anti-répétition entre deux générations, export GIFT et XML, historique profil, et gain de performance mesuré (US-30).
- Au moins un support de test différent de ceux utilisés en développement est utilisé par scénario.
- La recette est exécutée par une personne n'ayant pas développé la fonctionnalité testée.
- Un rapport de recette formalisé est produit avant la soutenance.

**Sous-tâches techniques :**

1. Rédaction du scénario de recette (checklist couvrant tous les modules).
2. Sélection des supports de test (distincts des supports de dev).
3. Exécution croisée (une personne par fonctionnalité qu'elle n'a pas codée).
4. Rapport : succès/échec par critère, captures d'écran si pertinent.

**Cas à tester :** scénario complet avec correction d'une question → vérification que le résumé LLM est mis à jour → nouvelle génération sur le même support → vérification anti-répétition + présence du résumé en en-tête du prompt.

**Definition of Done :** rapport de recette rédigé et partagé avec l'équipe avant la soutenance.

---

**Démo de sprint** : recette formalisée présentée, couvrant l'ensemble des fonctionnalités de bout en bout.