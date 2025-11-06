# Mp3File.py
import io
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, APIC
from PIL import Image
from AudioFile import AudioFile
from Metadata import Metadata


class Mp3File(AudioFile):
    """Classe représentant un fichier MP3 avec gestion des métadonnées."""

    def __init__(self, path: str):
        super().__init__(path)
        self.id3 = None

    def extract_metadata(self) -> Metadata:
        """Extrait les métadonnées du fichier MP3."""
        audio = MP3(self.path)
        meta = Metadata(self.path)

        meta.duration = float(audio.info.length) if audio.info else None
        self.duration = meta.duration

        tags = audio.tags
        if tags:
            meta.title = str(tags.get('TIT2', ''))
            meta.artist = str(tags.get('TPE1', ''))
            meta.album = str(tags.get('TALB', ''))
            try:
                meta.year = int(str(tags.get('TDRC', ''))[:4])
            except Exception:
                meta.year = None

            # Extraction de la jaquette (APIC)
            apic_tags = [v for k, v in tags.items() if k.startswith("APIC")]
            if apic_tags:
                try:
                    meta.cover = Image.open(io.BytesIO(apic_tags[0].data))
                except Exception:
                    meta.cover = None

        self.metadata = meta
        return meta

    def save_tags(self, title=None, artist=None, album=None, year=None):
        """Met à jour et sauvegarde les métadonnées d’un MP3."""
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
        print(f"✅ Tags mis à jour pour : {self.path}")
