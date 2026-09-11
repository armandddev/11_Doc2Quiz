# Sprint 2 — Semaines 4-5 : Niveau 1 complet (difficulté, calculs) + persistance de base

**Objectif** : le Niveau 1 fonctionne de bout en bout — un enseignant obtient un QCM avec calculs et niveaux de difficulté, et le système persiste les données.

---

## US-12 : Génération QCM niveau 1 (8 pts)

En tant qu'enseignant, je veux **générer un QCM avec des niveaux de difficulté explicites** afin d'adapter l'évaluation.

**CA :**

- Chaque question est associée à un niveau parmi {facile, moyen, difficile}, déterminé par le système en fonction de la complexité réelle de la notion source (pas un tirage aléatoire).
- Le prof peut, en option, indiquer une répartition souhaitée (ex. 2 faciles / 2 moyennes / 1 difficile), mais ce n'est jamais obligatoire.
- Le format de sortie (question, niveau, bonne réponse, 3 distracteurs, explication) est validé par un schéma strict (`pydantic`/`jsonschema`).
- En cas de JSON invalide, une régénération automatique est tentée (2 essais max) avant un message d'erreur explicite, sans crash.

**Sous-tâches techniques :**

1. Prompt de génération avec instruction explicite de niveau de difficulté par question.
2. Logique de "complexité de la notion" : nombre de sous-concepts, longueur, présence de formules → mapping vers facile/moyen/difficile.
3. Schéma Pydantic strict : `Question(question, niveau: Literal[...], bonne_reponse, distracteurs: List[str] len=3, explication)`.
4. Boucle de self-repair : si erreur de validation, renvoyer l'erreur au LLM dans un nouveau prompt de correction, max 2 tentatives.
5. Traduire l'option "répartition souhaitée" du prof en contrainte explicite injectée dans le prompt.

**Cas à tester :** notion très simple (doit rester facile), notion complexe multi-concepts (doit produire du difficile), LLM renvoyant un JSON tronqué.

**Definition of Done :** schéma validé automatiquement à 100 %, testé sur au moins 10 générations couvrant des notions de complexité variée.

---

## US-13 : Génère exercice de calcul réel (5 pts)

En tant qu'enseignant de matière scientifique, je veux que le système **génère des exercices de calcul réels** afin de tester la compétence et pas la restitution.

**CA :**

- Quand la discipline détectée (US-08) implique du calcul, chaque question générée nécessite une résolution numérique réelle (pas une question de définition).
- Un contrôle automatique vérifie qu'au moins une opération/valeur numérique apparaît dans l'énoncé ou la résolution attendue.
- Les valeurs numériques utilisées sont différentes de celles des exemples du cours source, tout en restant cohérentes avec la notion enseignée.
- Testé sur au moins 3 supports de maths/sciences de niveaux différents.

**Sous-tâches techniques :**

1. Prompt spécifique déclenché par le tag "calcul" (US-08), avec exemples few-shot d'exercices types.
2. Vérification post-génération : parsing léger pour détecter la présence d'opérateurs/valeurs numériques dans l'énoncé.
3. Vérifier que les valeurs numériques diffèrent de celles extraites du texte source (comparaison directe ou instruction explicite au LLM).
4. Vérification de cohérence mathématique : option de double-vérification via un second appel LLM "vérificateur", ou calcul symbolique (`sympy`) pour les cas simples.

**Cas à tester :** exercice à plusieurs étapes de calcul, notion avec formule mais sans exemple numérique dans le cours source.

**Definition of Done :** testé sur 3 supports de maths/sciences réels, taux de rejet (absence de calcul détecté) mesuré et documenté.

---

## US-14 : Questions différentes / anti-verbatim (5 pts)

En tant qu'enseignant, je veux que **les questions ne reprennent jamais des phrases du cours telles quelles** afin d'évaluer la compréhension.

**CA :**

- Un test de similarité texte (ratio de n-grammes communs) compare chaque question générée au texte source.
- Si le taux de similarité dépasse un seuil défini (valeur initiale proposée : 40 %, ajustable), la question est automatiquement régénérée (2 essais max).
- Le seuil est un paramètre de configuration externe, pas une valeur en dur dans le code.

**Sous-tâches techniques :**

1. Implémenter le calcul de similarité par n-grammes (shingles de 4 mots, via `nltk`/`sklearn` ou fonction maison).
2. Externaliser le seuil dans un fichier de config (`config.yaml`), valeur par défaut 40 %.
3. Boucle de régénération : renvoyer au LLM un prompt de reformulation explicite en cas de dépassement (pas juste répéter la demande initiale).
4. Logger les cas de rejet pour analyse ultérieure (utile pour ajuster le seuil en Sprint 3).

**Cas à tester :** question qui reprend une définition mot pour mot, question reformulée mais qui garde la structure de phrase du cours.

**Definition of Done :** aucune question testée manuellement sur 5 supports ne dépasse le seuil sans être régénérée.

---

## US-15 : Profil persistant (5 pts)

En tant qu'enseignant, je veux avoir un **profil persistant** afin de retrouver mes documents et mes QCM après redémarrage du système.

**CA :**

- Création de compte minimale (login/mot de passe) et reconnexion possible.
- Données stockées dans une base persistée via un volume Docker nommé.
- Un test de redémarrage du conteneur confirme l'absence de perte de données.
- Chaque document et chaque QCM généré est explicitement rattaché au profil qui l'a créé.

**Sous-tâches techniques :**

1. Modèle de données `User(id, email, password_hash, created_at)`.
2. Hashage du mot de passe (`bcrypt`/`argon2`), jamais de mot de passe en clair.
3. Tables `documents` et `generations` avec clé étrangère vers `user_id`.
4. Connexion au volume Docker nommé déjà posé en US-10.
5. Test de redémarrage automatisé : stop/restart du conteneur DB + vérification d'intégrité des données.

**Cas à tester :** connexion avec mauvais mot de passe, création de compte avec email déjà utilisé.

**Definition of Done :** test de redémarrage automatisé et passant en CI.

---

## US-16 : Interface édition/validation des QCM (5 pts)

En tant qu'enseignant, je veux une **interface d'édition/validation des QCM générés** afin de corriger avant utilisation.

**CA :**

- Édition en ligne du texte de la question, des distracteurs, du feedback et du niveau de difficulté.
- Les modifications sont sauvegardées et horodatées.
- Un indicateur visuel distingue une question "générée telle quelle" d'une question "modifiée manuellement" (utile pour le Niveau 3 plus tard).

**Sous-tâches techniques :**

1. Composants Gradio éditables (Textbox) pour question, distracteurs, feedback, sélecteur de niveau de difficulté.
2. Bouton "Sauvegarder" par question avec appel API PATCH.
3. Champ `modifie_manuellement: bool` + `date_modification` en base, mis à jour à chaque sauvegarde.
4. Affichage visuel (badge/couleur) selon ce champ.

**Cas à tester :** modification puis annulation, modification de plusieurs questions à la suite.

**Definition of Done :** une modification est bien persistée après rechargement de la page.

---

**Démo de sprint** : un enseignant se connecte, upload un support, obtient un QCM avec niveaux de difficulté et calculs, l'édite, et retrouve tout après redémarrage.
