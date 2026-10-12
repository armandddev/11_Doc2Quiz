# Sprint 4 — Semaines 8-9 : Qualité adaptative + Anti-répétition + Types de questions

**Objectif** : exploiter les retours stockés pour affiner la qualité génération après génération, introduire les questions Vrai/Faux, et garantir la variété entre sessions.

---

## US-27 : Notation individuelle des questions (3 pts)

En tant qu'enseignant, je veux **noter chaque question individuellement** (👍 / 👎) afin d'alimenter le résumé de contexte et de suivre la qualité perçue par notion.

**CA :**

- Chaque question peut être notée indépendamment depuis l'interface de génération ou depuis l'historique.
- Une notation remplace la précédente (upsert — pas de doublon).
- Les notations sont agrégées par notion et visibles dans l'historique (US-22).
- Une notion cumulant des 👎 répétés (au-delà d'un seuil, sur au moins N notations) déclenche une alerte visible.
- Chaque notation est stockée en base via US-20 (`type: "notation"`) et entre dans le calcul du résumé LLM (US-21).

**Sous-tâches techniques :**

1. Boutons 👍/👎 par question en interface, appel `PATCH /questions/{id}/rating`.
2. Logique d'upsert MongoDB sur le document `Feedback` correspondant.
3. Agrégation par notion/support exposée dans l'historique.
4. Règle d'alerte : taux de 👎 ≥ seuil sur au moins N notations → badge d'alerte dans l'interface.

**Cas à tester :** notation multiple sur la même question (upsert vérifié en test auto), agrégation sur une notion sans aucune notation (affichage neutre).

**Definition of Done :** upsert vérifié en test automatisé, agrégation visible et correcte dans l'écran d'historique.

---

## US-28 : Rejet d'un QCM entier avec motif (3 pts)

En tant qu'enseignant, je veux pouvoir **rejeter un QCM entier avec un commentaire libre** afin que le motif soit intégré dans le résumé de contexte et évité lors des prochaines générations.

**CA :**

- Bouton "Rejeter tout" avec textarea de motif libre disponible sur tout QCM généré.
- Le retour est stocké en base (`type: "rejet"`) via US-20 et déclenche une mise à jour du résumé LLM (US-21).
- Le statut de la génération passe à "rejeté" et est reflété dans l'historique (US-22).

**Sous-tâches techniques :**

1. Bouton "Rejeter tout" + textarea → appel `POST /generations/{id}/reject`.
2. Insertion dans `feedbacks` (`type: "rejet"`, contenu = motif libre) + mise à jour asynchrone du résumé via US-21.
3. Mise à jour du champ `statut` de la génération en base.

**Cas à tester :** commentaire vague ("c'est nul") — le résumé LLM doit quand même produire quelque chose d'actionnable, commentaire très précis.

**Definition of Done :** rejet stocké, statut mis à jour dans l'historique, résumé LLM vérifié manuellement sur la génération suivante.

---

## US-29 : Questions Vrai/Faux (5 pts)

En tant qu'enseignant, je veux pouvoir **générer des questions de type Vrai/Faux** en complément des QCM classiques, afin de diversifier les formes d'évaluation.

**CA :**

- L'enseignant peut choisir, à la génération, d'inclure des questions Vrai/Faux (en proportion libre ou fixe par rapport aux QCM).
- Chaque question Vrai/Faux contient : un énoncé affirmatif, la bonne réponse (Vrai ou Faux), et une explication justifiant la réponse.
- Les énoncés Vrai/Faux ne reprennent pas les phrases du cours telles quelles (même règle anti-verbatim que pour les QCM).
- Le format de sortie est validé par un schéma Pydantic dédié.
- Les questions Vrai/Faux sont exportées dans les formats GIFT et XML Moodle (type "truefalse").

**Sous-tâches techniques :**

1. Schéma Pydantic `QuestionVraiFaux(énoncé, réponse: bool, explication, niveau_difficulté)`.
2. Prompt dédié pour la génération Vrai/Faux : insister sur des énoncés qui ne soient pas trivialement vrais ou faux (éviter les "L'eau bout à 100°C — Vrai").
3. Ajout du sélecteur "Type de questions" dans l'interface de génération : QCM uniquement / Vrai/Faux uniquement / Mixte (avec slider de proportion).
4. Extension de l'anti-verbatim existant aux énoncés Vrai/Faux.
5. Sérialisation GIFT pour le type `TF` et XML Moodle pour le type `truefalse`.
6. Affichage différencié dans l'interface de révision (icône ou badge "V/F").

**Cas à tester :** énoncé Vrai/Faux trop proche du texte source (doit être rejeté par l'anti-verbatim), export GIFT d'un QCM mixte (QCM + Vrai/Faux), génération Vrai/Faux sur un contenu très court.

**Definition of Done :** génération, affichage, révision (US-24) et export fonctionnels pour le type Vrai/Faux, testés sur 3 supports de matières différentes.

---

## US-30 : Anti-répétition entre générations (8 pts)

En tant qu'enseignant, je veux que **deux générations successives sur le même support ne produisent jamais les mêmes questions**, afin de varier les évaluations.

**CA :**

- Deux générations successives sur le même support et le même profil ne produisent jamais de question identique ou quasi-identique (seuil : 30 %).
- Un historique des questions déjà posées (par support + profil) est stocké en base et pris en compte lors de chaque nouvelle génération.
- Un test automatisé mesure le taux de chevauchement sur 3 générations successives.
- La règle s'applique quel que soit le type de question (QCM ou Vrai/Faux) et la matière.

**Sous-tâches techniques :**

1. Stockage d'une empreinte sémantique (hash ou embedding léger) de chaque question générée, indexée par `(user_id, document_id)` en NoSQL — couvre QCM et Vrai/Faux.
2. Injection dans le prompt d'un résumé des "angles déjà couverts" (pas la liste brute complète, pour ne pas saturer le contexte LLM).
3. Calcul de similarité inter-générations (n-grammes ou embeddings).
4. Test automatisé : 3 générations successives sur le même support → mesure du taux de chevauchement par paire.

**Cas à tester :** support avec très peu de notions (doit déclencher une alerte plutôt qu'échouer silencieusement), mélange QCM + Vrai/Faux sur un même support (les deux types doivent être couverts par l'anti-répétition).

**Definition of Done :** taux de chevauchement mesuré et documenté sous 30 % sur au moins 5 supports, test automatisé passant en CI.

---

**Démo de sprint** : un enseignant génère un QCM mixte (QCM + Vrai/Faux), note des questions 👎, rejette le QCM avec un motif — la génération suivante sur le même support intègre ces retours en en-tête et ne reproduit aucune question déjà posée.