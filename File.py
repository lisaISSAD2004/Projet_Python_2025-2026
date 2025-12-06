import os
import mimetypes
from abc import ABC, abstractmethod

try:
    import magic  
except ImportError:
    magic = None


class File(ABC):
    """!
    @class File
    @brief Classe abstraite représentant un fichier générique sur le système.

    @details Cette classe est la base pour la gestion de tout fichier.
    Elle permet de gérer le chemin absolu et la détection du type MIME,
    avec une extension possible pour des fichiers audio, image, ou autres formats.

    @var path
    @details Chemin absolu du fichier (str).

    @var mime_type
    @details Type MIME détecté du fichier (str). Ex: 'audio/mpeg', 'audio/flac', etc.
    """

    def __init__(self, path: str):
        """!
        @brief Constructeur. Initialise un objet File et détermine son type MIME.

        @param path [in] Chemin d'accès relatif ou absolu du fichier (str).
        """
        self.path = os.path.abspath(path)
        self.mime_type = self.get_mime_type()

    def get_path(self) -> str:
        """!
        @brief Accesseur. Retourne le chemin absolu du fichier.

        @return str Le chemin absolu du fichier.
        """
        return self.path

    def get_mime_type(self) -> str:
        """!
        @brief Détermine et retourne le type MIME du fichier.

        @details Utilise la librairie \c python-magic si disponible pour une détection précise,
        sinon elle utilise la bibliothèque standard \c mimetypes.
        
        @return str Le type MIME détecté (ex: 'audio/mpeg').
        @retval 'application/octet-stream' si le type MIME ne peut être déterminé.
        """
        if magic:
            try:
                mime = magic.Magic(mime=True)
                return mime.from_file(self.path)
            except Exception:
                # Échec de python-magic, tentative avec mimetypes
                pass

        mime_type, _ = mimetypes.guess_type(self.path)
        return mime_type or "application/octet-stream"
