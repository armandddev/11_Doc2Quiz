# Sprint 4 : Qualité adaptative + Anti-répétition + Types de questions

**Objectif** : exploiter les retours stockés pour affiner la qualité génération après génération, introduire les questions Vrai/Faux, et garantir la variété entre sessions.

---

## US-26 : Agrégation et alertes sur les notations (3 pts)

En tant qu'enseignant, je veux **voir la qualité agrégée de mes questions par notion** et être alerté quand une notion pose systématiquement problème, afin d'identifier les zones faibles de mes supports.

> Les boutons 👍/👎 et leur stockage sont posés en US-20 (Sprint 3). Cette US couvre uniquement la couche analytique : agréger ces données et en faire quelque chose d'utile.

**CA :**

- Les notations sont agrégées par notion et par support, visibles dans l'historique (US-22) : taux d'approbation, nombre de notations, évolution dans le temps.
- Une notion cumulant des 👎 au-delà d'un seuil (sur au moins N notations) déclenche un badge d'alerte visible dans l'historique et lors de la prochaine génération sur ce support.
- L'agrégation couvre les deux types de questions (QCM et Vrai/Faux).

**Sous-tâches techniques :**

1. Pipeline d'agrégation MongoDB : `group by (user_id, notion)` sur la collection `feedbacks`, calcul du taux de 👎.
2. Endpoint `GET /analytics/notions` exposant le tableau agrégé (notion, taux_approbation, nb_notations).
3. Règle d'alerte : taux 👎 ≥ seuil sur ≥ N notations → champ `alerte: true` sur le document notion en base.
4. Affichage du badge d'alerte dans l'historique et dans l'écran de génération si une notion alertée est détectée dans le support.

**Cas à tester :** notion sans aucune notation (affichage neutre, pas de division par zéro), alerte déclenchée puis réinitialisée après correction (badge doit disparaître).

**Definition of Done :** agrégation correcte vérifiée en test automatisé, badge d'alerte visible manuellement dans les deux points d'accès.

---

## US-27 : Suivi et affichage des rejets dans l'historique (2 pts)

En tant qu'enseignant, je veux **voir clairement le statut et le motif de rejet de mes QCM** dans l'historique, afin de suivre l'évolution de la qualité de mes générations.

> Le stockage du rejet et la mise à jour du résumé LLM sont couverts par US-20 et US-21 (Sprint 3). Cette US couvre uniquement la visibilité dans l'interface.

**CA :**

- Dans l'historique (US-22), les QCM rejetés affichent un badge "Rejeté" avec le motif résumé (extrait du `ContextSummary`) en tooltip ou en ligne.
- Un filtre `statut=rejeté` est disponible dans l'historique.
- Un QCM rejeté peut être rouvert, consulté et régénéré depuis l'historique.

**Sous-tâches techniques :**

1. Champ `statut` et `motif_résumé` dans le document `generation` déjà mis à jour par US-20 — ici on les exploite en lecture.
2. Badge "Rejeté" dans le tableau de l'historique avec tooltip affichant le motif résumé.
3. Filtre `?statut=rejeté` dans l'endpoint `GET /generations` (extension du filtre existant US-22).
4. Bouton "Régénérer" depuis la vue détaillée d'un QCM rejeté → relance le pipeline sur le même document source.

**Cas à tester :** QCM rejeté sans motif saisi (badge "Rejeté" sans tooltip), régénération depuis un rejet sur un document source entre-temps supprimé (message d'erreur explicite).

**Definition of Done :** badge, filtre et régénération fonctionnels, testés manuellement sur 2 QCM rejetés.

---

## US-28 : Questions Vrai/Faux (5 pts)

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

## US-29 : Anti-répétition entre générations (8 pts)

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