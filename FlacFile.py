import io
from mutagen.flac import FLAC
from PIL import Image
from AudioFile import AudioFile
from Metadata import Metadata


class FlacFile(AudioFile):
    """
    Classe représentant un fichier FLAC.
    Permet d’extraire et modifier les métadonnées Vorbis Comment.
    """

    def __init__(self, path: str):
        super().__init__(path)
        self.vorbis = None

    def extract_metadata(self) -> Metadata:
        """Extrait les métadonnées d’un fichier FLAC via mutagen."""
        audio = FLAC(self.path)
        meta = Metadata(self.path)


        meta.duration = float(audio.info.length) if audio.info else None
        self.duration = meta.duration

        tags = audio.tags
        if tags:
            meta.title = tags.get('title', [None])[0]
            meta.artist = tags.get('artist', [None])[0]
            meta.album = tags.get('album', [None])[0]
            try:
                date = tags.get('date', [None])[0]
                if date:
                    meta.year = int(date.split('-')[0])
            except Exception:
                meta.year = None

        # Extraction de la cover (si présente)
        if audio.pictures:
            picture = audio.pictures[0]
            try:
                meta.cover = Image.open(io.BytesIO(picture.data))
            except Exception:
                meta.cover = None

        self.metadata = meta
        return meta

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
