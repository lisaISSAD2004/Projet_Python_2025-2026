"""!
@class Mp3File
@brief Représente un fichier audio au format MP3 et gère ses tags ID3.

@details Cette classe étend la classe de base \c AudioFile pour gérer les fichiers MP3.
Elle permet d'extraire les métadonnées via \c Metadata, de lire et de modifier les tags ID3
usuels (titre, artiste, album, année, genre), et d'assurer la mise à jour de la durée.

@var path
@details Chemin du fichier audio (str), hérité de AudioFile.

@var metadata
@details Objet \c Metadata ou \c None, contenant les métadonnées extraites.

@var duration
@details Durée (float ou None) du fichier en secondes, mise à jour après extraction.

@var id3
@details Gestionnaire interne des tags ID3 (ID3 | None) pour la modification et l'accès aux données via \c mutagen.
"""
import io
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, APIC,TCON
from PIL import Image
from AudioFile import AudioFile
from Metadata import Metadata


class Mp3File(AudioFile):
    """Classe représentant un fichier MP3 avec gestion des métadonnées."""

    def __init__(self, path: str):
        """!
        @brief Constructeur. Initialise un objet Mp3File.

        @details Initialise l'objet et prépare le gestionnaire interne des tags ID3 (\c self.id3).

        @param path [in] Chemin d'accès (str) du fichier MP3.
        """
        super().__init__(path)
        self.id3 = None

    def extract_metadata(self) -> Metadata:
        """!
        @brief Extrait toutes les métadonnées du fichier MP3.

        @details Utilise la classe \c Metadata pour l'extraction complète des tags, de la durée, et de la pochette.
        Met à jour l'attribut local \c duration.

        @return Metadata L'objet \c Metadata contenant toutes les informations récupérées.
        """
        # La classe Metadata gère l'extraction complète (tags, durée, cover)
        self.metadata = Metadata(self.path) 
        self.duration = self.metadata.duration # Mise à jour de l'attribut local
        return self.metadata


    # Fichier : Mp3File.py

    def save_tags(self, title=None, artist=None, album=None, year=None, genre=None): # <-- AJOUTER genre=None
        """!
        @brief Met à jour et sauvegarde les tags ID3 du fichier MP3.

        @details Met à jour les tags ID3 standard :
        * Titre (\c TIT2)
        * Artiste (\c TPE1)
        * Album (\c TALB)
        * Année (\c TDRC)
        * Genre (\c TCON)
        
        Si aucun tag ID3 n'existe, ils sont ajoutés. Les modifications sont sauvegardées directement dans le fichier.

        @param title [in] Nouveau titre.
        @param artist [in] Nouvel artiste.
        @param album [in] Nouvel album.
        @param year [in] Nouvelle année.
        @param genre [in] Nouveau genre.
        """
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
