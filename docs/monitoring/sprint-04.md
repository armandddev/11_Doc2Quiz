# Sprint 4 — Semaines 8-9 : Qualité adaptative + Anti-répétition + Préférences

**Objectif** : exploiter les retours stockés pour affiner la qualité génération après génération — notation, rejet global, anti-répétition entre sessions, et préférences automatiques.

---

## US-24 : Notation individuelle des questions (3 pts)

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

## US-25 : Rejet d'un QCM entier avec motif (3 pts)

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

## US-26 : Anti-répétition entre générations (8 pts)

En tant qu'enseignant, je veux que **deux générations successives sur le même support ne produisent jamais les mêmes questions**, afin de varier les évaluations.

**CA :**

- Deux générations successives sur le même support et le même profil ne produisent jamais de question identique ou quasi-identique (seuil : 30 %).
- Un historique des questions déjà posées (par support + profil) est stocké en base et pris en compte lors de chaque nouvelle génération.
- Un test automatisé mesure le taux de chevauchement sur 3 générations successives.
- La règle s'applique quel que soit le contexte ou la matière.

**Sous-tâches techniques :**

1. Stockage d'une empreinte sémantique (hash ou embedding léger) de chaque question générée, indexée par `(user_id, document_id)` en NoSQL.
2. Injection dans le prompt d'un résumé des "angles déjà couverts" (pas la liste brute complète, pour ne pas saturer le contexte LLM).
3. Calcul de similarité inter-générations (n-grammes identiques à l'anti-verbatim existant, ou embeddings pour robustesse sémantique accrue).
4. Test automatisé : 3 générations successives sur le même support → mesure du taux de chevauchement par paire.

**Cas à tester :** support avec très peu de notions (risque de répétition difficile à éviter — doit déclencher une alerte plutôt qu'échouer silencieusement), volume important de générations successives (impact performance sur l'injection).

**Definition of Done :** taux de chevauchement mesuré et documenté sous 30 % sur au moins 5 supports testés, test automatisé passant en CI.

---

## US-27 : Préférences automatiques par profil (3 pts)

En tant que système, je veux **mémoriser les habitudes de génération de chaque enseignant** afin de pré-remplir les paramètres au prochain lancement.

**CA :**

- Les paramètres effectivement utilisés à chaque génération (nombre de questions, répartition de difficulté, contexte sélectionné) sont enregistrés.
- Ces tendances pré-remplissent les champs à la prochaine ouverture de l'écran de génération.
- L'enseignant peut consulter et réinitialiser ses préférences depuis son profil.
- Nouvel utilisateur sans historique : valeurs par défaut génériques.

**Sous-tâches techniques :**

1. Document NoSQL `UserPreferences(user_id, clé, valeur, date_maj)` — upsert à chaque génération.
2. Mise à jour incrémentale (dernière valeur ou moyenne mobile sur les 5 dernières sessions).
3. Pré-remplissage des champs Gradio au chargement de l'écran.
4. Endpoints `GET /preferences` et `DELETE /preferences` (réinitialisation complète).

**Cas à tester :** changement brutal d'habitude (le système s'adapte dès la session suivante), réinitialisation → retour aux valeurs génériques.

**Definition of Done :** préférence modifiée puis reflétée au prochain formulaire, réinitialisation testée.

---

**Démo de sprint** : un enseignant note des questions 👎 et rejette un QCM — la génération suivante intègre ces retours via le résumé de contexte en en-tête — deux générations successives sur le même support produisent des questions différentes — ses habitudes de paramétrage sont pré-remplies automatiquement.