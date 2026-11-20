# Doc2Quiz — Onboarding Claude

> Colle ce fichier en entier au début d'une nouvelle conversation avec Claude pour qu'il reprenne le contexte du projet sans questions inutiles.

---

## Présentation du projet

**Doc2Quiz** est une application web qui permet à un enseignant d'uploader un support de cours (PDF ou Markdown), de le segmenter automatiquement en sections, et de générer un QCM par section via un LLM local (Ollama). Les étudiants peuvent ensuite s'entraîner sur ces QCM.

**Équipe** : projet SAÉ IUT — développement en sprints agiles.  
**Repo** : non cloné dans les sessions Claude — toujours passer les fichiers en attachement.

---

## Stack technique

| Couche | Techno |
|---|---|
| **Interface** | Gradio (Python) — mono-process, `async def` pour les handlers |
| **LLM / VLM** | Ollama local (`OLLAMA_DEFAULT_LLM`, `OLLAMA_DEFAULT_VLM`) sur `10.22.28.190:11434` |
| **Base de données** | MongoDB + Motor (driver async Python) |
| **Config** | pydantic-settings + `.env` + `config.yaml` |
| **Tests** | pytest + pytest-asyncio ( jamais de unittest.mock) |
| **Conteneurisation** | Docker Compose — container app `sae_Doc2Quiz` sur port `7860` |
| **CI** | GitHub Actions |

---

## Architecture des fichiers clés

```
src/
├── Doc2Quiz/
│   ├── config.py                  # Settings (pydantic-settings, .env + config.yaml)
│   ├── context.py                 # AppContext + UserContext (état de session Gradio)
│   ├── ui_gradio.py               # Interface Gradio — handlers async
│   ├── ollama_client/
│   │   ├── ollama_wrapper.py      # Client HTTP sync (urllib) vers Ollama
│   │   └── async_wrapper.py       # Client HTTP async (httpx) — US-34
│   ├── service/
│   │   ├── core.py                # Pipeline principal : generation_qcm(), expand_qcm()
│   │   ├── feedback_service.py    # reject_generation(), correct_question(), rate_question()
│   │   ├── import_service.py      # import_qcm_from_file() — US-25
│   │   ├── qcm_parser.py          # parse_gift(), parse_moodle_xml() — US-25
│   │   └── anti_verbatim.py       # is_too_similar() — shingles n-grammes
│   └── storage/
│       ├── feedback_storage.py    # save_feedback(), upsert_rating()
│       └── generation_storage.py  # save_generation(), get_generations_for_user()
├── shared/
│   ├── logging.py
│   ├── document.py                # extractFromPdf(), extractFromMd()
│   └── qcm.py                     # enregistrer_modification()
├── pages/                         # Composants Gradio par page
│   ├── page_profil.py
│   ├── page_QCM.py
│   └── ...
└── db.py                          # get_db() — connexion Motor MongoDB
```

---

## Collections MongoDB

```python
# users
{ _id, email, password_hash, name, role: "teacher"|"student", created_at }

# generations
{
  _id, user_id, document_name, level, revision,
  source: "generation" | "import",   # "import" pour les QCM importés (US-25)
  question_ids: [str],
  date
}

# questions
{ _id, generation_id, user_id, index, question, options, correct, feedbacks, type, section, date }

# feedbacks
{ _id, user_id, generation_id, question_id (nullable), type: "rejet"|"correction"|"notation", contenu, date }

# context_summaries  ← à créer en US-20
{ _id, user_id, résumé, date_maj, nb_retours_utilisés }
```

---

## Schéma interne QCM (invariant dans tout le code)

```python
{
    "question":  str,
    "options":   ["A. …", "B. …", "C. …", "D. …"],   # exactement 4
    "correct":   "A" | "B" | "C" | "D",
    "feedbacks": [str, str, str, str],                  # dans l'ordre des options
    "type":      "qcm",
    # champs optionnels : "section" (dict), "_id" (str ObjectId), "is_new" (bool)
}
```

---

## État d'avancement par sprint

### ✅ Sprint 0 — Cadrage
US-01 à US-04 : cahier des charges, maquettes, repo Git, backlog.

### ✅ Sprint 1 — Fondations
- **US-05** Upload PDF (pdfplumber/PyMuPDF, détection scan)
- **US-06** Upload Markdown (parsing AST, hiérarchie titres)
- **US-07** Segmentation (sections avec id + résumé)
- **US-08** Détection matière (heuristique + fallback LLM)
- **US-09** Client REST Ollama (`ollama_wrapper.py` — sync, urllib, retry/backoff, logs structurés)
- **US-10** Docker Compose (app + MongoDB + Ollama)
- **US-11** Interface upload Gradio

### ✅ Sprint 2 — Niveau 1 complet
- **US-12** Génération QCM niveau 1 (schéma JSON strict, self-repair 2 tentatives)
- **US-13** Exercices de calcul réel (prompt dédié si matière = calcul)
- **US-14** Anti-verbatim algorithmique (shingles 4-grammes, seuil configurable dans `config.yaml`)
- **US-15** Profil persistant (MongoDB, bcrypt, isolation par `user_id`)
- **US-16** Interface édition/validation QCM

### ✅ Sprint 3 — Partiellement terminé

| US | Titre | Statut |
|---|---|---|
| US-17 | Migration NoSQL (MongoDB + Motor) | ✅ Fait |
| US-19 (= US-22 interne) | Stockage des retours (feedbacks) | ✅ Fait |
| US-22 (= US-23 interne) | Export GIFT + XML Moodle | ✅ Fait |
| US-23 (= US-24 interne) | Validation question par question | ✅ Fait |
| US-24 (= US-25 interne) | Ajout de questions supplémentaires | ✅ Fait |
| US-25 | **Import QCM (GIFT + XML) dans le profil** | 🔶 En cours |
| US-21 | Historique des générations sur le profil | 🔶 En cours |
| US-20 | Résumé LLM + injection en en-tête de prompt | 🔶 En cours |
| US-18 | Contexte : consultation + réinitialisation | ⬜ À faire (dépend de US-20) |
| US-37 | Comparaison génération avec/sans lecture document | 🔶 En cours |

### ⬜ Sprint 4 — Pas commencé
US-26 (agrégation 👍/👎), US-27 (badge rejeté), US-28 (Vrai/Faux), US-29 (anti-répétition inter-générations)

### ⬜ Sprint 5 — US-34 en parallèle
- **US-34** Parallélisation LLM (`asyncio.gather` + `Semaphore`) — `async_wrapper.py` écrit, reste à câbler dans `core.py`

---

## Fichiers produits lors des sessions précédentes (à intégrer sur la branche)

Ces fichiers sont **écrits mais pas encore commités**. Les demander à Armand ou les recréer si besoin.

### US-25 — Import QCM
| Fichier | Destination |
|---|---|
| `generation_storage.py` | `src/Doc2Quiz/storage/generation_storage.py` — remplace l'existant (ajoute `source`, `get_generations_for_user()`, `get_questions_for_generation()`) |
| `qcm_parser.py` | `src/Doc2Quiz/service/qcm_parser.py` — nouveau (parsers GIFT + XML Moodle) |
| `import_service.py` | `src/Doc2Quiz/service/import_service.py` — nouveau (`import_qcm_from_file()`) |
| `ui_gradio_patch.py` | patch documenté sur `ui_gradio.py` — 5 changements numérotés |
| `test_qcm_parser.py` | `test/test_qcm_parser.py` — 20 tests unitaires |

### US-34 — Async wrapper
| Fichier | Destination |
|---|---|
| `async_wrapper.py` | `src/Doc2Quiz/ollama_client/async_wrapper.py` — nouveau (client httpx async, LLM + VLM) |
| `config.py` | `src/Doc2Quiz/config.py` — ajouter `llm_max_concurrent: int = 3` |

---

## Points techniques importants

**Gradio + async** : les handlers `async def` tournent directement dans la boucle asyncio. Les appels bloquants (Ollama sync) **doivent** être wrappés avec `asyncio.to_thread()` sinon l'app se fige.

**OllamaWrapper** (sync, `ollama_wrapper.py`) : utilisé partout actuellement. Paramètres dans `.env` :
```
OLLAMA_BASE_URL=http://10.22.28.190:11434
OLLAMA_DEFAULT_LLM=gemma4:26b
OLLAMA_DEFAULT_VLM=...
OLLAMA_DEFAULT_EMBED=...
OLLAMA_TIMEOUT_S=600
OLLAMA_MAX_RETRIES=3
OLLAMA_RETRY_BACKOFF_S=1.0
```

**Isolation stricte** : toutes les requêtes MongoDB filtrent obligatoirement par `user_id`. Ne jamais exposer les données d'un profil à un autre.

**AppContext** (dataclass, `context.py`) : état de session Gradio transmis via `gr.State`. Champs importants :
```python
@dataclass
class AppContext:
    user: UserContext | None = None
    document_id: int | None = None
    generation_id: str | None = None   # ajouté US-22
    sections: list = field(default_factory=list)
    pending_file: object = None
    pending_revision: str = "Les deux"
    pending_difficulty: str = ""
```

**Ollama cold start** : le premier appel après inactivité peut prendre 300–600s (chargement du modèle en RAM/VRAM). Pas un bug, c'est normal.

---
