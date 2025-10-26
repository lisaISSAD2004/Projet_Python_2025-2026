from typing import List
import os
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC

# --- Classe Metadata ---
class Metadata:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.file_name = os.path.basename(file_path)
        self.title = ""
        self.artist = ""
        self.album = ""
        self.year = ""
        self.cover = None  # placeholder pour l'image de couverture
        self.duration = 0

        # Extraction des tags dès l'initialisation
        self.extract_tags()

    def extract_tags(self):
        try:
            if self.file_path.lower().endswith(".mp3"):
                audio = EasyID3(self.file_path)
                self.title = audio.get("title", [""])[0]
                self.artist = audio.get("artist", [""])[0]
                self.album = audio.get("album", [""])[0]
                self.year = audio.get("date", [""])[0]
            elif self.file_path.lower().endswith(".flac"):
                audio = FLAC(self.file_path)
                self.title = audio.get("title", [""])[0]
                self.artist = audio.get("artist", [""])[0]
                self.album = audio.get("album", [""])[0]
                self.year = audio.get("date", [""])[0]
        except Exception as e:
            print(f"Erreur lors de l'extraction des tags pour {self.file_path}: {e}")

    def display_tags(self):
        print(f"Fichier : {self.file_name}")
        print(f"Titre  : {self.title}")
        print(f"Artiste: {self.artist}")
        print(f"Album  : {self.album}")
        print(f"Année  : {self.year}")




# --- Test sur test1.mp3 ---
metadata = Metadata("test1.mp3")
metadata.display_tags()