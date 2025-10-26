# mp3file.py

import io
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, APIC
from PIL import Image
from .AudioFile import AudioFile
from .Metadata import Metadata


class Mp3File(AudioFile):
    """
    Classe représentant un fichier MP3.
    Permet d'extraire, modifier et sauvegarder les métadonnées.
    """

    def __init__(self, path: str):
        super().__init__(path)
        self.id3 = None

    def extract_metadata(self) -> Metadata:
        """Extrait les métadonnées d’un fichier MP3 via mutagen."""
        audio = MP3(self.path)
        meta = Metadata()

        # Durée du morceau
        meta.duration = float(audio.info.length) if audio.info else None
        self.duration = meta.duration

        # Extraction des tags ID3
        tags = audio.tags
        if tags:
            meta.title = str(tags.get('TIT2', ''))
            meta.artist = str(tags.get('TPE1', ''))
            meta.album = str(tags.get('TALB', ''))
            try:
                meta.year = int(str(tags.get('TDRC', ''))[:4])
            except Exception:
                meta.year = None

            # Extraction de la cover (APIC)
            apic_tags = [v for k, v in tags.items() if k.startswith("APIC")]
            if apic_tags:
                image_data = apic_tags[0].data
                try:
                    meta.cover = Image.open(io.BytesIO(image_data))
                except Exception:
                    meta.cover = None

        self.metadata = meta
        return meta

    def save_tags(self, new_tags: dict):
        """
        Met à jour les métadonnées (titre, artiste, album, année)
        et les sauvegarde dans le fichier MP3.
        """
        audio = MP3(self.path, ID3=ID3)

        if audio.tags is None:
            audio.add_tags()

        if 'title' in new_tags:
            audio.tags.add(TIT2(encoding=3, text=new_tags['title']))
        if 'artist' in new_tags:
            audio.tags.add(TPE1(encoding=3, text=new_tags['artist']))
        if 'album' in new_tags:
            audio.tags.add(TALB(encoding=3, text=new_tags['album']))
        if 'year' in new_tags:
            audio.tags.add(TDRC(encoding=3, text=str(new_tags['year'])))

        audio.save()
        print(f"✅ Tags mis à jour pour : {self.path}")
