import base64
import io
import os
import requests
from PIL import Image
from shared.logging import get_logger

logger = get_logger("vlm_service")


class VLMService:

  def __init__(
      self,
      base_url: str = None,
      model: str = None,
      timeout: int = 180,
  ):
    self.base_url = (
        base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ).rstrip("/")
    self.model = model or os.getenv(
        "OLLAMA_DEFAULT_VLM", "qwen3-vl:8b-instruct"
    )
    # Augmentation du timeout à 180 secondes (3 minutes) pour absorber le chargement du VLM
    self.timeout = timeout

  def _prepare_image_bytes(
      self, image_data: bytes | str, max_size: int = 1024
  ) -> bytes:
    """Charge l'image et la redimensionne si elle dépasse max_size pour accélérer l'inférence VLM."""
    if isinstance(image_data, str):
      with open(image_data, "rb") as f:
        img_bytes = f.read()
    else:
      img_bytes = image_data

    try:
      with Image.open(io.BytesIO(img_bytes)) as pil_img:
        # Convertir en RGB si nécessaire (ex: RGBA avec transparence)
        if pil_img.mode in ("RGBA", "P"):
          pil_img = pil_img.convert("RGB")

        # Redimensionnement proportionnel si l'image est trop lourde
        pil_img.thumbnail((max_size, max_size))

        out_buffer = io.BytesIO()
        pil_img.save(out_buffer, format="JPEG", quality=85)
        return out_buffer.getvalue()
    except Exception:
      # En cas de problème de conversion, renvoyer les octets bruts
      return img_bytes

  def describe_image(self, image_data: bytes | str, context: str = "") -> str:
    """Envoie une image au VLM et renvoie un résumé textuel concis."""
    try:
      # 1. Optimisation de l'image (gain significatif de temps de calcul VLM)
      optimized_bytes = self._prepare_image_bytes(image_data)
      b64_image = base64.b64encode(optimized_bytes).decode("utf-8")

      prompt = (
          "Tu es un assistant pédagogique. Décris et résume ce schéma,"
          " graphique ou illustration de manière claire, factuelle et concise"
          " pour qu'un étudiant puisse comprendre son contenu et ses concepts"
          " clés sans voir l'image."
      )
      if context:
        prompt += f"\nContexte textuel associé : {context[-300:]}"

      payload = {
          "model": self.model,
          "prompt": prompt,
          "images": [b64_image],
          "stream": False,
      }

      logger.info(
          "Envoi de l'image au VLM (%s) via %s...", self.model, self.base_url
      )
      resp = requests.post(
          f"{self.base_url}/api/generate", json=payload, timeout=self.timeout
      )
      resp.raise_for_status()

      summary = resp.json().get("response", "").strip()
      logger.info(
          "Description VLM reçue avec succès (%d caractères).", len(summary)
      )
      return summary or "[Schéma non textuel sans description]"

    except requests.exceptions.Timeout:
      logger.error(
          "Timeout dépassé (%ds) lors de l'appel au modèle VLM %s.",
          self.timeout,
          self.model,
      )
      return "[Description VLM non disponible : délai d'attente dépassé]"
    except Exception as e:
      logger.error("Erreur VLM lors de la description de l'image : %s", e)
      return "[Description non disponible pour cette illustration]"