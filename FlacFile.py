r"""!
@class FlacFile
@brief Représente un fichier audio au format FLAC et gère ses métadonnées Vorbis Comment.

@details Cette classe étend la fonctionnalité de la classe de base AudioFile pour la gestion spécifique
des fichiers FLAC. Elle permet d'extraire, de modifier (titre, artiste, album, année, genre),
et de sauvegarder les Vorbis Comments, ainsi que de gérer la durée et les couvertures.

@var path
@details Chemin absolu du fichier audio (hérité de AudioFile).

@var metadata
@details Objet de type Metadata ou None, représentant les métadonnées extraites du fichier.

@var duration
@details Durée (float) du fichier audio en secondes.

@var vorbis
@details Référence interne (`FLAC | None`) utilisée pour manipuler la structure des Vorbis Comments via la librairie \c mutagen.
"""
import io
from mutagen.flac import FLAC, Picture
import mutagen
from PIL import Image
from AudioFile import AudioFile
from Metadata import Metadata

class FlacFile(AudioFile):
    """
    Classe représentant un fichier FLAC.
    Permet d'extraire et modifier les métadonnées Vorbis Comment.
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

    def save_tags(self, title=None, artist=None, album=None, year=None, genre=None):
        r"""!
        @brief Met à jour et sauvegarde les métadonnées Vorbis Comment dans le fichier FLAC.

        @details Met à jour les tags TITLE, ARTIST, ALBUM, DATE (année), et GENRE.

        Un tag sera supprimé du fichier si une valeur vide ou \c None est fournie et qu'il existait.

        @param title [in] Nouveau titre (str).
        @param artist [in] Nouvel artiste (str).
        @param album [in] Nouvel album (str).
        @param year [in] Nouvelle année (str, mappé sur le tag DATE).
        @param genre [in] Nouveau genre (str).
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

    def save_cover(self, image_data: bytes) -> bool:
        """
        @brief Sauvegarde la pochette d'album dans le fichier FLAC.

        @details Supprime toutes les pochettes existantes et attache la nouvelle image JPEG.

        @param image_data [in] Les données binaires (bytes) de l'image.
        @return bool True si la sauvegarde est réussie, False sinon.
        """
        try:
            audio = FLAC(self.path)  # ✅ Utiliser self.path
            
            # 1. Créer l'objet Picture
            picture = Picture()
            picture.data = image_data
            picture.type = 3  # 3 = Front Cover
            picture.mime = 'image/jpeg'
            picture.desc = 'Cover'
            
            # 2. Essayer d'extraire les dimensions de l'image
            try:
                img = Image.open(io.BytesIO(image_data))
                picture.width = img.width
                picture.height = img.height
                picture.depth = 24  # 24 bits pour JPEG
            except Exception as e:
                print(f"Avertissement: Impossible d'extraire les dimensions: {e}")

            # 3. Supprimer les pochettes existantes
            audio.clear_pictures()
            
            # 4. Ajouter la nouvelle pochette
            audio.add_picture(picture)
            
            # 5. Sauvegarder
            audio.save()
            return True
            
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la cover FLAC pour {self.path}: {e}")
            return False
