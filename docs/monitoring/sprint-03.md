# Sprint 3 — Semaines 6-7 : Niveau 2 (génération autonome, multi-matières)

**Objectif** : le prof n'a plus besoin de paramétrer un modèle de questionnaire — le système décide seul, et ça marche sur n'importe quelle matière.

---

## US-17 : Génération QCM niveau 2 (8 pts)

En tant qu'enseignant, je veux que le système **génère un QCM de façon autonome, sans que je fournisse de modèle de questionnaire**, afin de gagner du temps quelle que soit ma matière.

**CA :**

- Le prof ne renseigne aucun paramètre de structure (pas de "modèle" à remplir) : il fournit uniquement le support, plus éventuellement quelques cases à cocher générales.
- Le système détermine seul, à partir du contenu : le nombre de questions pertinent, la répartition des niveaux de difficulté, et le type de question (restitution vs. application) le mieux adapté à la matière détectée.
- Aucune configuration technique (structure JSON, prompt, etc.) n'est visible ni accessible côté prof.
- Testé sur au moins 5 matières différentes, sans aucune adaptation manuelle du prompt entre les tests.

**Sous-tâches techniques :**

1. Prompt "méta" qui décide en amont : nombre de questions, répartition difficulté, type de question — à partir uniquement du contenu segmenté et du tag discipline (US-08/US-19).
2. Séparer le pipeline niveau 1 (paramétrable) du pipeline niveau 2 (autonome) via une fonction d'orchestration commune avec un mode `autonome: bool`.
3. Définir des règles de décision par défaut si aucune préférence apprise n'existe encore (lien futur avec US-24 en Sprint 4).
4. Journaliser les décisions prises (nombre de questions choisi, pourquoi) pour pouvoir les expliquer côté UI si besoin.

**Cas à tester :** support très riche (le système doit-il limiter le nombre de questions ?), support avec une seule notion.

**Definition of Done :** testé sur 5 matières différentes sans changement de prompt entre les tests, résultats documentés.

---

## US-18 : Interface de lancement de génération (5 pts)

En tant qu'enseignant, je veux une **interface ultra-simplifiée** (upload + texte libre ou cases à cocher) afin de lancer une génération sans configuration technique.

**CA :**

- L'écran de génération ne propose que : upload du support + 2-3 cases à cocher optionnelles + un champ texte libre optionnel.
- Aucun champ n'est obligatoire à part l'upload.
- Un enseignant non technique doit pouvoir lancer une génération complète en moins de 30 secondes sans explication préalable.

**Sous-tâches techniques :**

1. Nouvel écran Gradio distinct de l'écran niveau 1 (US-11), avec un minimum de champs.
2. Appel à l'API en mode "autonome" (cf. US-17).
3. Test utilisateur informel : chronométrer un enseignant non technique du clic d'upload jusqu'au résultat affiché.

**Cas à tester :** utilisateur qui ne coche aucune case (doit quand même fonctionner), champ texte libre contradictoire avec le contenu du support.

**Definition of Done :** temps mesuré < 30 secondes sur au moins 3 testeurs différents.

---

## US-19 : Détection de matière niveau 2 (5 pts)

En tant que système, je veux une **détection de discipline généralisée et ouverte** (pas limitée à une liste fermée de matières) afin de fonctionner sur des matières imprévues.

**CA :**

- La détection (US-08) est étendue via une classification ouverte plutôt qu'une liste figée de matières.
- Les contenus hybrides (ex. SVT avec calculs de génétique) combinent plusieurs stratégies de génération sans erreur.
- Testé explicitement sur des matières non prévues initialement : pas de crash, pas de génération dégradée silencieuse.

**Sous-tâches techniques :**

1. Remplacer/étendre la liste fermée de l'US-08 par un prompt de classification ouvert (le LLM propose lui-même un ou plusieurs tags).
2. Gérer le cas multi-tags (ex. `["SVT", "calcul"]`) en combinant plusieurs prompts spécialisés.
3. Étendre le jeu de test de l'US-08 avec des matières non prévues initialement.

**Cas à tester :** contenu dans une discipline absente du jeu de test initial (ex. philosophie, arts plastiques).

**Definition of Done :** aucun crash sur les nouvelles matières testées, classification cohérente validée manuellement.

---

## US-20 : Autocritique contenu (5 pts)

En tant qu'enseignant, je veux que le système **m'alerte si mon support est trop pauvre pour générer un QCM de qualité**, quelle que soit la matière, afin d'éviter des questions artificielles.

**CA :**

- Quand le contenu est jugé insuffisant, aucune génération dégradée n'est produite silencieusement.
- Un message explicite précise la raison exacte.
- Une proposition alternative chiffrée est faite.
- Ce contrôle s'applique quelle que soit la matière détectée.

**Sous-tâches techniques :**

1. Définir une métrique "richesse du contenu" (nombre de concepts distincts / longueur du texte), réutilisable quelle que soit la discipline.
2. Définir un seuil minimal de concepts par question demandée (valeur initiale à ajuster avec des tests réels).
3. Générer le message d'alerte avec le nombre exact de concepts détectés + une proposition de nombre de questions alternative calculée automatiquement.
4. Exécuter ce contrôle **avant** l'appel de génération de QCM, pour éviter un appel LLM inutile.

**Cas à tester :** support riche mais demande de 50 questions, support pauvre avec demande de seulement 3 questions (ne doit pas bloquer inutilement).

**Definition of Done :** message d'alerte vérifié sur au moins 3 cas de contenu insuffisant, avec proposition alternative cohérente.

---

## US-21 : Mise en place d'anti-verbatim généralisé (5 pts)

En tant que système, je veux que **l'anti-verbatim fonctionne sur tous types de contenus** afin de garantir le Niveau 2 sur toute matière.

**CA :**

- Un jeu de test couvrant au moins 5 matières différentes confirme qu'aucune question générée ne dépasse le seuil de similarité défini (US-14).
- Les faux positifs sont mesurés, et le seuil est ajusté si le taux dépasse 10 %.

**Sous-tâches techniques :**

1. Réexécuter le test de similarité de l'US-14 sur un corpus élargi (texte littéraire, code, contenu juridique inclus).
2. Ajuster l'algorithme si nécessaire : les n-grammes se comportent différemment sur du code/formules que sur du texte narratif (prévoir une normalisation adaptée par type de contenu).
3. Mesurer et documenter le taux de faux positifs.

**Cas à tester :** citation de loi (contenu juridique) où une reformulation totale changerait le sens — cas limite à documenter explicitement.

**Definition of Done :** taux de faux positifs mesuré et sous les 10 %, sinon seuil ajusté et re-testé.

---

**Démo de sprint** : upload d'un support dans une matière non testée auparavant → génération complète sans aucun paramétrage technique, ou alerte explicite si le contenu est trop pauvre.
