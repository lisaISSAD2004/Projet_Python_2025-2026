import os
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC, Picture
from mutagen.id3 import ID3, APIC
import musicbrainzngs  

# --- Configuration de MusicBrainz ---
musicbrainzngs.set_useragent(
    "L3PythonProject", "1.0", "https://musicbrainz.org"
)

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
        self.fetch_cover_and_lyrics()

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

    # --- Affichage des tags ---
    def display_tags(self):
        print(f"Fichier : {self.file_name}")
        print(f"Titre  : {self.title}")
        print(f"Artiste: {self.artist}")
        print(f"Album  : {self.album}")
        print(f"Année  : {self.year}")
        print(f"Pochette: {'Oui' if self.cover else 'Non'}")

    # --- Ajout de la cover dans le MP3 ---
    def save_cover_mp3(self, cover_data):
        audio = ID3(self.file_path)
        audio.add(
            APIC(
                encoding=3,          # UTF-8
                mime='image/jpeg',   # ou 'image/png'
                type=3,              # front cover
                desc='Cover',
                data=cover_data
            )
        )
        audio.save()
        print("Cover ajoutée au MP3 !")

    # --- Ajout de la cover dans le FLAC ---
    def save_cover_flac(self, cover_data):
        audio = FLAC(self.file_path)
        pic = Picture()
        pic.data = cover_data
        pic.type = 3  # front cover
        pic.mime = "image/jpeg"  # ou 'image/png'
        audio.add_picture(pic)
        audio.save()
        print("Cover ajoutée au FLAC !")

    # --- Récupération cover + paroles ---
    def fetch_cover_and_lyrics(self):
        if not self.artist or not self.title:
            print("Impossible de chercher les métadonnées (titre/artiste manquant).")
            return

        try:
            result = musicbrainzngs.search_recordings(
                artist=self.artist,
                recording=self.title,
                limit=1
            )

            if result["recording-list"]:
                recording = result["recording-list"][0]

                # Cover : via release
                if "release-list" in recording and recording["release-list"]:
                    release_id = recording["release-list"][0]["id"]
                    try:
                        cover_data = musicbrainzngs.get_image_front(release_id)
                        self.cover = cover_data
                        print("Pochette trouvée sur MusicBrainz !")

                        # Sauvegarde dans le fichier
                        if self.cover:
                            with open("cover.jpg", "wb") as f:
                                f.write(self.cover)
                        print("Cover sauvegardée en cover.jpg")
                       

                    except musicbrainzngs.ResponseError:
                        print("Aucune pochette trouvée.")
                else:
                    print("Pas de release associée à ce morceau.")
            else:
                print("Aucun enregistrement trouvé sur MusicBrainz.")
        except Exception as e:
            print(f"Erreur lors de la recherche MusicBrainz : {e}")


# --- Exemple d'utilisation ---
if __name__ == "__main__":
    path = "test1.mp3"  
    meta = Metadata(path)
    meta.display_tags()
