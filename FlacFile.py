import io
from mutagen.flac import FLAC
from PIL import Image
from AudioFile import AudioFile
from Metadata import Metadata
from mutagen.flac import FLAC, Picture # Assurez-vous d'importer Picture

class FlacFile(AudioFile):
    """
    Classe représentant un fichier FLAC.
    Permet d’extraire et modifier les métadonnées Vorbis Comment.
    """

    def __init__(self, path: str):
        super().__init__(path)
        self.vorbis = None

    def extract_metadata(self) -> Metadata:
        """Extrait les métadonnées en utilisant la classe Metadata."""
        # La classe Metadata gère l'extraction complète (tags, durée, cover)
        self.metadata = Metadata(self.path) 
        self.duration = self.metadata.duration # Mise à jour de l'attribut local
        return self.metadata

    def save_tags(self, new_tags: dict):
        """
        Met à jour les métadonnées (titre, artiste, album, année)
        et les sauvegarde dans le fichier FLAC.
        """
        audio = FLAC(self.path)

        for key, value in new_tags.items():
            audio[key] = str(value)

        audio.save()
        print(f"Tags mis à jour pour : {self.path}")

    def save_tags(self, title=None, artist=None, album=None, year=None, genre=None):
        """
        Met à jour les métadonnées (titre, artiste, album, année, genre)
        et les sauvegarde dans le fichier FLAC en utilisant les Vorbis Comments.
        """
        audio = FLAC(self.path)

        # Créer un dictionnaire temporaire pour faciliter le mapping Vorbis Comment
        tags_to_save = {
            'TITLE': title,
            'ARTIST': artist,
            'ALBUM': album,
            'DATE': year,  # La clé Vorbis Comment pour l'année est 'DATE' ou 'YEAR'
            'GENRE': genre
        }

        # Parcourir et sauvegarder uniquement les valeurs non vides
        for vorbis_key, value in tags_to_save.items():
            if value is not None and value != "":
                # Vorbis Comment stocke les valeurs dans des listes
                audio[vorbis_key] = [str(value)] 
            elif vorbis_key in audio:
                 # Supprimer le tag s'il était présent et que la nouvelle valeur est vide
                del audio[vorbis_key]

        audio.save()
        print(f"Tags mis à jour pour : {self.path}")

    # ... (Le reste de votre classe FlacFile) ...
