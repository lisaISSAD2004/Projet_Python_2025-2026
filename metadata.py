import os
import io
import requests
from mutagen import File
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC, Picture
from mutagen.id3 import ID3, APIC
from urllib.parse import quote


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
    
    def save_cover_mp3(self, cover_data: bytes):
        """Ajoute ou remplace la jaquette d'un fichier MP3"""
        try:
            # CORRECTION 4: Créer ID3 si nécessaire
            try:
                audio = ID3(self.file_path)
            except:
                audio = ID3()
            
            # Supprimer les anciennes covers
            audio.delall("APIC")
            
            # Ajouter la nouvelle cover
            audio.add(
                APIC(
                    encoding=3,
                    mime='image/jpeg',
                    type=3,
                    desc='Cover',
                    data=cover_data
                )
            )
            audio.save(self.file_path)
            
            # Mettre à jour l'objet
            self.cover = io.BytesIO(cover_data)
            self.cover.seek(0)
            print(f"✓ Cover ajoutée au MP3 : {self.file_name}")
            return True
            
        except Exception as e:
            print(f"Erreur ajout cover MP3 : {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def save_cover_flac(self, cover_data: bytes):
        """Ajoute ou remplace la jaquette d'un fichier FLAC"""
        try:
            audio = FLAC(self.file_path)
            
            # Supprimer les anciennes covers
            audio.clear_pictures()
            
            # Créer et ajouter la nouvelle cover
            pic = Picture()
            pic.data = cover_data
            pic.type = 3  # Front cover
            pic.mime = "image/jpeg"
            # CORRECTION 5: Dimensions optionnelles
            pic.width = 0
            pic.height = 0
            pic.depth = 24
            
            audio.add_picture(pic)
            audio.save()
            
            # Mettre à jour l'objet
            self.cover = io.BytesIO(cover_data)
            self.cover.seek(0)
            print(f"✓ Cover ajoutée au FLAC : {self.file_name}")
            return True
            
        except Exception as e:
            print(f"Erreur ajout cover FLAC : {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def save_cover(self, cover_data: bytes):
        """Sauvegarde la cover selon le format du fichier"""
        if self.file_path.lower().endswith(".mp3"):
            return self.save_cover_mp3(cover_data)
        elif self.file_path.lower().endswith(".flac"):
            return self.save_cover_flac(cover_data)
        else:
            print("Format de fichier non supporté pour la cover")
            return False
    
    def fetch_lyrics(self):
        """Récupère les paroles depuis l'API lyrics.ovh"""
        if not self.artist or not self.title:
            print("⚠ Artiste ou titre manquant pour récupérer les paroles")
            return False
        
        url = f"https://api.lyrics.ovh/v1/{quote(self.artist)}/{quote(self.title)}"
        
        try:
            print(f"🔍 Recherche paroles : {self.artist} - {self.title}")
            resp = requests.get(url, timeout=10)
            
            if resp.status_code == 200:
                self.lyrics = resp.json().get("lyrics")
                print("✓ Paroles récupérées avec succès")
                return True
            else:
                print(f"✗ Paroles introuvables (status {resp.status_code})")
                return False
                
        except Exception as e:
            print(f"✗ Erreur récupération lyrics : {e}")
            return False
    
    def display_tags(self):
        """Affiche toutes les métadonnées dans la console (debug)"""
        print("\n" + "="*50)
        print(f"📁 Fichier : {self.file_name}")
        print("="*50)
        print(f"🎵 Titre   : {self.title or '(vide)'}")
        print(f"👤 Artiste : {self.artist or '(vide)'}")
        print(f"💿 Album   : {self.album or '(vide)'}")
        print(f"📅 Année   : {self.year or '(vide)'}")
        print(f"🎸 Genre   : {self.genre or '(vide)'}")
        print(f"⏱️  Durée   : {self.duration or '(vide)'}")
        print(f"🖼️  Cover   : {'✓ Présente' if self.cover else '✗ Absente'}")
        if self.cover:
            print(f"   Taille : {len(self.cover.getvalue())} bytes")
        print(f"📝 Paroles : {'✓ Chargées' if self.lyrics else '✗ Non chargées'}")
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
