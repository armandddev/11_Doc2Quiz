FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt ./
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY . /app
ENV PYTHONUNBUFFERED=1

EXPOSE 7860
CMD ["python", "-m", "gradio", "src/Doc2Quiz/ui_gradio.py"]