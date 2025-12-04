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
# --- Classe AudioFile (Modifié) ---

    def play(self):
        if not pygame:
            print("Erreur : pygame n'est pas installé. Lecture impossible.")
            return

        print(f"▶ Lecture de : {self.path}")
        
        # Initialisation déplacée dans la CLI pour être sûr
        # Mais nous la laissons ici pour l'exemple
        pygame.mixer.init()
        pygame.mixer.music.load(self.path)
        pygame.mixer.music.play()
        
        # --- NOUVELLE LOGIQUE INTERACTIVE ---
        print("Appuyez sur 'q' et ENTER pour arrêter la lecture et revenir au shell.")
        
        # Nous utilisons une boucle pour maintenir le programme en vie 
        # tant que la musique joue et qu'on n'a pas tapé 'q'.
        while pygame.mixer.music.get_busy():
            try:
                # Utiliser input() pour attendre la saisie utilisateur
                # Cette approche est la plus simple en CLI pour un thread bloquant.
                user_input = input() 
                if user_input.lower() == 'q':
                    self.stop()
                    break # Sortir de la boucle while
            except EOFError:
                # Si l'entrée se termine (rare en console, mais pour la robustesse)
                break 
            
            time.sleep(0.1) # Petite pause pour ne pas surcharger le CPU
            
        print("Lecture terminée ou arrêtée.")
        # Fin du programme, revient au $
