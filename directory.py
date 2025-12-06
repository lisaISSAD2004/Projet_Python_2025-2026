"""!
@class Metadata
@brief Gère l'extraction, la modification et l'affichage des métadonnées des fichiers audio (MP3 et FLAC).

@details Cette classe agit comme un conteneur pour toutes les informations pertinentes d'un fichier audio.
Elle inclut la logique pour gérer les formats spécifiques MP3 (ID3, EasyID3) et FLAC (Vorbis Comments),
la durée, la pochette, et la récupération des paroles via une API externe.

@var file_path
@details Chemin d'accès complet (str) du fichier audio.

@var file_name
@details Nom du fichier (str) sans le chemin.

@var title
@var artist
@var album
@var year
@var genre
@details Tags textuels (str) extraits du fichier.

@var duration
@details Durée (str) du fichier audio au format MM:SS.

@var cover
@details Données binaires (\c io.BytesIO) de la pochette intégrée au fichier, ou \c None.

@var lyrics
@details Paroles (str) récupérées via API, ou \c None.
"""
import os
import io
import requests
from mutagen import File
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC, Picture
from mutagen.id3 import ID3, APIC
from urllib.parse import quote
from requests.exceptions import Timeout, RequestException, ConnectionError


class Metadata:
    """Classe pour gérer les métadonnées des fichiers audio MP3 et FLAC"""

    def __init__(self, file_path: str):
        """!
        @brief Constructeur. Initialise l'objet et extrait automatiquement les métadonnées.

        @details Initialise les attributs de métadonnées, puis appelle les méthodes d'extraction
        (\c extract_tags(), \c extract_duration(), et \c extract_cover()) pour peupler l'objet.

        @param file_path [in] Chemin d'accès complet (str) du fichier audio.
        """
        self.file_path = file_path
        self.file_name = os.path.basename(file_path)

        # Métadonnées textuelles
        self.title = ""
        self.artist = ""
        self.album = ""
        self.year = ""
        self.genre = ""
        self.duration = ""

        # Données binaires
        self.cover = None  # BytesIO object contenant l'image
        self.lyrics = None

        # Extraction automatique lors de l'initialisation
        self.extract_tags()
        self.extract_duration()
        self.extract_cover()

    def extract_tags(self):
        """!
        @brief Extrait les métadonnées textuelles (titre, artiste, album, etc.).

        @details Implémente une logique spécifique pour les MP3 (EasyID3 avec fallback ID3) et
        les FLAC (Vorbis Comments), incluant la gestion robuste des erreurs de lecture.
        """
        try:
            if self.file_path.lower().endswith(".mp3"):

                # --- Bloc MP3 : Lecture via EasyID3 ---
                audio = EasyID3(self.file_path)

                # Récupération du titre
                title_list = audio.get("title", [""])
                self.title = title_list[0]

                # Fallback : Si EasyID3 ne donne rien (pour gérer les bugs de relecture)
                if not self.title:
                    try:
                        from mutagen.id3 import ID3, TIT2
                        full_tags = ID3(self.file_path)
                        # Lire directement la frame TIT2
                        if 'TIT2' in full_tags:
                            self.title = str(full_tags.get('TIT2', ''))
                    except Exception:
                        pass

                # Reste des tags MP3
                self.artist = audio.get("artist", [""])[0]
                self.album = audio.get("album", [""])[0]
                self.year = audio.get("date", [""])[0]
                genre_list = audio.get("genre", [""])
                self.genre = genre_list[0] if genre_list else ""

            elif self.file_path.lower().endswith(".flac"):

                # 🚀 CORRECTION FLAC : Gestion d'erreur spécifique pour l'ouverture 🚀
                try:
                    audio = FLAC(self.file_path)

                    # Extraction des tags (Vorbis Comments)
                    self.title = audio.get("title", [""])[0]
                    self.artist = audio.get("artist", [""])[0]
                    self.album = audio.get("album", [""])[0]
                    self.year = audio.get("date", [""])[0]

                    genre_list = audio.get("genre", [""])
                    self.genre = genre_list[0] if genre_list else ""


                except Exception as e:
                    # Si l'ouverture ou la lecture FLAC échoue, cela est affiché
                    print(f"Erreur de lecture FLAC critique pour '{self.file_path}': {e}")
                    # Les attributs restent vides ("")

        except Exception as e:
            # Bloc d'exception général (inchangé)
            print(f"Erreur extraction tags pour {self.file_path}: {e}")

    # Fichier: Metadata.py (Méthode extract_duration)

    def extract_duration(self):
        """!
        @brief Extrait la durée du fichier audio.

        @details Met à jour l'attribut \c duration au format textuel MM:SS.

        @note Affiche une erreur critique si la lecture de la durée échoue.
        """
        try:
            # 🚀 CORRECTION : Isoler l'accès au fichier pour la durée
            audio = File(self.file_path)
            if audio and audio.info:
                seconds = int(audio.info.length)
                minutes = seconds // 60
                secs = seconds % 60
                self.duration = f"{minutes:02d}:{secs:02d}"
        except Exception as e:
            print(f"Erreur critique lors de l'extraction de la durée pour '{self.file_path}': {e}")
            self.duration = ""


    def extract_cover(self):
        """!
        @brief Extrait la pochette intégrée au fichier audio.

        @details Recherche le tag \c APIC pour les MP3 ou la première image dans \c audio.pictures pour les FLAC.
        La pochette est stockée dans \c self.cover sous forme de \c io.BytesIO.
        """
        try:
            if self.file_path.lower().endswith(".mp3"):
                try:
                    audio_id3 = ID3(self.file_path)
                    for tag in audio_id3.values():
                        if isinstance(tag, APIC):
                            self.cover = io.BytesIO(tag.data)
                            self.cover.seek(0)  # ← IMPORTANT
                            break
                except Exception as e:
                    print(f"Pas de tags ID3 ou erreur: {e}")
            elif self.file_path.lower().endswith(".flac"):
                audio = FLAC(self.file_path)
                if audio.pictures:
                    self.cover = io.BytesIO(audio.pictures[0].data)
                    self.cover.seek(0)  # ← IMPORTANT
        except Exception as e:
            print(f"Erreur extraction cover pour {self.file_path}: {e}")
            self.cover = None

    def save_tags(self, title=None, artist=None, album=None, year=None, genre=None):
        """!
        @brief Sauvegarde les métadonnées modifiées dans le fichier, gérant la suppression des tags vides.

        @details Met à jour les tags spécifiés. Si une valeur est vide (\c "") et que le tag existe,
        il est supprimé du fichier. Gère la création des tags ID3 si manquants sur un MP3.

        @param title [in] Nouveau titre.
        @param artist [in] Nouvel artiste.
        @param album [in] Nouvel album.
        @param year [in] Nouvelle année.
        @param genre [in] Nouveau genre.
        @return bool \c True si la sauvegarde a réussi, \c False sinon.
        """
        try:
            is_mp3 = self.file_path.lower().endswith(".mp3")
            is_flac = self.file_path.lower().endswith(".flac")

            if is_mp3:
                try:
                    audio = EasyID3(self.file_path)
                except:
                    from mutagen.id3 import ID3
                    audio_id3 = ID3()
                    audio_id3.save(self.file_path)
                    audio = EasyID3(self.file_path)

            elif is_flac:
                audio = FLAC(self.file_path)
            else:
                print("Format de fichier non supporté pour la sauvegarde des tags.")
                return False

            tags_to_update = {
                "title": title,
                "artist": artist,
                "album": album,
                "date": year,
                "genre": genre
            }

            for key, value in tags_to_update.items():

                attr_name = 'year' if key == 'date' else key

                if value is not None:

                    if value == "":
                        if key in audio:
                            del audio[key]
                        setattr(self, attr_name, "")

                    elif value != "":
                        if is_flac:
                            audio[key] = [value]
                        else:
                            audio[key] = [value]

                        setattr(self, attr_name, value)

            if is_mp3:
                audio.save()
            else:
                audio.save()

            print(f"✓ Métadonnées sauvegardées pour {self.file_name}")
            return True

        except Exception as e:
            print(f" Erreur sauvegarde tags pour {self.file_path}: {e}")
            import traceback
            traceback.print_exc()
            return False

    def save_cover(self, cover_data: bytes):
        """!
        @brief Sauvegarde les données binaires de couverture dans le fichier audio.

        @details Met à jour l'attribut \c self.cover et intègre la couverture dans le tag \c APIC (MP3)
        ou dans \c audio.pictures (FLAC). Assure la suppression de la pochette précédente.

        @param cover_data [in] Les données binaires (bytes) de l'image à intégrer.
        @return bool \c True si la sauvegarde a réussi, \c False sinon.
        """
        self.cover = io.BytesIO(cover_data)
        self.cover.seek(0)

        try:
            # --- LOGIQUE MP3 ---
            if self.file_path.lower().endswith(".mp3"):
                audio = ID3(self.file_path)
                audio.delall('APIC')
                audio.add(
                    APIC(
                        encoding=3, type=3,
                        mime='image/jpeg', desc='Cover',
                        data=cover_data
                    )
                )
                audio.save(v2_version=3)

            # --- LOGIQUE FLAC ---
            elif self.file_path.lower().endswith(".flac"):
                audio = FLAC(self.file_path)
                audio.pictures = []
                image = Picture()
                image.data = cover_data
                image.type = 3
                image.mime = 'image/jpeg'
                audio.pictures.append(image)
                audio.save()

            print(f"✓ Cover sauvegardée dans le fichier {self.file_name}")
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la cover: {e}")
            return False

    def fetch_lyrics(self):
        """!
        @brief Tente de récupérer les paroles via l'API \c lyrics.ovh.

        @details Utilise \c self.artist et \c self.title pour interroger l'API.
        Les paroles sont stockées dans \c self.lyrics. La méthode gère diverses exceptions
        de \c requests (Timeout, Connexion, HTTPError).

        @return bool \c True si les paroles ont été trouvées et chargées, \c False sinon.
        """
        if not self.artist or not self.title:
            print("⚠ Artiste ou titre manquant pour récupérer les paroles")
            return False
        url = f"https://api.lyrics.ovh/v1/{quote(self.artist)}/{quote(self.title)}"

        try:
            # Note: Nous gardons le print de la recherche pour le diagnostic
            print(f"🔍 Recherche paroles : {self.artist} - {self.title} (Via lyrics.ovh)")

            resp = requests.get(url, timeout=10)
            resp.raise_for_status() # Lève une exception pour les codes 4xx/5xx

            if resp.status_code == 200:
                data = resp.json()

                if 'lyrics' in data:
                    self.lyrics = data['lyrics']
                    print("✓ Paroles récupérées avec succès")
                    return True
                else:
                    self.lyrics = None # ⬅️ LAISSE self.lyrics à None
                    return False

        except requests.exceptions.Timeout:
            self.lyrics = None
            return False

        except requests.exceptions.ConnectionError as e:
            self.lyrics = None
            return False

        except requests.exceptions.HTTPError as e:
            self.lyrics = None
            return False

        except requests.exceptions.RequestException as e:
            self.lyrics = None
            return False

        except Exception as e:
            self.lyrics = None
            return False

    # --- Metadata.py (Modifié) ---
    def display_tags(self):
        """!
        @brief Affiche toutes les métadonnées extraites dans la console.

        @details Utilisé principalement pour l'inspection rapide. Affiche "✗ Non trouvé" pour les champs vides.
        Inclut des détails sur la taille de la pochette et l'état des paroles.
        """

        # CHANGEMENT 1 : Utilisation de "Non trouvé" comme valeur par défaut
        placeholder = '✗ Non trouvé'

        print("\n" + "="*50)
        print(f"📁 Fichier : {self.file_name}")
        print("="*50)

        # Champs textuels (Titre, Artiste, Album, etc.)
        print(f"🎵 Titre   : {self.title or placeholder}")
        print(f"👤 Artiste : {self.artist or placeholder}")
        print(f"💿 Album   : {self.album or placeholder}")
        print(f"📅 Année   : {self.year or placeholder}")
        print(f"🎸 Genre   : {self.genre or placeholder}")
        print(f"⏱️  Durée   : {self.duration or placeholder}")

        # CHANGEMENT 2 : Ajuster l'affichage de la Cover
        print(f"🖼️  Cover   : {'✓ Trouvée' if self.cover else '✗ Non trouvé'}")
        if self.cover:
            print(f"📏Taille : {len(self.cover.getvalue())} bytes")
        print(f"📝 Paroles : {'✓ Chargées' if self.lyrics else '✗ Non trouvées'}")
        print("="*50 + "\n")


# Test de la classe
if __name__ == "__main__":
    # Exemple d'utilisation
    test_file = "test1.mp3"

    if os.path.exists(test_file):
        meta = Metadata(test_file)
        meta.display_tags()

        # Test récupération paroles
        meta.fetch_lyrics()
        
        # Test modification métadonnées
        # meta.save_tags(title="Nouveau Titre", artist="Nouvel Artiste")
    else:
        print(f"Fichier {test_file} introuvable")
