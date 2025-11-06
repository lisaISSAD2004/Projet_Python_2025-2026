from abc import ABC, abstractmethod
from File import File
from Metadata import Metadata
import time
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

    
    def play(self):
        print(f"▶ Lecture de : {self.path}")
        pygame.mixer.init()
        pygame.mixer.music.load(self.path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():  # attend que la lecture se termine
            time.sleep(0.1)
    def stop(self) -> None:
        """Arrête la lecture audio."""
        if pygame:
            pygame.mixer.music.stop()
            print("Lecture arrêtée.")
