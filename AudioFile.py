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

    def stop(self, silent: bool = False) -> None:
        """Arrête la lecture audio."""
        if pygame:
            pygame.mixer.music.stop()
            if not silent:
                print("Lecture arrêtée.")

    def play(self):
        if not pygame:
            print("Erreur : pygame n'est pas installé. Lecture impossible.")
            return
        
        print(f"▶ Lecture de : {self.path}")
        
        try:
            pygame.mixer.init()
            pygame.mixer.music.load(self.path)
            pygame.mixer.music.play()
            
            # Attendre que la musique se termine OU que l'utilisateur tape 'q'
            import select
            import sys
            
            while pygame.mixer.music.get_busy():
                # Vérifier si 'q' a été tapé sans bloquer
                if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                    line = sys.stdin.readline().strip()
                    if line.lower() == 'q':
                        self.stop(silent=True)  # ← MODE SILENCIEUX
                        print("⏹ Lecture arrêtée par l'utilisateur.")
                        break
                time.sleep(0.1)
        
        except Exception as e:
            print(f"Erreur lors de la lecture : {e}")
