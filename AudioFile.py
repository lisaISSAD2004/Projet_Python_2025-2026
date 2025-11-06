# audiofile.py

from abc import ABC, abstractmethod
from File import File
from Metadata import Metadata

try:
    import pygame
    import time
except ImportError:
    pygame = None


class AudioFile(File, ABC):
    """
    Classe abstraite représentant un fichier audio générique.
    Sert de base aux classes Mp3File et FlacFile.
    """

    def __init__(self, path: str):
        super().__init__(path)
        # ✅ Correction : passage du chemin au constructeur Metadata
        self.metadata: Metadata = Metadata(path)
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
        """
        Joue le fichier audio dans la console avec pygame.
        Par défaut, on lit le fichier dans le répertoire courant.
        """
        try:
            pygame.mixer.init()
            pygame.mixer.music.load(self.path)
            pygame.mixer.music.play()
            print(f"Lecture de : {self.path}")

            # Attente de la fin de la lecture
            while pygame.mixer.music.get_busy():
                time.sleep(1)

            pygame.mixer.music.stop()

        except ImportError:
            raise RuntimeError("⚠️ La bibliothèque 'pygame' est requise pour la lecture audio.")
        except Exception as e:
            print(f"❌ Erreur lors de la lecture du fichier : {e}")

    def stop(self) -> None:
        """Arrête la lecture audio."""
        if pygame:
            pygame.mixer.music.stop()
            print("Lecture arrêtée.")
