# Sprint 4 — Semaines 8-9 : Niveau 3 (correction persistante, profils, tendances, anti-répétition) + export

**Objectif** : le système apprend définitivement de ses erreurs, par profil, suit les habitudes d'usage, et garantit la variété entre générations.

---

## US-22 : Correction erreur (8 pts)

En tant qu'enseignant, je veux que **la correction d'une erreur signalée s'applique pour toujours, à toutes mes futures générations**, afin de ne jamais revoir la même erreur.

**CA :**

- Quand une question ou un distracteur est signalé comme faux/ambigu, la correction est enregistrée comme une "règle apprise" rattachée au profil de l'enseignant.
- Toute génération future sur un support similaire ou la même notion, pour ce même profil, intègre cette règle.
- La règle apprise persiste après redémarrage du système (stockage en base, pas en mémoire).
- Un test vérifie qu'après correction, une nouvelle génération sur le même support ne reproduit pas l'erreur signalée.
- Une limite est fixée sur le nombre de règles conservées par profil (ex. 50 dernières corrections).
- Chaque profil a ses propres règles apprises : aucune fuite entre enseignants.

**Sous-tâches techniques :**

1. Modèle de données `RegleApprise(id, user_id, notion_id nullable, description, date_creation)`.
2. Mécanisme de résumé : un appel LLM résume l'erreur signalée en une phrase courte réutilisable dans un prompt futur.
3. Injection dans le prompt de génération : récupérer les N dernières règles pertinentes (par profil, et par notion si disponible).
4. Politique de purge : limite à 50 règles par profil, suppression FIFO ou par pertinence/fréquence d'usage.
5. Test de non-régression : générer → signaler une erreur → régénérer → vérifier que l'erreur ne réapparaît pas.

**Cas à tester :** deux règles apprises contradictoires, volume important de règles (test de performance sur l'injection prompt).

**Definition of Done :** test de non-régression automatisé et passant en CI, règles persistées après redémarrage.

---

## US-23 : Historique complet (5 pts)

En tant qu'enseignant, je veux **consulter l'historique complet de mes documents, générations et corrections** afin de suivre l'évolution de mes QCM.

**CA :**

- L'historique liste support, date, nombre de questions, statut et corrections appliquées.
- Les données sont strictement isolées entre profils.
- Un filtre par support, date ou statut est disponible.

**Sous-tâches techniques :**

1. Vue agrégée SQL (jointure documents/generations/corrections) exposée via un endpoint API paginé.
2. Filtres côté API traduits en clauses `WHERE` (support, date, statut).
3. Vérification stricte de l'isolation par `user_id` à chaque requête (jamais de requête sans filtre utilisateur).

**Cas à tester :** utilisateur avec un très grand historique (pagination), tentative d'accès à l'historique d'un autre utilisateur (doit être bloquée).

**Definition of Done :** test d'isolation entre 2 comptes utilisateurs passant, sans fuite possible via l'API.

---

## US-24 : Tendance d'utilisation (5 pts)

En tant que système, je veux **suivre les tendances d'utilisation de chaque enseignant** afin de pré-remplir intelligemment les paramètres par défaut.

**CA :**

- Le système enregistre les habitudes récurrentes.
- Ces tendances pré-remplissent automatiquement les paramètres proposés à la génération suivante.
- L'enseignant peut consulter et réinitialiser ces préférences apprises.

**Sous-tâches techniques :**

1. Table `preferences_utilisateur(user_id, cle, valeur, date_maj)`.
2. Mise à jour incrémentale à chaque génération (ex. "dernière valeur utilisée" ou moyenne mobile).
3. Pré-remplissage des formulaires (US-11/US-18) à partir de ces préférences au chargement de l'écran.
4. Écran de gestion permettant de visualiser et réinitialiser les préférences.

**Cas à tester :** nouvel utilisateur sans historique (valeurs par défaut génériques), changement brutal d'habitude (le système doit s'adapter, pas rester figé).

**Definition of Done :** préférence modifiée manuellement puis reflétée au prochain formulaire de génération.

---

## US-25 : Rejeter un QCM entier avec un motif (5 pts)

En tant qu'enseignant, je veux pouvoir **rejeter un QCM entier avec un motif libre** afin que le système évite de reproduire ce défaut à l'avenir.

**CA :**

- Un bouton "Rejeter tout" avec un champ de commentaire libre est disponible.
- Le motif est résumé automatiquement et injecté dans les prompts futurs.
- Un test vérifie qu'après un rejet motivé, la génération suivante tend à corriger le défaut signalé.

**Sous-tâches techniques :**

1. Bouton "Rejeter tout" déclenchant un appel API avec le commentaire libre.
2. Résumé automatique du motif par le LLM et ajout dans `RegleApprise` (US-22) ou une table dédiée `rejets`.
3. Le résumé de rejet est injecté au même titre qu'une règle apprise dans le pipeline de prompt.

**Cas à tester :** commentaire vague ("c'est nul"), commentaire précis et actionnable.

**Definition of Done :** après un rejet motivé et une nouvelle génération, vérification manuelle que le prompt inclut bien le résumé du motif.

---

## US-26 : Noter chaque question individuellement (3 pts)

En tant qu'enseignant, je veux **noter chaque question individuellement** (👍/👎) afin d'affiner progressivement la qualité perçue.

**CA :**

- Chaque question peut être notée indépendamment.
- Les notations sont agrégées et visibles dans l'historique.
- Une notion recevant des notes négatives répétées déclenche une alerte.

**Sous-tâches techniques :**

1. Boutons 👍/👎 par question, appel API à la volée.
2. Table `notations(question_id, user_id, valeur, date)`.
3. Agrégation par notion/support/matière exposée dans l'historique (US-23).
4. Règle d'alerte : taux de 👎 au-delà d'un seuil sur au moins N notations déclenche une alerte visible.

**Cas à tester :** notation multiple sur la même question (doit écraser la précédente, pas s'additionner).

**Definition of Done :** agrégation visible et correcte dans l'écran d'historique.

---

## US-27 : Changement dans les questions / anti-répétition (8 pts)

En tant qu'enseignant, je veux que **deux générations sur le même cours ne donnent jamais les mêmes questions**, afin de pouvoir varier les évaluations.

**CA :**

- Deux générations successives sur le même support et le même profil ne produisent jamais de question identique ou quasi identique (seuil initial : 30 %).
- Un historique des questions déjà posées est stocké et transmis au prompt suivant.
- Un test automatisé vérifie le taux de chevauchement sur 3 générations successives.
- Règle appliquée indépendamment du niveau et de la matière.

**Sous-tâches techniques :**

1. Stockage d'une empreinte (hash sémantique ou embedding) de chaque question générée, liée au support + profil.
2. Injection dans le prompt suivant d'un résumé des "angles déjà couverts" (pas la liste brute complète, pour ne pas saturer le prompt).
3. Calcul de similarité inter-générations (même technique que US-14/21, ou embeddings pour plus de robustesse sémantique).
4. Test automatisé : 3 générations successives sur le même support, calcul du taux de chevauchement.

**Cas à tester :** support très pauvre en notions (risque de répétition difficile à éviter — interagit avec la posture critique US-20), très grand nombre de tentatives successives.

**Definition of Done :** taux de chevauchement mesuré et documenté sous le seuil sur au moins 5 supports testés.

---

## US-28 : Export vers GIFT (5 pts)

En tant qu'enseignant, je veux **exporter un QCM au format GIFT** afin de l'importer dans Moodle.

**CA :**

- Fichier `.txt` conforme à la syntaxe GIFT, incluant le feedback par réponse.
- Échappement correct des caractères spéciaux GIFT.
- Test d'import réussi dans une instance Moodle de test (ou validation via un parseur tiers).

**Sous-tâches techniques :**

1. Fonction de sérialisation JSON QCM → syntaxe GIFT, avec échappement des caractères spéciaux (`~ = # { } :`).
2. Inclusion du feedback par réponse dans la syntaxe GIFT.
3. Test d'import réel dans une instance Moodle de test si disponible, sinon validation via un parseur GIFT open-source.

**Cas à tester :** distracteur contenant un caractère spécial GIFT, question avec accents/caractères Unicode.

**Definition of Done :** fichier généré importé avec succès (ou validé par parseur) sans erreur de syntaxe.

---

## US-29 : Exporter au format XML Moodle (5 pts)

En tant qu'enseignant, je veux **exporter un QCM au format XML Moodle** afin de disposer d'une alternative interopérable.

**CA :**

- Fichier XML conforme au format Moodle (type "multichoice"), bonne réponse marquée, feedback par réponse.
- Le fichier est validé par un parseur XML avant d'être proposé au téléchargement.

**Sous-tâches techniques :**

1. Génération XML via `xml.etree.ElementTree` ou une librairie de templating, respectant le schéma Moodle "multichoice".
2. Validation du XML généré par un parseur avant téléchargement (fail-safe : jamais de fichier invalide livré).
3. Gestion de l'échappement XML (`&`, `<`, `>`).

**Cas à tester :** QCM avec 0 distracteur valide (cas d'erreur à empêcher en amont), caractères spéciaux dans les questions.

**Definition of Done :** fichier XML validé automatiquement avant chaque téléchargement proposé.

---

## US-30 : Télécharger l'export depuis l'interface (2 pts)

En tant qu'enseignant, je veux **télécharger directement l'export depuis l'interface** afin de ne pas manipuler de fichiers serveur.

**CA :**

- Bouton de téléchargement disponible pour chaque format (GIFT, XML).
- Nom de fichier explicite incluant le support et la date.

**Sous-tâches techniques :**

1. Génération du nom de fichier à partir du nom du support (slugifié) + date au format `YYYY-MM-DD`.
2. Bouton de téléchargement Gradio par format, déclenchant la génération à la demande ou servant un fichier en cache.

**Cas à tester :** nom de support avec caractères spéciaux/espaces (doit être proprement slugifié).

**Definition of Done :** fichier téléchargé correctement nommé et exploitable, testé sur au moins 2 formats.

---

**Démo de sprint** : préférence réappliquée automatiquement ; correction d'une erreur qui ne réapparaît plus sur les générations suivantes ; export GIFT importé dans Moodle de test.
