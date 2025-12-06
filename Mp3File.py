# Mp3File.py
import io
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, APIC,TCON
from PIL import Image
from AudioFile import AudioFile
from Metadata import Metadata


class Mp3File(AudioFile):
    """Classe représentant un fichier MP3 avec gestion des métadonnées."""

    def __init__(self, path: str):
        super().__init__(path)
        self.id3 = None

    def extract_metadata(self) -> Metadata:
        """Extrait les métadonnées en utilisant la classe Metadata."""
        # La classe Metadata gère l'extraction complète (tags, durée, cover)
        self.metadata = Metadata(self.path) 
        self.duration = self.metadata.duration # Mise à jour de l'attribut local
        return self.metadata
    """
    def save_tags(self, title=None, artist=None, album=None, year=None):
        Met à jour et sauvegarde les métadonnées d’un MP3.
        audio = MP3(self.path, ID3=ID3)

        if audio.tags is None:
            audio.add_tags()

        if title:
            audio.tags.add(TIT2(encoding=3, text=title))
        if artist:
            audio.tags.add(TPE1(encoding=3, text=artist))
        if album:
            audio.tags.add(TALB(encoding=3, text=album))
        if year:
            audio.tags.add(TDRC(encoding=3, text=str(year)))

        audio.save()


    # Fichier : Mp3File.py
"""
    def save_tags(self, title=None, artist=None, album=None, year=None, genre=None): # <-- AJOUTER genre=None
        """Met à jour et sauvegarde les métadonnées d’un MP3, y compris le genre."""
        audio = MP3(self.path, ID3=ID3)

        if audio.tags is None:
            audio.add_tags()

        if title:
            audio.tags.add(TIT2(encoding=3, text=title))
        if artist:
            audio.tags.add(TPE1(encoding=3, text=artist))
        if album:
            audio.tags.add(TALB(encoding=3, text=album))
        if year:
            audio.tags.add(TDRC(encoding=3, text=str(year)))
            
        # MODIFICATION 2: Gérer la sauvegarde du genre (TCON)
        if genre:
            audio.tags.add(TCON(encoding=3, text=genre)) # <-- AJOUTER cette ligne

        audio.save()



    
