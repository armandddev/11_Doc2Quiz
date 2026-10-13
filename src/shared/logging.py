import logging
import sys

def get_logger(name: str = "Doc2Quiz") -> logging.Logger:
    """Crée et configure un logger standard pour le projet."""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Format du log : Horodatage | Niveau | Nom du module | Message
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # Sortie dans la console (stdout)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger

# Logger par défaut réutilisable directement
logger = get_logger()
