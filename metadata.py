import os
import requests
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC, Picture
from mutagen.id3 import ID3, APIC
import time  
from urllib.parse import quote  


class Metadata:
    def __init__(self, file_path: str): 
        self.file_path = file_path
        self.file_name = os.path.basename(file_path)
        self.title = ""
        self.artist = ""
        self.album = ""
        self.year = ""
        self.cover = None
        self.lyrics = None

        # Extraction et récupération
        self.extract_tags()
    


    # --- Extraction des tags ---
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

    def fetch_lyrics(self):
        if not self.artist or not self.title:
            print("Artiste ou titre manquant")
            return
        url = f"https://api.lyrics.ovh/v1/{quote(self.artist)}/{quote(self.title)}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                self.lyrics = response.json().get("lyrics", None)
            else:
                print("Paroles non trouvées")
        except:
            print("Erreur lors de la récupération des paroles")
    # --- Affichage des tags ---
    def display_tags(self):
        print(f"Fichier : {self.file_name}")
        print(f"Titre   : {self.title}")
        print(f"Artiste : {self.artist}")
        print(f"Album   : {self.album}")
        print(f"Année   : {self.year}")
    
    # --- Affichage des paroles ---
    def display_lyrics(self):
        """
        Affiche les paroles si elles sont disponibles
        """
        if self.lyrics:
            print("\n" + "="*50)
            print(f"PAROLES - {self.title} par {self.artist}")
            print("="*50)
            print(self.lyrics)
            print("="*50)
        else:
            print("Aucune parole disponible")

# --- Exemple d'utilisation ---
if __name__ == "__main__":   
    path = "test1.mp3"  
    meta = Metadata(path)
    meta.display_tags()
    
    # Récupération et affichage des paroles
    print("\nRécupération des paroles...")
    meta.fetch_lyrics()
    meta.display_lyrics() 

    
