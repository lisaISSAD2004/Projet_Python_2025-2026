from abc import ABC, abstractmethod
from File import File
from metadata import Metadata
from Mp3file import Mp3File

try:
    import pygame
except ImportError:
    pygame = None


class AudioFile(File, ABC):
    """
    Classe abstraite représentant un fichier audio générique.
    Sert de base aux classes Mp3File et FlacFile.
    """

    def __init__(self, path: str):
        super().__init__(path)
        self.metadata: Metadata = Metadata(self.path)
        self.duration: float = 0.0

    # --- Méthodes abstraites ---
    @abstractmethod
    def extract_metadata(self) -> Metadata:
        """Extrait les métadonnées du fichier audio."""
        pass

    @abstractmethod
    def save_tags(self, new_tags: dict):
        """Met à jour et sauvegarde les métadonnées dans le fichier."""
        pass

    # --- Méthodes communes ---
    def get_duration(self) -> float:
        """Retourne la durée du morceau."""
        return self.duration

    def play(self) -> None:
        """
        Joue le fichier audio via pygame.
        Nécessite que pygame soit installé.
        """
        if not pygame:
            raise RuntimeError("⚠️ La bibliothèque 'pygame' est requise pour la lecture audio.")

        try:
            pygame.mixer.init()
            pygame.mixer.music.load(self.path)
            pygame.mixer.music.play()
            print(f" Lecture de : {self.path}")
        except Exception as e:
            print(f"Erreur de lecture : {e}")

    def stop(self) -> None:
        """Arrête la lecture audio."""
        if pygame:
            pygame.mixer.music.stop()
            print("Lecture arrêtée.")

audio_file = Mp3File("test1.mp3")
print(audio_file.metadata.title)
audio_file.metadata.display_tags()

