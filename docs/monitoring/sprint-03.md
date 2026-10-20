# Sprint 3 : Migration NoSQL + Contexte pédagogique + Stockage des retours + Export

**Objectif** : migrer vers NoSQL, permettre à l'enseignant de définir un contexte pédagogique réutilisable, poser la fondation du système d'apprentissage par les erreurs (stockage + résumé LLM), rendre l'export disponible dès maintenant, et conduire les tests d'évaluation du pipeline de segmentation.

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
3. **Persistance des documents uploadés** : à partir de ce sprint, chaque fichier uploadé (PDF, Markdown) est stocké avec ses métadonnées (nom, taille, date, `user_id`, texte extrait, sections) dans la collection `documents`. En Sprint 2 ce stockage n'existait pas — le document était traité en mémoire puis perdu.
4. Adapter la couche repository : remplacer les requêtes SQL par des opérations driver async (`motor` pour MongoDB).
5. Index sur les champs filtrés fréquemment : `user_id`, `document_id`, `generation_id`, `date`.
6. Mettre à jour `docker-compose.yml` (service MongoDB + volume nommé).
7. Script de re-seed pour les données de test.
8. Tests de non-régression : upload, génération, récupération de QCM — tous re-testés après migration.

**Cas à tester :** redémarrage conteneur sans perte de données, document avec sections profondément imbriquées, re-upload du même fichier par le même profil (doit créer un nouveau document ou détecter le doublon).

**Definition of Done :** aucune régression fonctionnelle, document uploadé retrouvable en base après redémarrage, tests de non-régression passants en CI.

---

## US-18 : Contexte personnalisé basé sur les retours (5 pts)

En tant qu'enseignant, je veux **consulter et réinitialiser mon contexte** — le résumé de tous mes retours passés — afin de comprendre ce que le système a appris de moi et de corriger d'éventuelles mauvaises interprétations.

> Ce que le système appelle "contexte" n'est pas un profil pédagogique statique (matière, niveau) — un même utilisateur peut enseigner plusieurs matières à plusieurs niveaux, ce qui rendrait un tel profil inutile. Le contexte est uniquement ce que le système a **appris des retours explicites** de l'enseignant : ses corrections, ses rejets, ses notations. C'est ce résumé qui est injecté en en-tête de chaque prompt (US-21).

**CA :**

- L'enseignant peut consulter son contexte actuel depuis son profil : le résumé LLM de ses retours passés, la date de dernière mise à jour, et le nombre de retours pris en compte.
- Il peut réinitialiser son contexte (suppression de tous ses retours et du résumé associé) avec confirmation explicite.
- Après réinitialisation, la prochaine génération part sans en-tête de contexte — comme un profil vierge.
- Le contexte est strictement isolé par profil.

**Sous-tâches techniques :**

1. Endpoint `GET /context` — retourne `ContextSummary(user_id, résumé, date_maj, nb_retours_utilisés)` pour le profil courant.
2. Endpoint `DELETE /context` — supprime le `ContextSummary` et tous les `Feedback` du profil (avec flag de confirmation obligatoire dans le body).
3. Interface Gradio dans l'écran profil : bloc "Mon contexte" affichant le résumé en lecture, date de mise à jour, et bouton "Réinitialiser" avec modale de confirmation.
4. Après réinitialisation, vérifier que la génération suivante n'injecte plus de bloc `[HISTORIQUE DES RETOURS]`.

**Cas à tester :** profil sans aucun retour (affiche "Aucun contexte établi"), réinitialisation suivie immédiatement d'un nouveau retour (le contexte se reconstruit correctement), tentative d'accès au contexte d'un autre profil (403).

**Definition of Done :** consultation et réinitialisation fonctionnelles, vérifiées manuellement sur 2 profils distincts.

---

## US-19 : Stockage des retours utilisateur (5 pts)

En tant que système, je veux **stocker chaque retour de l'enseignant en base** (correction, rejet, notation) afin de constituer la source de vérité pour le résumé de contexte (US-21).

> **Nouveau par rapport au Sprint 2** : en Sprint 2, les retours n'étaient pas persistés — ils étaient traités à la volée (anti-verbatim, self-repair JSON) mais jamais stockés. De plus, l'interface ne permettait de donner un retour qu'au niveau du QCM entier. Cette US introduit les deux manques : la persistance en base ET la granularité par question.

**CA :**

- Tout retour émis par l'enseignant est persisté immédiatement en base, dans la collection `feedbacks`.
- **Trois types de retours** sont couverts, du plus global au plus fin :
  - Rejet d'un QCM entier avec motif libre
  - Correction libre sur une question ou un distracteur spécifique
  - Notation 👍/👎 par question individuelle
- Chaque retour est horodaté et rattaché au profil, à la génération et à la question concernée (`question_id` nullable pour les retours globaux).
- Les retours survivent au redémarrage du système.
- Isolation stricte par `user_id` : aucun retour n'est accessible par un autre profil.

**Sous-tâches techniques :**

1. Document `Feedback(id, user_id, generation_id, question_id nullable, type: enum[correction|rejet|notation], contenu, date)`.
2. Endpoints dédiés :
   - `POST /generations/{id}/reject` — rejet global avec motif.
   - `POST /questions/{id}/correction` — correction libre sur une question ou un distracteur.
   - `PATCH /questions/{id}/rating` — notation 👍/👎, upsert (écrase la précédente).
3. Mise à jour de l'interface Gradio : ajouter bouton correction inline et boutons 👍/👎 par question, en plus du bouton "Rejeter tout" déjà présent.
4. Test de redémarrage : tous les retours persistés sont récupérables après restart.

**Cas à tester :** notation multiple sur la même question (upsert, pas doublon), rejet d'un QCM déjà partiellement corrigé question par question, retour sur une question dont la génération parente a été supprimée (intégrité référentielle en NoSQL).

**Definition of Done :** les trois types de retours sont stockés, testés et récupérables après redémarrage ; les contrôles par question sont visibles et fonctionnels dans l'interface.

---

## US-20 : Résumé LLM des erreurs et injection en en-tête de prompt (8 pts)

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

## US-21 : Historique des générations sur le profil (3 pts)

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

## US-22 : Export et téléchargement du QCM (5 pts)

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

## US-23 : Interface de validation du QCM question par question (5 pts)

En tant qu'enseignant, je veux **valider ou supprimer chaque question individuellement** depuis l'affichage du QCM généré, avec la possibilité de régénérer une question supprimée, afin d'affiner le QCM sans repartir de zéro.

**CA :**

- Chaque question affiche deux boutons : ✓ (valider) et ✕ (supprimer).
- À la suppression, une modale demande : "Voulez-vous régénérer une question sur cette notion ?" → Oui / Non.
  - Si Oui : une nouvelle question est générée pour la même section, en tenant compte du contexte de retours (US-21) et de l'anti-verbatim existant.
  - Si Non : la question est simplement retirée du QCM.
- Les questions validées sont marquées visuellement (badge vert), les supprimées disparaissent de la liste.
- Un compteur en haut de page indique la progression : "7 / 10 questions validées".
- Un bouton "Valider tout" permet de valider d'un coup les questions restantes non traitées.

**Sous-tâches techniques :**

1. Composants Gradio par question : bouton ✓, bouton ✕, badge d'état.
2. Modale de confirmation de suppression avec choix Oui/Non.
3. Appel `DELETE /questions/{id}` pour la suppression pure.
4. Appel `POST /questions/{id}/regenerate` pour la régénération : re-soumet la section source au pipeline de génération avec le contexte de retours courant.
5. Compteur de progression mis à jour en temps réel.
6. Bouton "Valider tout" → appel batch `PATCH /questions/validate-all` avec la liste des ids non traités.

**Cas à tester :** suppression + régénération sur une section avec une seule notion possible (risque de question très similaire — doit être détecté par anti-verbatim), suppression sans régénération (le QCM se retrouve avec moins de questions que prévu — comportement documenté).

**Definition of Done :** flow complet suppression → modale → régénération fonctionnel, testé manuellement de bout en bout.

---

## US-24 : Demande de questions supplémentaires (3 pts)

En tant qu'enseignant, je veux pouvoir **demander plus de questions sur un QCM déjà généré**, afin d'approfondir l'évaluation sans relancer une génération complète.

**CA :**

- Un bouton "Ajouter des questions" est disponible sur un QCM généré.
- Le système génère 2 questions supplémentaires par section (ou par section sélectionnée), en respectant l'anti-répétition (US-26 Sprint 4) et le contexte de retours.
- Les nouvelles questions sont ajoutées à la suite du QCM existant, clairement distinguées visuellement ("Questions ajoutées").
- L'anti-verbatim et l'anti-répétition s'appliquent entre les nouvelles questions et celles déjà présentes.

**Sous-tâches techniques :**

1. Bouton "Ajouter des questions" sur l'écran de génération + sélecteur optionnel de sections ciblées.
2. Endpoint `POST /generations/{id}/expand` : relance le pipeline de génération (2 questions / section ciblée) avec les questions existantes comme contexte d'exclusion.
3. Injection dans le prompt des intitulés des questions déjà présentes pour forcer la nouveauté.
4. Affichage des nouvelles questions avec un badge "Nouveau" dans l'interface.

**Cas à tester :** ajout sur un QCM déjà à 10 questions (les 2 nouvelles ne doivent pas dupliquer les existantes), ajout sur une section avec contenu limité (doit déclencher l'alerte de contenu insuffisant existante).

**Definition of Done :** les questions ajoutées passent l'anti-verbatim et ne dupliquent pas les existantes, testé sur 3 QCM.

---

## US-25 : Sauvegarde et import de QCM dans le profil (3 pts)

En tant qu'enseignant ou étudiant, je veux **retrouver mes QCM sauvegardés dans mon profil** et pouvoir **en importer un depuis un fichier externe**, afin de centraliser tous mes QCM dans l'application.

**CA :**

- Tout QCM généré dans l'app est automatiquement sauvegardé dans le profil (collection `generations` en NoSQL) et accessible depuis l'historique (US-22).
- Un enseignant peut importer un QCM au format GIFT ou XML Moodle depuis son profil : le QCM est parsé et stocké avec le même schéma interne que les QCM générés.
- Un QCM importé est clairement identifié comme "Importé" (pas "Généré") dans l'historique.
- Un QCM importé peut être soumis à la révision question par question (US-24), exporté, ou utilisé en mode entraînement étudiant.

**Sous-tâches techniques :**

1. Save automatique : vérifier que chaque génération est bien persistée dans `generations` dès la fin du pipeline (pas d'action manuelle requise de l'utilisateur).
2. Endpoint `POST /generations/import` : upload d'un fichier GIFT ou XML → parsing → validation du schéma → insertion dans `generations` avec `source: "import"`.
3. Parser GIFT et XML Moodle (peut réutiliser la logique d'export en sens inverse).
4. Badge "Importé" dans l'historique et dans l'interface de révision.

**Cas à tester :** import d'un fichier GIFT malformé (message d'erreur clair, pas de crash), import d'un QCM avec des caractères spéciaux dans les questions.

**Definition of Done :** import fonctionnel depuis les deux formats, QCM importé visible dans l'historique et révisable via US-24.

---

**Démo de sprint** : un enseignant génère un QCM, valide et supprime des questions une par une (avec régénération sur l'une d'elles), ajoute 2 questions supplémentaires, exporte en XML — puis importe un vieux QCM GIFT dans son profil et le retrouve dans son historique.

---

## US-35 : Test de taille maximale de document (3 pts)

En tant qu'équipe, je veux **déterminer la taille maximale de document qui produit un traitement de qualité** afin de fixer des limites documentées et d'orienter les utilisateurs.

**CA :**

- Une batterie de tests est conduite sur des documents de tailles croissantes (1 page, 5 pages, 10 pages, 20 pages, 50 pages+).
- Pour chaque taille, on mesure : nombre de sections détectées, qualité des sections (pertinence, cohérence), temps de traitement total, taux d'échec de parsing JSON.
- Un seuil de taille "optimale" et un seuil "maximum acceptable" sont identifiés et documentés.
- La limite de taille dans l'interface (actuellement 20 Mo) est ajustée si nécessaire en fonction des résultats.

**Sous-tâches techniques :**

1. Constituer un corpus de test : au moins 5 documents de tailles différentes, couvrant des matières variées.
2. Script de test automatisé qui lance la segmentation sur chaque document et collecte les métriques (nb sections, temps, taux d'échec).
3. Évaluation manuelle de la qualité des sections produites (grille de notation : pertinence du découpage, cohérence des titres, complétude du contenu).
4. Rapport de résultats : tableau taille → métriques, identification des seuils, recommandation sur la limite à afficher dans l'interface.

**Cas à tester :** document d'une seule ligne, document avec une seule très longue section sans titre, document de 50+ pages dense.

**Definition of Done :** rapport de test produit avec seuils identifiés, limite d'interface ajustée si nécessaire et documentée dans le doc de thomas.

---

## US-36 : Test de segmentation avec VLM ou LLM alternatif (5 pts)

En tant qu'équipe, je veux **tester des approches alternatives de segmentation** (VLM pour les documents avec représentations visuelles, ou LLM de taille différente) afin d'identifier la meilleure combinaison qualité/vitesse.

**CA :**

- Au moins deux approches alternatives sont testées et comparées au pipeline de segmentation actuel.
- Les solutions combinées sont explorées : ex. VLM pour extraire les schémas/tableaux + LLM texte pour le contenu narratif.
- Chaque approche est évaluée sur les mêmes documents de référence que US-26.
- Un rapport comparatif documente les avantages et limites de chaque approche.

**Sous-tâches techniques :**

1. Identifier les modèles candidats disponibles via Ollama : VLM (ex. `llava`, `minicpm-v`) pour les documents avec images/schémas, LLM léger alternatif (ex. `phi3`, `llama3.2:1b`) pour la vitesse.
2. Implémenter un wrapper de segmentation alternatif pour chaque modèle testé, en réutilisant l'interface existante (`segment_text`).
3. Définir une grille de comparaison : qualité du découpage, détection des schémas/formules, temps de traitement, taux d'erreur JSON.
4. Tester la solution combinée VLM + LLM sur au moins 2 documents contenant des représentations visuelles (schémas, graphiques, formules).
5. Rapport comparatif : tableau des résultats par approche + recommandation sur l'approche à adopter ou à combiner avec le pipeline actuel.

**Cas à tester :** document avec schémas et texte (VLM vs LLM texte seul), document purement textuel (LLM léger vs modèle actuel), document avec formules LaTeX.

**Definition of Done :** rapport comparatif produit sur au moins 3 approches, recommandation argumentée incluse.

---

## US-37 : Comparaison génération avec/sans lecture du document (5 pts)

En tant qu'équipe, je veux **comparer la qualité des questions générées avec et sans lecture complète du document**, en testant si indiquer uniquement la thématique suffit à produire des questions de qualité comparable.

**CA :**

- Pour un même ensemble de sections, deux générations sont produites : une avec le contenu complet de la section (pipeline actuel), une avec uniquement le titre/thématique de la section.
- La qualité des deux générations est comparée sur des critères définis : pertinence, précision, ancrage dans le contenu du cours, difficulté.
- Le gain de temps de la version "thématique seule" est mesuré.
- Si la qualité est jugée acceptable, cette approche peut devenir un mode "rapide" dans le pipeline.

**Sous-tâches techniques :**

1. Implémenter un mode de génération `prompt_mode: "full" | "topic_only"` dans le pipeline, paramétrable sans changer le reste du code.
2. Conduire la comparaison sur au moins 5 sections de matières différentes, en générant les deux versions pour chaque section.
3. Grille d'évaluation manuelle : un membre de l'équipe n'ayant pas vu le document note chaque question sur 3 critères (pertinence, précision, difficulté) sans savoir laquelle vient de quel mode.
4. Mesure du gain de temps (les tokens du contenu n'étant plus envoyés, le prompt est plus court → inférence plus rapide).
5. Rapport : tableau comparatif des scores, mesure de gain de temps, recommandation sur l'utilité d'un mode rapide.

**Cas à tester :** section très courte (thématique seule ≈ contenu complet), section dense avec données chiffrées (la thématique seule risque de produire des questions génériques), section avec formules (le LLM peut-il deviner les formules depuis la thématique ?).

**Definition of Done :** comparaison conduite en double aveugle sur 5 sections minimum, rapport produit avec recommandation claire sur l'opportunité d'un mode rapide.

---

## US-38 : Analyse des sorties LLM indispensables vs évitables (3 pts)

En tant qu'équipe, je veux **identifier quelles sorties du premier LLM sont réellement indispensables** au pipeline afin d'éliminer les appels inutiles et gagner en efficacité.

**CA :**

- Chaque sortie produite par le LLM en phase de segmentation/analyse est évaluée : est-elle utilisée en aval ? améliore-t-elle la qualité de la génération ? ou peut-elle être remplacée par du calcul algorithmique ?
- Les sorties jugées évitables sont supprimées ou remplacées, et l'impact sur la qualité finale est mesuré.
- Le nombre d'appels LLM total par document est réduit d'au moins 1 appel par section suite à cette analyse.

**Sous-tâches techniques :**

1. Cartographier toutes les sorties du premier LLM actuellement utilisées : résumé de section, détection content-type, détection matière, titre de section.
2. Pour chaque sortie, évaluer : utilisée par quel module en aval ? peut-elle être calculée algorithmiquement (ex. détection content-type par heuristique de mots-clés au lieu d'un LLM) ?
3. Tester la suppression ou le remplacement algorithmique de chaque sortie candidate, en mesurant l'impact sur la qualité des questions générées.
4. Rapport : tableau sortie → utilisée/évitable/remplaçable + gain en nombre d'appels LLM + impact qualité mesuré.

**Cas à tester :** génération sans résumé de section injecté dans le prompt (la qualité des questions baisse-t-elle ?), détection content-type par heuristique vs LLM (taux de concordance).

**Definition of Done :** rapport produit, au moins une sortie supprimée ou remplacée avec impact qualité documenté, gain en nombre d'appels LLM mesuré et chiffré.