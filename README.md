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
docker compose up -d
```

## Lancer les tests

```bash
# Windows
$env:PYTHONPATH="src"
pytest test/ -v -m

# Linux / macOS
PYTHONPATH=src pytest test/ -v
```

## Variables d'environnement

Voir `.env.sample` pour la liste complète des variables à configurer.

| Variable | Description | Exemple |
|---|---|---|
| `OLLAMA_BASE_URL` | URL de l'instance Ollama | `http://10.22.28.190:11434` |
| `LLM_MODEL` | Modèle LLM à utiliser | `gemma4:12b` |
| `DB_HOST` | Hôte PostgreSQL | `pg` |
| `DB_PORT` | Port PostgreSQL | `5432` |
| `DB_NAME` | Nom de la base | `app_db` |
| `DB_USER` | Utilisateur PostgreSQL | `app_user` |
| `DB_PASSWORD` | Mot de passe PostgreSQL | — |

## Architecture

```
src/
├─ Doc2Quiz/               # Module principal
│   ├─ ui_gradio.py        # Interface Gradio (point d'entrée)
│   ├─ auth.py             # Inscription / connexion
│   ├─ db.py               # Accès base de données
│   ├─ context.py          # Contexte applicatif (session)
│   ├─ service/            # Logique métier
│   ├─ ollama_client/      # Wrapper LLM (Ollama)
│   ├─ storage/            # Accès base de données
│   ├─ Template/           # Templates UI
│   └─ config.py           # Configuration
│
└─ shared/                 # Code partagé
    ├─ document/           # Extraction, segmentation, résumé, détection
    └─ logging.py

test/                      # Tests pytest
sql/                       # Scripts SQL (init.sql)
docker/                    # Dockerfile
docker-compose.yml
.env.sample
requirements.txt
```