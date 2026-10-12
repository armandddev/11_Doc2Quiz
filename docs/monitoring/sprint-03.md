# Sprint 3 — Semaines 6-7 : Migration NoSQL + Contexte pédagogique + Stockage des retours + Export

**Objectif** : migrer vers NoSQL, permettre à l'enseignant de définir un contexte pédagogique réutilisable, poser la fondation du système d'apprentissage par les erreurs (stockage + résumé LLM), et rendre l'export disponible dès maintenant.

---

## US-17 : Migration NoSQL (5 pts)

En tant qu'équipe, je veux **migrer la couche de persistance vers une base NoSQL** afin d'adopter un modèle de données adapté aux structures imbriquées du projet (sections, retours, résumés LLM, contextes).

**CA :**

- Toutes les données existantes (utilisateurs, documents, sections, générations, questions) sont stockées en NoSQL.
- Les opérations CRUD continuent de fonctionner sans régression.
- La base tourne dans un service Docker dédié avec volume nommé persistant.
- Un script de re-seed des données de test est fourni.

**Sous-tâches techniques :**

1. Choix du moteur NoSQL (MongoDB recommandé — flexibilité des documents imbriqués, requêtes sur tableaux).
2. Définir les collections : `users`, `documents`, `generations`, `questions`, `feedbacks`, `contexts`, `context_summaries`.
3. Adapter la couche repository : remplacer les requêtes SQL par des opérations driver async (`motor` pour MongoDB).
4. Index sur les champs filtrés fréquemment : `user_id`, `document_id`, `generation_id`, `date`.
5. Mettre à jour `docker-compose.yml` (service MongoDB + volume nommé).
6. Script de re-seed pour les données de test.
7. Tests de non-régression : upload, génération, récupération de QCM — tous re-testés après migration.

**Cas à tester :** redémarrage conteneur sans perte de données, document avec sections profondément imbriquées.

**Definition of Done :** aucune régression fonctionnelle, tests de non-régression passants en CI, volume persistant vérifié après restart.

---

## US-18 : Création d'un contexte pédagogique (3 pts)

En tant qu'enseignant, je veux **créer un contexte pédagogique nommé** (niveau de classe, matière, objectifs) afin de ne pas re-saisir ces informations à chaque génération.

**CA :**

- Un enseignant peut créer un ou plusieurs contextes nommés (ex. "Terminale Maths", "3e SVT").
- Un contexte contient : nom, niveau scolaire, matière, objectifs pédagogiques libres, consignes de style optionnelles.
- Les contextes sont listés, modifiables et supprimables depuis l'interface.
- Strictement rattachés au profil créateur (`user_id`).
- Persistés en NoSQL dans la collection `contexts`.

**Sous-tâches techniques :**

1. Document `Context(id, user_id, nom, niveau, matière, objectifs, consignes_style, date_création, date_maj)`.
2. Endpoints CRUD : `POST /contexts`, `GET /contexts`, `PATCH /contexts/{id}`, `DELETE /contexts/{id}`.
3. Interface Gradio : formulaire création/édition + liste avec boutons Modifier/Supprimer.
4. Validation : nom unique par profil, champs obligatoires (nom, niveau, matière).

**Cas à tester :** deux contextes avec le même nom (refusé), suppression d'un contexte déjà utilisé dans une génération (avertissement).

**Definition of Done :** CRUD fonctionnel depuis l'interface, données isolées et persistées par profil.

---

## US-19 : Utilisation du contexte dans la génération (3 pts)

En tant qu'enseignant, je veux **sélectionner un contexte lors d'une génération** afin que les questions soient adaptées au niveau et aux objectifs définis.

**CA :**

- À l'écran de génération, l'enseignant sélectionne un de ses contextes (ou laisse "sans contexte").
- Niveau, matière, objectifs et style sont injectés dans le prompt, **en complément** du résumé d'erreurs (US-21).
- L'identifiant du contexte est stocké avec chaque génération.

**Sous-tâches techniques :**

1. Dropdown Gradio alimenté par `GET /contexts` dans l'écran de génération.
2. Bloc `[CONTEXTE PÉDAGOGIQUE]` injecté dans le prompt (niveau, matière, objectifs, style).
3. Stocker `context_id` (nullable) dans le document de génération.
4. Test : une même section génère des questions différentes avec "Terminale" vs "3e".

**Cas à tester :** génération sans contexte (doit fonctionner), contexte supprimé entre le chargement et la soumission (gestion gracieuse).

**Definition of Done :** différence observable et documentée entre une génération avec et sans contexte.

---

## US-20 : Stockage des retours utilisateur (5 pts)

En tant que système, je veux **stocker chaque retour de l'enseignant en base** (correction, rejet, notation) afin de constituer la source de vérité pour le résumé de contexte (US-21).

**CA :**

- Tout retour émis par l'enseignant est persisté immédiatement en base, dans la collection `feedbacks`.
- Les types de retours couverts : correction d'une question ou d'un distracteur, rejet d'un QCM entier avec motif, notation 👍/👎 par question.
- Chaque retour est horodaté et rattaché au profil, à la génération et à la question concernée.
- Les retours survivent au redémarrage du système.
- Isolation stricte par `user_id` : aucun retour n'est accessible par un autre profil.

**Sous-tâches techniques :**

1. Document `Feedback(id, user_id, generation_id, question_id nullable, type: enum[correction|rejet|notation], contenu, date)`.
2. Endpoints dédiés :
   - `POST /questions/{id}/correction` — correction libre sur une question ou un distracteur.
   - `POST /generations/{id}/reject` — rejet global avec motif.
   - `PATCH /questions/{id}/rating` — notation 👍/👎 (upsert : écrase la précédente).
3. Affichage des contrôles dans l'interface Gradio : bouton correction inline, bouton "Rejeter tout" + textarea, boutons 👍/👎 par question.
4. Test de redémarrage : tous les retours persistés sont récupérables après restart.

**Cas à tester :** notation multiple sur la même question (upsert, pas doublon), rejet d'un QCM déjà partiellement corrigé.

**Definition of Done :** les trois types de retours sont stockés, testés et récupérables après redémarrage.

---

## US-21 : Résumé LLM des erreurs et injection en en-tête de prompt (8 pts)

En tant que système, je veux **envoyer au LLM l'ensemble des retours d'un enseignant pour qu'il en génère un résumé**, afin que ce résumé soit injecté en en-tête de chaque nouveau prompt de génération.

**CA :**

- Avant chaque génération, le système récupère tous les retours stockés du profil concerné (collection `feedbacks`, US-20).
- Ces retours sont envoyés au LLM avec une instruction de résumé : "À partir de ces retours, produis un résumé concis des erreurs récurrentes et des attentes de cet enseignant."
- Le résumé produit est stocké dans la collection `context_summaries` (un document par profil, mis à jour à chaque nouvelle génération ou dès qu'un nouveau retour est ajouté).
- Ce résumé est systématiquement injecté en premier bloc du prompt de génération, avant les instructions et le contenu du support.
- Si aucun retour n'existe encore pour ce profil, le bloc est omis sans erreur.
- La mise à jour du résumé est asynchrone et ne bloque pas l'interface.

**Sous-tâches techniques :**

1. Endpoint interne `POST /context-summaries/refresh` déclenché à chaque nouveau retour (ou en différé par batch si le volume est important).
2. Prompt de résumé dédié : collecter tous les `Feedback.contenu` du profil → appel LLM → résumé en 5-10 lignes max.
3. Document `ContextSummary(user_id, résumé, date_maj, nb_retours_utilisés)`.
4. Injection dans le pipeline de génération : récupérer `ContextSummary` par `user_id` → l'ajouter en tête du prompt sous un bloc `[HISTORIQUE DES RETOURS DE L'ENSEIGNANT]`.
5. Log du résumé injecté par génération (pour debug et traçabilité).
6. Gestion de la taille : si le résumé dépasse un seuil de tokens, le tronquer ou demander au LLM de le condenser davantage.

**Cas à tester :** profil sans aucun retour (aucun bloc injecté, génération normale), profil avec 50+ retours variés (résumé cohérent et non-démesuré), nouveau retour ajouté → vérifier que le prochain prompt reflète le nouveau résumé.

**Definition of Done :** vérification manuelle sur 3 profils avec historiques différents que le bloc injecté reflète fidèlement les retours stockés.

---

## US-22 : Historique des générations sur le profil (3 pts)

En tant qu'enseignant, je veux **consulter l'historique de mes générations sur mon profil** afin de retrouver, consulter et ré-exporter mes QCM passés.

**CA :**

- L'historique liste, pour chaque génération : support source, contexte utilisé, date, nombre de questions, statut (validé / rejeté / en cours).
- Filtres disponibles : par support, par contexte, par plage de dates, par statut.
- On peut rouvrir une génération passée pour la consulter, la modifier ou la ré-exporter.
- Isolation stricte par profil.
- Pagination si l'historique dépasse 20 entrées.

**Sous-tâches techniques :**

1. Requête MongoDB sur `generations` avec filtre `user_id` obligatoire + paramètres de filtre optionnels.
2. Interface Gradio : tableau paginé, colonne statut + bouton "Rouvrir".
3. Test d'isolation : un profil ne peut pas accéder aux générations d'un autre via l'API (doit retourner 403).

**Cas à tester :** utilisateur avec 0 générations (page vide sans erreur), accès à une génération appartenant à un autre profil (bloqué).

**Definition of Done :** test d'isolation automatisé et passant en CI, pagination vérifiée manuellement.

---

## US-23 : Export et téléchargement du QCM (5 pts)

En tant qu'enseignant, je veux **exporter mon QCM en GIFT et en XML Moodle et le télécharger directement depuis l'interface**, sans manipuler de fichiers serveur.

**CA :**

- Deux formats : `.txt` GIFT et `.xml` Moodle (multichoice), avec feedback par réponse dans les deux cas.
- Le fichier XML est validé par un parseur avant mise à disposition (jamais de fichier invalide livré).
- Boutons de téléchargement accessibles depuis l'écran de génération **et** depuis l'historique (US-22).
- Nom de fichier explicite : `{nom-support-slugifié}_{YYYY-MM-DD}.{ext}`.

**Sous-tâches techniques :**

1. Sérialisation JSON → GIFT avec échappement des caractères spéciaux (`~ = # { } :`).
2. Génération XML via `xml.etree.ElementTree`, schéma Moodle "multichoice", échappement XML (`&`, `<`, `>`).
3. Validation XML avant téléchargement (parseur standard — fail-safe systématique).
4. Slugification du nom de support pour le nom de fichier.
5. Composants Gradio de téléchargement (un par format) dans les deux points d'accès.

**Cas à tester :** distracteur avec caractère spécial GIFT, question avec accents, nom de support avec espaces et caractères spéciaux.

**Definition of Done :** fichiers GIFT et XML générés, validés et téléchargeables depuis les deux points d'accès, testés sur au moins 3 QCM.

---

**Démo de sprint** : l'enseignant crée un contexte "Terminale Physique", génère un QCM — le prompt intègre en en-tête le résumé de ses retours passés — corrige une question — le résumé est mis à jour — il retrouve la génération dans son historique et télécharge le fichier XML.