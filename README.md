# 11_Doc2Quiz

Un outil pédagogique permettant aux enseignants de transformer instantanément leurs supports de cours en questionnaires d'auto-évaluation interactifs.

## Prérequis

- Python 3.12

## Installation

```bash
pip install gradio pymupdf mistune pydantic pytest
```

Copier le fichier d'environnement et le compléter :

```bash
cp .env.sample .env
```

## Lancement

```bash
cd C:\...\11_Doc2Quiz
$env:PYTHONPATH="src"
python src/Doc2Quiz/ui_gradio.py
```

## Lancer les tests

```bash
$env:PYTHONPATH="src"
pytest test/ -v
```

## Architecture

```
src/
├─ Doc2Quiz/               # Module principal
│   ├─ ui_gradio.py        # Interface Gradio (point d'entrée)
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
docker/                    # Dockerfile
docker-compose.yml
```