# ---------- Builder ----------
FROM python:3.12-slim AS builder
WORKDIR /app
COPY pyproject.toml poetry.lock* ./
RUN pip install --upgrade pip && \
    pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --only main

# ---------- Runtime ----------
FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY . /app
ENV PYTHONUNBUFFERED=1

EXPOSE 7860
CMD ["python", "-m", "gradio", "src/Doc2Quiz/ui_gradio.py"]