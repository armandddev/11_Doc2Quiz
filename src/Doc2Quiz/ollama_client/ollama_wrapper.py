"""
ollama_wrapper.py
=================
Client REST robuste et typé pour l'API HTTP d'Ollama (IUT).

Configuration via .env (à la racine du projet) :
    OLLAMA_BASE_URL        = http://10.22.28.190:11434
    OLLAMA_DEFAULT_LLM     = gemma4:26b
    OLLAMA_DEFAULT_VLM     = qwen3-vl:8b-instruct
    OLLAMA_DEFAULT_EMBED   = qwen3-embedding:0.6b
    OLLAMA_TIMEOUT_S       = 120.0
    OLLAMA_MAX_RETRIES     = 3
    OLLAMA_RETRY_BACKOFF_S = 1.0
"""

from __future__ import annotations

import base64
import json
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, List, Mapping, Optional, Sequence, Union
import urllib.error
import urllib.request
from urllib.parse import urljoin

from dotenv import find_dotenv, load_dotenv

# find_dotenv() remonte l'arborescence depuis le CWD jusqu'à trouver le .env
# — fonctionne peu importe depuis quel dossier on lance le script.
load_dotenv(find_dotenv())

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lecture des variables obligatoires du .env
# _require() lève ValueError immédiatement si une clé est absente,
# sans aucune valeur en dur dans le code.
# ---------------------------------------------------------------------------

def _require(key: str) -> str:
    """Lit une variable d'env obligatoire — lève ValueError si absente."""
    val = os.getenv(key)
    if val is None:
        raise ValueError(f"Variable d'environnement manquante dans le .env : {key}")
    return val


_BASE_URL    = _require("OLLAMA_BASE_URL")
_MODEL_LLM   = _require("OLLAMA_DEFAULT_LLM")
_MODEL_VLM   = _require("OLLAMA_DEFAULT_VLM")
_MODEL_EMBED = _require("OLLAMA_DEFAULT_EMBED")
_TIMEOUT     = float(os.getenv("OLLAMA_TIMEOUT_S",      "120.0"))
_MAX_RETRIES = int(os.getenv("OLLAMA_MAX_RETRIES",       "3"))
_BACKOFF     = float(os.getenv("OLLAMA_RETRY_BACKOFF_S", "1.0"))


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class OllamaError(RuntimeError):
    """Erreur générique Ollama."""

class OllamaConnectionError(OllamaError):
    """Impossible de joindre le serveur."""

class OllamaResponseError(OllamaError):
    """Réponse HTTP/JSON invalide ou inattendue."""

class OllamaHTTPError(OllamaResponseError):
    """Erreur HTTP connue (4xx / 5xx)."""
    def __init__(self, status: int, message: str) -> None:
        super().__init__(f"HTTP {status}: {message}")
        self.status = status


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class OllamaGenerateResult:
    response:          str
    model:             Optional[str]  = None
    done:              Optional[bool] = None
    total_duration:    Optional[int]  = None
    load_duration:     Optional[int]  = None
    prompt_eval_count: Optional[int]  = None
    eval_count:        Optional[int]  = None

@dataclass(frozen=True, slots=True)
class OllamaChatMessage:
    role:    str   # "system" | "user" | "assistant"
    content: str

@dataclass(frozen=True, slots=True)
class OllamaChatResult:
    message:        OllamaChatMessage
    model:          Optional[str]  = None
    done:           Optional[bool] = None
    total_duration: Optional[int]  = None
    eval_count:     Optional[int]  = None

@dataclass(frozen=True, slots=True)
class OllamaStreamChunk:
    token: str
    done:  bool
    model: Optional[str] = None


# ---------------------------------------------------------------------------
# Wrapper
# ---------------------------------------------------------------------------

class OllamaWrapper:
    """
    Client REST pour l'API HTTP d'Ollama (IUT).
    URL et modèles chargés depuis le .env automatiquement.

    Endpoints
    ---------
    GET  /api/version  → is_server_running()
    POST /api/generate → generate_text(), generate_with_image(), generate_stream()
    POST /api/chat     → chat()
    POST /api/embed    → embed()
    """

    def __init__(
        self,
        base_url:        str   = _BASE_URL,
        default_model:   str   = _MODEL_LLM,
        timeout_s:       float = _TIMEOUT,
        max_retries:     int   = _MAX_RETRIES,
        retry_backoff_s: float = _BACKOFF,
    ) -> None:
        self._base_url      = base_url.rstrip("/")
        self.default_model  = default_model
        self._timeout_s     = timeout_s
        self._max_retries   = max_retries
        self._retry_backoff = retry_backoff_s
        logger.debug("OllamaWrapper initialisé — url=%s, modèle=%s", self._base_url, self.default_model)

    @property
    def base_url(self) -> str:
        return self._base_url

    # ------------------------------------------------------------------
    # Santé serveur
    # ------------------------------------------------------------------

    def is_server_running(self) -> bool:
        """Ping léger via GET /api/version."""
        try:
            payload = self._request("GET", "/api/version")
            return isinstance(payload.get("version"), str)
        except OllamaConnectionError:
            return False
        except OllamaResponseError:
            return True

    # ------------------------------------------------------------------
    # Génération texte
    # ------------------------------------------------------------------

    def generate_text(
        self,
        prompt:  str,
        *,
        model:   Optional[str]               = None,
        system:  Optional[str]               = None,
        options: Optional[Mapping[str, Any]] = None,
    ) -> OllamaGenerateResult:
        """POST /api/generate — réponse complète (stream=false)."""
        model = model or self.default_model
        body: Dict[str, Any] = {"model": model, "prompt": prompt, "stream": False}
        if system  is not None: body["system"]  = system
        if options is not None: body["options"] = dict(options)
        return self._parse_generate_result(
            self._request("POST", "/api/generate", body=body, _log_prompt=prompt)
        )

    def generate_stream(
        self,
        prompt:  str,
        *,
        model:   Optional[str]               = None,
        system:  Optional[str]               = None,
        options: Optional[Mapping[str, Any]] = None,
    ) -> Iterator[OllamaStreamChunk]:
        """POST /api/generate — tokens en streaming (stream=true)."""
        model = model or self.default_model
        body: Dict[str, Any] = {"model": model, "prompt": prompt, "stream": True}
        if system  is not None: body["system"]  = system
        if options is not None: body["options"] = dict(options)
        for chunk in self._stream_request("/api/generate", body, _log_prompt=prompt):
            yield OllamaStreamChunk(
                token=chunk.get("response", ""),
                done= bool(chunk.get("done", False)),
                model=chunk.get("model"),
            )
            if chunk.get("done"):
                break

    def generate_with_image(
        self,
        prompt:  str,
        *,
        image:   Union[str, Path, bytes],
        model:   Optional[str]               = None,
        system:  Optional[str]               = None,
        options: Optional[Mapping[str, Any]] = None,
    ) -> OllamaGenerateResult:
        """POST /api/generate — multimodal avec image encodée en base64."""
        model = model or _MODEL_VLM
        body: Dict[str, Any] = {
            "model":  model,
            "prompt": prompt,
            "images": [self._encode_image(image)],
            "stream": False,
        }
        if system  is not None: body["system"]  = system
        if options is not None: body["options"] = dict(options)
        return self._parse_generate_result(
            self._request("POST", "/api/generate", body=body, _log_prompt=prompt)
        )

    # ------------------------------------------------------------------
    # Chat multi-tours
    # ------------------------------------------------------------------

    def chat(
        self,
        messages: Sequence[OllamaChatMessage],
        *,
        model:   Optional[str]               = None,
        options: Optional[Mapping[str, Any]] = None,
    ) -> OllamaChatResult:
        """POST /api/chat — conversation multi-tours (stream=false)."""
        model = model or self.default_model
        body: Dict[str, Any] = {
            "model":    model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream":   False,
        }
        if options is not None:
            body["options"] = dict(options)

        last_user = next((m.content for m in reversed(messages) if m.role == "user"), None)
        payload   = self._request("POST", "/api/chat", body=body, _log_prompt=last_user)

        raw_msg = payload.get("message")
        if not isinstance(raw_msg, dict):
            raise OllamaResponseError(f"Réponse /api/chat inattendue : {payload!r}")

        return OllamaChatResult(
            message=        OllamaChatMessage(role=raw_msg.get("role", "assistant"), content=raw_msg.get("content", "")),
            model=          payload.get("model")          if isinstance(payload.get("model"),          str)  else None,
            done=           payload.get("done")           if isinstance(payload.get("done"),           bool) else None,
            total_duration= payload.get("total_duration") if isinstance(payload.get("total_duration"), int)  else None,
            eval_count=     payload.get("eval_count")     if isinstance(payload.get("eval_count"),     int)  else None,
        )

    # ------------------------------------------------------------------
    # Embeddings
    # ------------------------------------------------------------------

    def embed(
        self,
        text:  str,
        *,
        model: Optional[str] = None,
    ) -> List[float]:
        """POST /api/embed — vecteur d'embedding."""
        model   = model or _MODEL_EMBED
        payload = self._request("POST", "/api/embed", body={"model": model, "input": text}, _log_prompt=text)

        if isinstance(payload.get("embedding"), list):
            emb = payload["embedding"]
            if all(isinstance(x, (int, float)) for x in emb):
                return [float(x) for x in emb]

        if isinstance(payload.get("embeddings"), list) and payload["embeddings"]:
            first = payload["embeddings"][0]
            if isinstance(first, list) and all(isinstance(x, (int, float)) for x in first):
                return [float(x) for x in first]

        raise OllamaResponseError(f"Réponse /api/embed inattendue : {payload!r}")

    # ------------------------------------------------------------------
    # Couche HTTP
    # ------------------------------------------------------------------

    def _request(
        self,
        method: str,
        path:   str,
        body:   Optional[Dict[str, Any]] = None,
        *,
        _log_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Requête HTTP avec retry/backoff et logging structuré."""
        url     = self._build_url(path)
        data    = json.dumps(body).encode("utf-8") if body is not None else None
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        last_exc: Exception = RuntimeError("Aucune tentative.")

        for attempt in range(1, self._max_retries + 1):
            t0      = time.perf_counter()
            log_ctx = {"method": method, "path": path, "attempt": attempt}
            if _log_prompt:
                log_ctx["prompt_preview"] = _log_prompt[:120]

            try:
                req = urllib.request.Request(url=url, data=data, headers=headers, method=method.upper())
                with urllib.request.urlopen(req, timeout=self._timeout_s) as resp:
                    raw = resp.read()
                ms = round((time.perf_counter() - t0) * 1000, 1)
                logger.info("Ollama %s %s → OK (%.0fms)", method, path, ms,
                            extra={**log_ctx, "latency_ms": ms, "status": "ok"})
                return self._parse_json(raw, url)

            except urllib.error.HTTPError as e:
                body_err = e.read().decode("utf-8", errors="replace")
                ms = round((time.perf_counter() - t0) * 1000, 1)
                logger.error("Ollama %s %s → HTTP %d (%.0fms)", method, path, e.code, ms,
                             extra={**log_ctx, "latency_ms": ms, "status": "http_error", "http_status": e.code})
                raise OllamaHTTPError(e.code, body_err) from e

            except (urllib.error.URLError, OSError, TimeoutError) as e:
                ms = round((time.perf_counter() - t0) * 1000, 1)
                last_exc = OllamaConnectionError(f"[{attempt}/{self._max_retries}] {url} : {e}")
                logger.warning("Ollama %s %s → échec (%.0fms) tentative %d/%d : %s",
                               method, path, ms, attempt, self._max_retries, e,
                               extra={**log_ctx, "latency_ms": ms, "status": "conn_error"})

            if attempt < self._max_retries:
                time.sleep(self._retry_backoff * (2 ** (attempt - 1)))

        raise last_exc

    def _stream_request(
        self,
        path: str,
        body: Dict[str, Any],
        *,
        _log_prompt: Optional[str] = None,
    ) -> Iterator[Dict[str, Any]]:
        """Requête streaming NDJSON — yield un dict par ligne."""
        url  = self._build_url(path)
        data = json.dumps(body).encode("utf-8")
        req  = urllib.request.Request(
            url=url, data=data,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            method="POST",
        )
        if _log_prompt:
            logger.debug("Ollama STREAM %s — prompt: %r", path, _log_prompt[:80])
        t0 = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=self._timeout_s) as resp:
                for raw_line in resp:
                    line = raw_line.decode("utf-8", errors="replace").strip()
                    if not line:
                        continue
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        logger.warning("Ligne NDJSON invalide ignorée : %r", line)
        except urllib.error.URLError as e:
            raise OllamaConnectionError(f"Erreur stream vers {url} : {e}") from e
        ms = round((time.perf_counter() - t0) * 1000, 1)
        logger.info("Ollama STREAM %s → terminé (%.0fms)", path, ms)

    # ------------------------------------------------------------------
    # Helpers statiques
    # ------------------------------------------------------------------

    def _build_url(self, path: str) -> str:
        return urljoin(self._base_url + "/", path.lstrip("/"))

    @staticmethod
    def _parse_json(raw: bytes, url: str) -> Dict[str, Any]:
        text = raw.decode("utf-8", errors="replace")
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as e:
            raise OllamaResponseError(f"Réponse non-JSON depuis {url} : {text[:300]!r}") from e
        if not isinstance(payload, dict):
            raise OllamaResponseError(f"JSON non-dict depuis {url} : {type(payload).__name__}")
        return payload

    @staticmethod
    def _parse_generate_result(payload: Dict[str, Any]) -> OllamaGenerateResult:
        resp = payload.get("response")
        if not isinstance(resp, str):
            raise OllamaResponseError(f"Champ 'response' manquant : {payload!r}")
        return OllamaGenerateResult(
            response=          resp,
            model=             payload.get("model")             if isinstance(payload.get("model"),             str)  else None,
            done=              payload.get("done")              if isinstance(payload.get("done"),              bool) else None,
            total_duration=    payload.get("total_duration")    if isinstance(payload.get("total_duration"),    int)  else None,
            load_duration=     payload.get("load_duration")     if isinstance(payload.get("load_duration"),     int)  else None,
            prompt_eval_count= payload.get("prompt_eval_count") if isinstance(payload.get("prompt_eval_count"), int)  else None,
            eval_count=        payload.get("eval_count")        if isinstance(payload.get("eval_count"),        int)  else None,
        )

    @staticmethod
    def _encode_image(image: Union[str, Path, bytes]) -> str:
        if isinstance(image, (str, Path)):
            image_bytes = Path(image).read_bytes()
        elif isinstance(image, (bytes, bytearray)):
            image_bytes = bytes(image)
        else:
            raise TypeError(f"image doit être str/Path ou bytes, reçu : {type(image).__name__}")
        return base64.b64encode(image_bytes).decode("ascii")


# ---------------------------------------------------------------------------
# Démo rapide
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    client = OllamaWrapper()
    print(f"URL    : {client.base_url}")
    print(f"Modèle : {client.default_model}")

    if not client.is_server_running():
        print("❌ Serveur Ollama inaccessible.")
    else:
        print("✅ Serveur accessible.")
        result = client.generate_text("Donne une définition de l'IA en une phrase.")
        print("Réponse :", result.response)
        