# Sprint 1 — Semaines 2-3 : Fondations techniques + amorce Niveau 1

**Objectif** : la donnée circule de bout en bout (upload → texte segmenté → discipline détectée), et l'infra tourne.

---

## US-05 : Upload PDF (5 pts)

En tant qu'enseignant, je veux **uploader un support PDF** afin d'en extraire le texte exploitable pour la génération.

**CA :**

- Extraction du texte brut et de la structure (titres, sous-titres) via une lib type `pdfplumber`/`PyMuPDF`.
- Les PDF scannés (image pure) sont détectés et signalés par un message explicite ("PDF non exploitable, scan détecté, veuillez utiliser un OCR au préalable"), sans plantage de l'application.
- Le texte extrait est stocké, associé au document et horodaté.
- Testé sur au moins 3 PDF réels de matières différentes (ex. maths, lettres, sciences) avec validation manuelle de la qualité d'extraction.

**Sous-tâches techniques :**

1. Choix de la lib : `PyMuPDF` (rapide, bonne mise en page) vs `pdfplumber` (meilleur sur les tableaux) — trancher via un test rapide sur des supports réels.
2. Extraction page par page en conservant l'ordre de lecture (attention aux PDF en 2 colonnes qui peuvent mélanger l'ordre si extraction naïve).
3. Détection heuristique des titres (taille de police, gras, position) pour préparer la segmentation (US-07).
4. Détection PDF scanné : ratio texte extrait / nombre de pages proche de zéro alors que le fichier n'est pas vide → déclenche le message d'erreur dédié.
5. Gestion des cas limites : PDF protégé par mot de passe, PDF corrompu, PDF sans texte.
6. Stockage du texte brut + métadonnées (nombre de pages, taille fichier, date d'upload).

**Cas à tester en particulier :** PDF multi-colonnes, PDF avec formules mathématiques (Unicode vs image), PDF volumineux (>50 pages, test de perf).

**Definition of Done :** testé sur 3 PDF réels de matières différentes + tous les cas d'échec renvoient un message clair (pas de 500 ni de plantage silencieux).

---

## US-06 : Upload d'un fichier Markdown (3 pts)

En tant qu'enseignant, je veux **uploader un fichier Markdown** afin d'en extraire le contenu structuré.

**CA :**

- Parsing des titres (`#`, `##`, `###`) pour construire une arborescence de sections.
- Le niveau hiérarchique de chaque section est conservé.
- Les blocs de code et les formules (LaTeX inline, ex. `$...$`) ne sont pas cassés par le parsing.

**Sous-tâches techniques :**

1. Utiliser une librairie de parsing en AST (`markdown-it-py` ou `mistune`) plutôt qu'une extraction par regex, plus robuste sur les cas limites.
2. Construire l'arborescence de sections à partir des niveaux de titres (h1 > h2 > h3).
3. Préserver comme blocs "non segmentables" : blocs de code (` ``` `) et formules LaTeX (`$...$`, `$$...$$`).
4. Gérer le cas d'un éventuel front-matter YAML en tête de fichier (à ignorer ou extraire comme métadonnées, pas comme contenu de cours).

**Cas à tester :** Markdown avec titres non hiérarchiques (h3 direct sans h1/h2), fichier sans aucun titre, fichier avec tableaux Markdown.

**Definition of Done :** parsing testé sur au moins 3 fichiers Markdown réels de structures différentes, sans perte de contenu.

---

## US-07 : Segmentation du texte extrait (3 pts)

En tant que système, je veux **segmenter le texte extrait par notion/section** afin de générer des QCM ciblés plutôt qu'un bloc unique.

**CA :**

- Chaque section détectée reçoit un identifiant unique et un résumé automatique (1-2 phrases).
- Le découpage fonctionne aussi bien sur un support avec titres explicites que sur un support peu structuré (repli sur un découpage par paragraphes/longueur si aucun titre n'est détecté).
- Une même notion peut être rattachée à plusieurs sections si le contenu du cours le justifie.

**Sous-tâches techniques :**

1. Définir la structure de données `Section` (id, titre, niveau hiérarchique, texte, résumé, notion(s) associées).
2. Algorithme de repli : si aucun titre détecté, découper par blocs de N mots ou par rupture de paragraphe significative.
3. Génération du résumé automatique via un appel léger au LLM (fallback : extraction des premières phrases si le LLM est indisponible).
4. Association section ↔ notion en many-to-many (table de liaison), pas un simple champ, pour permettre qu'une notion traverse plusieurs sections.

**Cas à tester :** cours très court (1 seule section), cours très long (50+ sections), cours avec sections de titres dupliqués.

**Definition of Done :** chaque section obtient un id unique et un résumé, testé sur les mêmes supports que l'US-05/06.

---

## US-08 : Détection matière niveau 1 (5 pts)

En tant que système, je veux **détecter automatiquement la discipline et la nature du contenu** (théorique vs. calcul/exercice) afin d'adapter la génération sans intervention du prof.

**CA :**

- Détection de la présence de calculs/formules (symboles mathématiques, LaTeX, opérateurs) vs. contenu théorique.
- Attribution automatique d'un ou plusieurs tags de discipline (maths, sciences, lettres, histoire, droit, etc.), sans configuration manuelle.
- Taux de détection correcte validé sur un jeu de test d'au moins 10 supports variés, avec un objectif de ≥ 80 % de bonnes détections.
- En cas d'ambiguïté, le système ne bloque jamais : il applique une stratégie de génération "générique" par défaut.

**Sous-tâches techniques :**

1. Définir une liste de tags de discipline de départ + un mécanisme d'extension (pas une liste figée en dur).
2. Heuristique légère : densité de symboles mathématiques/LaTeX + dictionnaire de mots-clés par discipline.
3. Fallback : appel LLM de classification si l'heuristique a une confiance faible (score sous un seuil défini).
4. Stockage du tag au niveau du document ET de chaque section (un cours peut être hybride, ex. SVT + calculs).
5. Constituer le jeu de test de 10 supports variés avec une "vérité terrain" pour mesurer le taux de réussite.

**Cas à tester :** cours hybride (SVT avec calculs de génétique), cours très bref sans contenu discriminant.

**Definition of Done :** ≥ 80 % de bonnes détections sur le jeu de test, résultat documenté dans un rapport de test.

---

## US-09 : Appel REST vers Ollama (5 pts)

En tant que backend, je veux un **client REST vers Ollama** afin d'interroger le modèle local de façon fiabilisée.

**CA :**

- Gestion du timeout et des retries (au moins 2 tentatives) en cas d'échec réseau.
- Chaque appel est loggé (prompt envoyé, temps de réponse, succès/échec) pour permettre debug et suivi de charge.
- Testé avec un mock du serveur simulant latence et erreurs.
- Le nom exact du modèle utilisé est un paramètre de configuration (pas en dur), pour pouvoir changer de modèle sans réécrire le code.

**Sous-tâches techniques :**

1. Wrapper HTTP (`requests` ou `httpx`) autour de l'API Ollama (`/api/generate` ou `/api/chat`).
2. Configuration externalisée (`.env`/config) : URL du serveur, nom du modèle, timeout par défaut.
3. Retries avec backoff (ex. 2 tentatives, délai 2s puis 4s) sur erreur réseau/timeout.
4. Gestion différenciée des erreurs : connexion refusée, timeout, modèle introuvable, réponse malformée.
5. Logs structurés : prompt (ou hash si trop long), taille de réponse, latence, statut.
6. Privilégier le non-streaming pour un JSON structuré (besoin de la réponse complète avant parsing).
7. Mock du serveur pour les tests unitaires, sans dépendance à un vrai serveur en CI.

**Definition of Done :** module testable et testé isolément, sans nécessiter un serveur Ollama réel en CI.

---

## US-10 : Environnement Docker (5 pts)

En tant qu'équipe, je veux un **environnement Docker Compose complet** (backend, frontend, DB, Ollama) afin de garantir la reproductibilité.

**CA :**

- `docker-compose up` démarre l'ensemble des services en une seule commande.
- Le README documente les prérequis matériels (RAM/GPU nécessaires) et la procédure de démarrage.
- Un healthcheck vérifie que chaque service est up avant de considérer le déploiement réussi.

**Sous-tâches techniques :**

1. Dockerfile backend (FastAPI/Python).
2. Dockerfile frontend (Gradio), ou conteneur unique si l'app est mono-process.
3. Service DB (SQLite ou Postgres) avec volume nommé.
4. Service Ollama avec volume dédié pour les modèles téléchargés (sinon retéléchargement à chaque rebuild).
5. Réseau Docker interne backend ↔ Ollama ↔ DB.
6. Variables d'environnement centralisées (`.env`).
7. Healthchecks par service (endpoint `/health` backend, ping Ollama).
8. Script d'initialisation/migration DB au premier lancement.
9. README détaillant prérequis matériels et commande `ollama pull` du modèle.

**Definition of Done :** `docker-compose up` fonctionne sur une machine "propre", testé par une personne n'ayant pas fait le setup initial.

---

## US-11 : Interface d'upload (5 pts)

En tant qu'enseignant, je veux une **interface minimale d'upload** afin de lancer une extraction de mon support.

**CA :**

- Formulaire permettant d'uploader un PDF ou Markdown et de lancer l'extraction.
- Un indicateur de progression est visible pendant l'extraction/segmentation.
- La liste des notions détectées (US-07) est affichée avant toute génération.

**Sous-tâches techniques :**

1. Composant Gradio d'upload de fichier, limité aux extensions `.pdf` et `.md`.
2. Appel à l'API backend au moment de l'upload (ou via un bouton "Analyser").
3. Indicateur de progression pendant l'extraction + segmentation.
4. Affichage de la liste des notions détectées (nom + résumé court).
5. Remontée lisible des erreurs backend, sans stack trace visible côté utilisateur.
6. Limite de taille de fichier (ex. 20 Mo) avec message explicite en cas de dépassement.

**Definition of Done :** un enseignant non technique peut uploader un fichier et voir le résultat de la segmentation sans qu'aucune erreur ne reste cachée uniquement dans les logs serveur.

---

**Démo de sprint** : upload d'un PDF/Markdown → texte segmenté et discipline détectée visibles, Ollama joignable via l'app.
