"""
@class AudioFile
@brief Classe abstraite représentant un fichier audio générique.

@details Cette classe sert de base pour les classes spécifiques comme Mp3File et FlacFile.
Elle implémente la logique commune pour :
* L'extraction et la sauvegarde des métadonnées.
* La récupération de la durée.
* La gestion de la lecture audio via pygame.

@var metadata
@details Objet contenant les métadonnées du fichier audio.

@var duration
@details Durée du fichier audio en secondes (float).


@version 1.0
@date Décembre 2025
@note Assurez-vous que la bibliothèque pygame est installée et configurée.

"""


from abc import ABC, abstractmethod
from File import File
from Metadata import Metadata
import time
try:
    import pygame
except ImportError:
    pygame = None
import select 
import sys

class AudioFile(File, ABC):
    """
    Classe abstraite représentant un fichier audio générique.
    Sert de base aux classes Mp3File et FlacFile.
    """
    def __init__(self, path: str):
        super().__init__(path)
        self.metadata: Metadata = Metadata(self.path)
        self.duration: float = 0.0

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

    def play(self,wait_for_end: bool = True):
        if not pygame:
            print("Erreur : pygame n'est pas installé. Lecture impossible.")
            return
        
        
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init() 
                
            pygame.mixer.music.load(self.path)
            pygame.mixer.music.play()
            
            if wait_for_end:
                print(f"▶ Lecture de : {self.path} (tapez 'q' pour arrêter)")
                while pygame.mixer.music.get_busy():
                    if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                        line = sys.stdin.readline().strip()
                        if line.lower() == 'q':
                            self.stop(silent=True)
                            print("⏹ Lecture arrêtée par l'utilisateur (q).")
                            break
                    time.sleep(0.1) 
            else:
                 print(f"▶ Démarrage en playlist de : {self.path}")
            
        except Exception as e:
            print(f"Erreur lors de la lecture : {e}")
