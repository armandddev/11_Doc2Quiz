# 11_Doc2Quiz

Un outil pédagogique permettant aux enseignants de transformer instantanément leurs supports de cours en questionnaires d'auto-évaluation interactifs.

## Prérequis

- Python 3.12
- Docker & Docker Compose
- Une instance Ollama accessible (locale ou distante)

## Installation

```bash
pip install -r requirements.txt
```

Copier le fichier d'environnement et le compléter :

```bash
cp .env.sample .env
```

## Lancement

### Sans Docker

```bash
# Windows
$env:PYTHONPATH="src"
python src/Doc2Quiz/ui_gradio.py

# Linux / macOS
PYTHONPATH=src python src/Doc2Quiz/ui_gradio.py
```

### Avec Docker

```bash
docker compose build
docker compose up -d
```

## Lancer les tests

```bash
# Windows
$env:PYTHONPATH="src"
pytest test/ -v

# Linux / macOS
PYTHONPATH=src pytest test/ -v
```

## Variables d'environnement

Voir `.env.sample` pour la liste complète des variables à configurer.

| Variable | Description | Exemple |
|---|---|---|
| `OLLAMA_BASE_URL` | URL de l'instance Ollama | `http://10.22.28.190:11434` |
| `OLLAMA_DEFAULT_LLM` | Modèle LLM à utiliser | `gemma4:26b` |
| `OLLAMA_DEFAULT_VLM` | Modèle VLM (vision) | `llava:13b` |
| `OLLAMA_TIMEOUT_S` | Timeout des requêtes Ollama (s) | `600` |
| `MONGO_URI` | URI de connexion MongoDB | `mongodb://mongo:27017` |
| `MONGO_DB_NAME` | Nom de la base de données | `doc2quiz` |

## Architecture

```
src/
├─ Doc2Quiz/               # Module principal
│   ├─ ui_gradio.py        # Interface Gradio (point d'entrée)
│   ├─ auth.py             # Inscription / connexion
│   ├─ db.py               # Connexion MongoDB (Motor async)
│   ├─ context.py          # Contexte applicatif (session Gradio)
│   ├─ config.py           # Configuration (pydantic-settings)
│   ├─ service/            # Logique métier
│   │   ├─ core.py         # Pipeline : génération et extension de QCM
│   │   ├─ feedback_service.py  # Retours utilisateur
│   │   └─ anti_verbatim.py    # Détection de copie verbatim
│   ├─ ollama_client/      # Wrapper HTTP vers Ollama
│   ├─ storage/            # Accès MongoDB (générations, feedbacks)
│   └─ Template/           # Templates HTML pour l'UI
│
└─ shared/                 # Code partagé
    ├─ document/           # Extraction PDF/Markdown, segmentation
    └─ logging.py

test/                      # Tests pytest (pytest-asyncio + unittest.mock)
docker/                    # Dockerfile
docker-compose.yml
.env.sample
requirements.txt
```