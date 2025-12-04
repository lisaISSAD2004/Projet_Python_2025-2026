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
        """Extrait les métadonnées textuelles (titre, artiste, album, etc.)"""
        try:
            if self.file_path.lower().endswith(".mp3"):
                audio = EasyID3(self.file_path)
                self.title = audio.get("title", [""])[0]
                self.artist = audio.get("artist", [""])[0]
                self.album = audio.get("album", [""])[0]
                self.year = audio.get("date", [""])[0]
                # CORRECTION 1: Gestion plus robuste du genre
                genre_list = audio.get("genre", [""])
                self.genre = genre_list[0] if genre_list else ""
                
            elif self.file_path.lower().endswith(".flac"):
                audio = FLAC(self.file_path)
                self.title = audio.get("title", [""])[0]
                self.artist = audio.get("artist", [""])[0]
                self.album = audio.get("album", [""])[0]
                self.year = audio.get("date", [""])[0]
                # CORRECTION 1: Gestion plus robuste du genre
                genre_list = audio.get("genre", [""])
                self.genre = genre_list[0] if genre_list else ""
                
        except Exception as e:
            print(f"Erreur extraction tags pour {self.file_path}: {e}")
    
    def extract_duration(self):
        """Extrait la durée du fichier audio au format MM:SS"""
        try:
            audio = File(self.file_path)
            if audio and audio.info:
                seconds = int(audio.info.length)
                minutes = seconds // 60
                secs = seconds % 60
                self.duration = f"{minutes:02d}:{secs:02d}"
        except Exception as e:
            print(f"Erreur extraction durée pour {self.file_path}: {e}")
            self.duration = ""
    def display_lyrics(self):
        """Affiche les paroles si elles ont été chargées"""
        if self.lyrics:
            print("\n" + "📝 PAROLES" + "\n" + "="*50)
            print(self.lyrics)
            print("="*50 + "\n")
        elif self.lyrics is not None and not self.lyrics: # Si fetch_lyrics a réussi mais n'a rien trouvé
            print("\n✗ Paroles introuvables pour ce titre.")
        else: # Si lyrics est None (pas encore chargé ou échec réseau)
            print("\n✗ Les paroles n'ont pas été chargées ")
    def extract_cover(self):
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
        """Sauvegarde les métadonnées modifiées dans le fichier"""
        try:
            if self.file_path.lower().endswith(".mp3"):
                # CORRECTION 3: Créer le fichier ID3 s'il n'existe pas
                try:
                    audio = EasyID3(self.file_path)
                except:
                    # Si pas de tags ID3, en créer
                    from mutagen.id3 import ID3
                    audio_id3 = ID3()
                    audio_id3.save(self.file_path)
                    audio = EasyID3(self.file_path)
                
            elif self.file_path.lower().endswith(".flac"):
                audio = FLAC(self.file_path)
            else:
                print("Format de fichier non supporté")
                return False
            
            # Mise à jour des tags
            if title is not None:
                audio["title"] = title
                self.title = title
            if artist is not None:
                audio["artist"] = artist
                self.artist = artist
            if album is not None:
                audio["album"] = album
                self.album = album
            if year is not None:
                audio["date"] = year
                self.year = year
            if genre is not None:
                audio["genre"] = genre
                self.genre = genre
            
            audio.save()
            print(f"✓ Métadonnées sauvegardées pour {self.file_name}")
            return True
            
        except Exception as e:
            print(f"Erreur sauvegarde tags pour {self.file_path}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
   
            
    
    

    def fetch_lyrics(self):
        if not self.artist or not self.title:
            print("⚠ Artiste ou titre manquant pour récupérer les paroles")
            return False
        url = f"https://api.lyrics.ovh/v1/{quote(self.artist)}/{quote(self.title)}"
        
        try:
            print(f"🔍 Recherche paroles : {self.artist} - {self.title} (Via lyrics.ovh)")
            
            # Utilisation de Timeout, ConnectionError et RequestException pour un meilleur diagnostic
            resp = requests.get(url, timeout=10)
            resp.raise_for_status() # Lève une exception pour les codes 4xx/5xx

            if resp.status_code == 200:
                data = resp.json()
                # L'API retourne un dictionnaire vide si les paroles ne sont pas trouvées (en plus du 404)
                if 'lyrics' in data:
                    self.lyrics = data['lyrics']
                    print("✓ Paroles récupérées avec succès")
                    return True
                else:
                    self.lyrics = None # Assurez-vous que c'est None en cas d'échec
                    print("✗ Paroles introuvables dans la réponse de l'API.")
                    return False
        except Timeout:
            print("✗ Erreur récupération lyrics : Le temps d'attente (timeout) a été dépassé.")
            self.lyrics = None
            return False
        
        except ConnectionError as e:
            # Capture spécifiquement l'erreur de résolution de nom (DNS) ou de connexion
            print(f"✗ Erreur récupération lyrics : Impossible de se connecter à l'hôte (DNS ou réseau). Détails: {e}")
            self.lyrics = None
            return False
            
        except requests.HTTPError as e:
            # Gère les statuts d'erreur HTTP (404 Not Found, 500 Server Error, etc.)
            print(f"✗ Paroles introuvables (Erreur HTTP {e.response.status_code}).")
            self.lyrics = None
            return False
            
        except RequestException as e:
            # Attrape toute autre erreur de la librairie requests
            print(f"✗ Erreur récupération lyrics : Problème lors de la requête HTTP. Détails: {e}")
            self.lyrics = None
            return False
        
        except Exception as e:
            # Pour toute autre exception (ex: erreur de décodage JSON)
            print(f"✗ Erreur inattendue lors de la récupération des paroles. Détails: {e}")
            self.lyrics = None
            return False
    
    # --- Metadata.py (Modifié) ---
    def display_tags(self):
        """Affiche toutes les métadonnées dans la console (debug)"""
        
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
            print(f"   Taille : {len(self.cover.getvalue())} bytes")
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
