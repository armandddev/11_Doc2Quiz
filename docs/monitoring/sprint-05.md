# Sprint 5 : Stabilisation & recette

**Objectif** : valider l'ensemble du produit de bout en bout, sécuriser la qualité logicielle, et ramener le temps de génération à moins de 4 minutes avant la soutenance.

---

## US-30 : Tests unitaires (5 pts)

En tant qu'équipe, je veux des **tests unitaires sur les modules critiques** afin de sécuriser les évolutions.

**CA :**

- Couverture ≥ 60 % sur : parsing, génération JSON, anti-verbatim, anti-répétition, stockage des retours (US-20), résumé LLM (US-21), export.
- Tests exécutés automatiquement en CI à chaque push.

**Sous-tâches techniques :**

1. Framework `pytest` + couverture `pytest-cov`.
2. Modules prioritaires : parsing (US-05/06/07), validation JSON (US-12), anti-verbatim pipeline, anti-répétition (US-30), stockage feedback (US-20), résumé et injection contexte (US-21), export GIFT/XML (US-23), Vrai/Faux (US-29).
3. Mock systématique des appels Ollama (jamais de dépendance à un serveur réel en CI).
4. Mock MongoDB (ex. `mongomock`) pour les tests de persistance.

**Cas à tester :** tous les cas limites identifiés au fil des sprints (PDF scanné, JSON invalide, profil sans retours, résumé LLM vide, etc.).

**Definition of Done :** couverture ≥ 60 % mesurée en CI, badge de couverture dans le README.

---

## US-31 : CI (2 pts)

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

## US-32 : Fusion des appels LLM par section (5 pts)

En tant qu'équipe, je veux **regrouper les appels LLM séquentiels par section en un seul appel** afin de diviser le nombre total d'appels par ~3 et réduire drastiquement le temps de génération.

**CA :**

- Pour chaque section, les trois appels actuellement séquentiels (détection content-type + matière, résumé, génération des questions) sont remplacés par un seul prompt qui retourne les trois en une réponse JSON.
- Le schéma de sortie est validé par Pydantic comme avant — seule la structure d'appel change, pas la validation.
- Aucune régression sur la qualité des questions générées (vérifiée sur les mêmes supports de test qu'avant).
- Benchmark avant/après documenté sur un support de 10 sections : objectif ÷3 sur le nombre d'appels.

**Sous-tâches techniques :**

1. Concevoir le prompt fusionné : `[texte de section]` → JSON avec clés `content_type`, `matière`, `résumé`, `questions[]`. Utiliser un exemple few-shot pour forcer la structure.
2. Adapter le schéma Pydantic pour valider la réponse fusionnée en une passe.
3. Supprimer les trois anciens appels séquentiels et les remplacer par l'appel unique dans le pipeline.
4. Vérifier que le self-repair (2 tentatives sur JSON invalide) fonctionne toujours sur le nouveau schéma fusionné.
5. Benchmark : comparer nombre d'appels et temps total avant/après sur 3 supports de tailles différentes.

**Cas à tester :** section très courte (le LLM doit quand même produire les 3 sorties), section avec formules mathématiques (content-type "calcul" correctement détecté dans la réponse fusionnée), JSON partiellement invalide (self-repair sur la réponse fusionnée).

**Definition of Done :** nombre d'appels LLM par section réduit à 1, benchmark documenté, aucune régression sur les tests unitaires existants.

---

## US-33 : Anti-verbatim algorithmique (3 pts)

En tant qu'équipe, je veux **remplacer l'appel LLM de validation anti-verbatim par un calcul algorithmique de similarité** afin de supprimer 10+ appels lents pour une tâche qui n'en a pas besoin.

**CA :**

- La détection de verbatim n'effectue plus aucun appel LLM : elle repose uniquement sur un calcul de similarité par n-grammes (shingles de 4 mots).
- Le seuil de similarité reste configurable dans `config.yaml` (valeur par défaut 40 %, inchangée).
- Le temps de traitement de l'anti-verbatim passe de ~30s/question (appel LLM) à <5ms/question (calcul local).
- En cas de dépassement du seuil, la question est renvoyée au LLM pour reformulation avec un prompt explicite — c'est le seul appel LLM restant dans ce module.
- Les tests existants sur l'anti-verbatim continuent de passer sans modification.

**Sous-tâches techniques :**

1. Implémenter la fonction `similarity_score(text_a, text_b, n=4) -> float` basée sur les shingles de n-grammes (`nltk` ou fonction maison — pas de dépendance lourde).
2. Remplacer l'appel LLM de validation par cette fonction dans le pipeline.
3. Conserver uniquement l'appel LLM de *reformulation* en cas de dépassement (le LLM ne juge plus, il reformule seulement).
4. Benchmark : mesurer le temps de traitement anti-verbatim avant/après sur un QCM de 10 questions.
5. Vérifier que le taux de faux positifs reste comparable à l'ancienne version LLM (mesure sur le corpus de test existant).

**Cas à tester :** question identique au texte source (doit être rejetée), question reformulée légèrement (doit passer), contenu avec formules LaTeX ou code (les n-grammes doivent les traiter sans crash).

**Definition of Done :** zéro appel LLM dans la phase de détection, temps <5ms par question mesuré, tests anti-verbatim existants tous verts.

---

## US-34 : Optimisation par parallélisation des appels LLM (5 pts)

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

## US-35 : Validation globale (5 pts)

En tant qu'équipe, je veux une **recette globale couvrant l'ensemble des fonctionnalités** afin de valider le produit avant la soutenance.

**CA :**

- Le scénario de recette couvre explicitement : génération de base (QCM + Vrai/Faux), injection du résumé de retours en en-tête, revue question par question avec régénération (US-23), anti-répétition entre deux générations (US-29), export GIFT et XML (US-22), historique profil (US-21), gain de performance mesuré (US-32 + US-33 + US-34).
- Au moins un support de test différent de ceux utilisés en développement est utilisé par scénario.
- La recette est exécutée par une personne n'ayant pas développé la fonctionnalité testée.
- Un rapport de recette formalisé est produit avant la soutenance.

**Sous-tâches techniques :**

1. Rédaction du scénario de recette (checklist couvrant tous les modules).
2. Sélection des supports de test (distincts des supports de dev).
3. Exécution croisée (une personne par fonctionnalité qu'elle n'a pas codée).
4. Rapport : succès/échec par critère, captures d'écran si pertinent.

**Cas à tester :** scénario complet — correction + rejet → résumé LLM mis à jour → nouvelle génération sur le même support (anti-répétition vérifiée, résumé en en-tête) → revue question par question avec une régénération → export XML validé.

**Definition of Done :** rapport de recette rédigé et partagé avec l'équipe avant la soutenance.

---

**Démo de sprint** : recette formalisée présentée, couvrant l'ensemble des fonctionnalités de bout en bout — avec benchmark de génération montrant le passage de ~27 min à <4 min sur un support de 10 sections.