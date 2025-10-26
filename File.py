import os
import mimetypes
from abc import ABC, abstractmethod

try:
    import magic  # pour détection MIME plus précise
except ImportError:
    magic = None


class File(ABC):
    """
    Classe abstraite représentant un fichier générique.

    Attributs :
        path (str) : chemin absolu du fichier.
        mime_type (str) : type MIME détecté (ex: 'audio/mpeg', 'audio/flac', ...).
    """

    def __init__(self, path: str):
        self.path = os.path.abspath(path)
        self.mime_type = self.get_mime_type()

    def get_path(self) -> str:
        """Retourne le chemin absolu du fichier."""
        return self.path

    def get_mime_type(self) -> str:
        """
        Retourne le type MIME du fichier.
        Utilise python-magic si disponible, sinon mimetypes.
        """
        if magic:
            try:
                mime = magic.Magic(mime=True)
                return mime.from_file(self.path)
            except Exception:
                pass

        mime_type, _ = mimetypes.guess_type(self.path)
        return mime_type or "application/octet-stream"

        return mime_type or "application/octet-stream"
