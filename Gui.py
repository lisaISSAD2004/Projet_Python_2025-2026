import os
import threading
from urllib.parse import unquote, urlparse
import time
import io

# Imports des autres couches
from library.view.mainview import MainView
from library.apis.audioservices import AudioService
from library.apis.apiservices import ApiService
from library.model.Directory import Directory
from library.model.Mp3File import Mp3File
from library.model.FlacFile import FlacFile

class MainController:
    def __init__(self):
        # 1. Initialiser les Services
        self.audio_service = AudioService()
        self.api_service = ApiService()

        # 2. Initialiser les Données (Modèle)
        self.current_directory = None
        self.selected_audio = None
        self.playlist = []

        self.is_paused = False

        # 3. Initialiser la Vue
        self.view = MainView(controller=self) 

    def run(self):
        """Lance l'application"""
        self.view.mainloop()

    # ==========================
    # GESTION DOSSIERS / FICHIERS
    # ==========================

    def handle_open_directory(self):
        """Appelé par le bouton 'Ouvrir Dossier'"""
        path = self.view.ask_directory()
        if path:
            self.load_directory(path)

    def handle_drop_explorer(self, data):
        """Appelé quand on lâche un dossier"""
        paths = self._parse_dnd_paths(data)
        if paths and os.path.isdir(paths[0]):
            self.load_directory(paths[0])

    def load_directory(self, path):
        """Logique commune pour charger un dossier"""
        print(f"Controller: Chargement dossier -> {path}")
        try:
            self.current_directory = Directory(path)
            self.current_directory.exploration_dir()
            self.view.update_file_list(self.current_directory.files)
            self.view.update_footer(f"Prêt | {len(self.current_directory.files)} fichiers trouvés")
        except Exception as e:
            self.view.show_message("Erreur", f"Impossible d'ouvrir ce dossier: {e}", is_error=True)

    def handle_file_select(self, audio_object):
        """Appelé quand on clique sur une musique"""
        self.selected_audio = audio_object
        self.view.display_metadata(audio_object.metadata)

    # ==========================
    # LECTURE AUDIO
    # ==========================

    # Dans controler/maincontroler.py

    def handle_play(self):
        """Gère le bouton Play/Pause intelligemment"""
        
        # CAS 1 : On est en PAUSE -> On REPREND
        if self.is_paused:
            self.audio_service.unpause()
            self.is_paused = False
            self.view.update_play_button("⏸", "#D32F2F")
            
            # --- AJOUT IMPORTANT : ON RELANCE LE COMPTEUR ! ---
            self.check_time_loop()
            # --------------------------------------------------
            return

        # CAS 2 : La musique JOUE -> On met en PAUSE
        if self.audio_service.is_playing():
            self.audio_service.pause()
            self.is_paused = True
            self.view.update_play_button("▶", "#E040FB")
            # Ici, la boucle check_time_loop va s'arrêter toute seule au prochain tour
            return

        # CAS 3 : Rien ne joue -> On LANCE du début
        if self.selected_audio:
            self._start_new_song(self.selected_audio.path)

    def check_time_loop(self):
        """Met à jour le temps chaque seconde"""
        if self.audio_service.is_playing() and self.selected_audio:
            # 1. Temps actuel (vient de pygame en secondes)
            current_sec = self.audio_service.get_current_position()
            
            # 2. Durée totale (Le correctif est ici)
            raw_duration = self.selected_audio.metadata.duration
            total_sec = self._parse_duration(raw_duration)
            
            # Formater pour l'affichage (ex: "01:05" / "04:57")
            cur_fmt = self._format_time(current_sec)
            tot_fmt = self._format_time(total_sec)
            
            # Mettre à jour la vue (Titre/Artiste optionnels ici si déjà mis à jour par handle_play)
            # On met juste à jour le label du temps via update_timer_label si vous l'avez créé
            # Sinon on utilise update_footer
            self.view.update_footer(f"{cur_fmt} / {tot_fmt}", 
                                    title=self.selected_audio.metadata.title, 
                                    artist=self.selected_audio.metadata.artist)
            
            # Rappeler dans 1 seconde
            self.view.after(1000, self.check_time_loop)

    def handle_add_single_to_playlist(self, audio_obj):
        """Ajoute un seul fichier à la playlist (via clic droit)"""
        if not audio_obj: return
        
        # On évite les doublons exacts si on veut (optionnel)
        if audio_obj not in self.playlist:
            self.playlist.append(audio_obj)
            self.view.update_playlist_view(self.playlist)
            self.view.update_footer(f"Ajouté à la playlist : {audio_obj.metadata.title}")
        else:
            self.view.show_message("Info", "Ce titre est déjà dans la playlist.")

            
    def handle_stop(self):
        self.audio_service.stop()
        self.is_paused = False # Reset important
        self.view.update_footer("Arrêté")

    # ==========================
    # SAUVEGARDE & API
    # ==========================

    def handle_save_tags(self, tags_dict):
        """Appelé par le bouton 'Sauvegarder Tags'"""
        if not self.selected_audio: return

        # 1. Arrêter la musique pour libérer le fichier
        self.audio_service.stop()

        # 2. Sauvegarder via le Modèle
        if self.selected_audio.save_tags(**tags_dict):
            # 3. Recharger les infos pour vérifier
            self.selected_audio.extract_metadata()
            self.view.display_metadata(self.selected_audio.metadata)
            
            # 4. Mettre à jour la liste à gauche (si le titre a changé)
            self.view.update_file_list(self.current_directory.files)
            self.view.show_message("Succès", "Tags sauvegardés avec succès.")
        else:
            self.view.show_message("Erreur", "Échec de la sauvegarde.", is_error=True)

    def handle_download_cover(self):
        """Appelé par le bouton 'Télécharger Cover'"""
        if not self.selected_audio: return

        # Récupérer les infos actuelles de la vue (ou du modèle)
        entries = self.view.get_entry_values()
        artist = entries.get('artist')
        album = entries.get('album')

        # Lancer la recherche dans un thread pour ne pas figer l'interface
        threading.Thread(target=self._thread_download_cover, args=(artist, album), daemon=True).start()

    def _thread_download_cover(self, artist, album):
        # Appel API
        data = self.api_service.fetch_cover_hybrid(artist, album)
        
        # Mise à jour de la vue (Attention: certaines libs UI n'aiment pas être appelées depuis un thread)
        # Mais customtkinter gère ça relativement bien. Sinon utiliser self.view.after
        if data:
            # On demande à la vue d'afficher une confirmation ou l'image
            # Pour simplifier ici, on sauvegarde direct si l'utilisateur valide dans la vue
            # Note: Dans une architecture pure, le thread devrait renvoyer l'info au main thread.
            
            # Hack simple pour mettre à jour l'image sans confirmation complexe ici:
            self.audio_service.stop()
            if self.selected_audio.save_cover(data):
                self.selected_audio.extract_metadata()
                self.view.display_metadata(self.selected_audio.metadata)
                self.view.show_message("Info", "Cover trouvée et sauvegardée !")
        else:
            self.view.show_message("Info", "Aucune cover trouvée.")

    # ==========================
    # UTILITAIRES
    # ==========================
    def _parse_dnd_paths(self, data):
        if data.startswith('file://'):
            if '\r\n' in data: raw_paths = data.split('\r\n')
            else: raw_paths = data.split('\n')
            return [unquote(urlparse(p).path).strip() for p in raw_paths if p.strip()]
        return self.view.tk.splitlist(data)
    
    def _parse_duration(self, raw):
        """Transforme n'importe quel format (str '04:57', str '297', float 297.5) en secondes (float)"""
        if not raw: 
            return 0
        
        # Cas 1 : C'est déjà un nombre (int ou float)
        if isinstance(raw, (int, float)):
            return float(raw)
            
        # Cas 2 : C'est du texte (str)
        if isinstance(raw, str):
            # Si c'est formaté comme "04:57"
            if ":" in raw:
                try:
                    parts = raw.split(":")
                    # minutes * 60 + secondes
                    return int(parts[0]) * 60 + int(parts[1])
                except:
                    return 0
            # Si c'est juste un nombre en texte "297"
            try:
                return float(raw)
            except:
                return 0
                
        return 0
    # ----------------------------------------------
    
    def _format_time(self, seconds):
        # ... (votre fonction existante reste identique) ...
        if not seconds: return "00:00"
        try:
            seconds = float(seconds)
            m = int(seconds // 60)
            s = int(seconds % 60)
            return f"{m:02d}:{s:02d}"
        except:
            return "00:00"
        
    # ==========================
    # GESTION PAROLES
    # ==========================
    def handle_show_lyrics(self):
        if not self.selected_audio: return
        
        meta = self.selected_audio.metadata
        # On lance le thread
        threading.Thread(target=self._thread_lyrics, 
                         args=(meta.artist, meta.title, meta.album, meta.duration), 
                         daemon=True).start()

    def _thread_lyrics(self, artist, title, album, duration):
        dur_sec = int(duration) if isinstance(duration, (int, float)) else None
        data = self.api_service.fetch_lyrics_logic(artist, title, album, dur_sec)
        
        if data:
            text = data.get("syncedLyrics") or data.get("plainLyrics")
            if text:
                # Affichage dans la vue (via after pour thread-safety si besoin, mais customtkinter gère souvent)
                self.view.show_lyrics_window(text)
            else:
                self.view.show_message("Info", "Titre trouvé mais pas de texte.")
        else:
            self.view.show_message("Info", "Paroles introuvables.")

    # ==========================
    # GESTION PLAYLIST
    # ==========================
    def handle_add_playlist_files(self):
        paths = self.view.ask_open_filenames()
        if not paths: return
        
        self._add_paths_to_playlist(paths)

    def handle_drop_playlist(self, data):
        paths = self._parse_dnd_paths(data)
        self._add_paths_to_playlist(paths)

    def _add_paths_to_playlist(self, paths):
        count = 0
        for p in paths:
            if os.path.isfile(p):
                try:
                    if p.lower().endswith(".mp3"):
                        self.playlist.append(Mp3File(p))
                        count += 1
                    elif p.lower().endswith(".flac"):
                        self.playlist.append(FlacFile(p))
                        count += 1
                except: pass
        
        if count > 0:
            self.view.update_playlist_view(self.playlist)
            self.view.update_footer(f"{count} titres ajoutés à la playlist.")

    def handle_remove_playlist_item(self, index):
        if 0 <= index < len(self.playlist):
            del self.playlist[index]
            self.view.update_playlist_view(self.playlist)

    def handle_save_playlist(self):
        """Sauvegarde la playlist actuelle au format XSPF"""
        if not self.playlist:
            self.view.show_message("Info", "La playlist est vide.")
            return

        # 1. Demander où sauvegarder
        path = self.view.ask_save_filename()
        if not path: return

        try:
            # 2. Utiliser la classe Directory pour générer le XML
            # On crée une instance temporaire juste pour utiliser sa méthode de génération
            temp_dir = Directory(".") 
            temp_dir.files = self.playlist # On lui donne notre liste de lecture
            
            # 3. Générer le fichier
            temp_dir.generate_xspf_playlist(path)
            
            self.view.show_message("Succès", f"Playlist sauvegardée dans :\n{path}")
            
        except Exception as e:
            print(f"Erreur sauvegarde playlist : {e}")
            self.view.show_message("Erreur", f"Impossible de sauvegarder la playlist.\n{e}", is_error=True)

    # ==========================
    # LECTURE PLAYLIST
    # ==========================
    def handle_play_playlist(self):
        if not self.playlist: return
        
        self.audio_service.stop()
        self.is_playing_playlist = True
        self.current_playlist_index = 0
        
        # On lance la boucle de lecture dans un thread
        threading.Thread(target=self._playlist_loop, daemon=True).start()

    def handle_next_track(self):
        """Passe à la chanson suivante"""
        if not self.is_playing_playlist: return
        # On arrête le son, ce qui débloque la boucle et passe au suivant (+1)
        self.audio_service.stop()

    # --- C'EST CETTE FONCTION QUI MANQUAIT ---
    def handle_prev_track(self):
        """Passe à la chanson précédente"""
        if not self.is_playing_playlist or not self.playlist: return

        # EXPLICATION MATHÉMATIQUE :
        # La boucle _playlist_loop fait "index + 1" dès que le son s'arrête.
        # Si on est à la chanson 5 et qu'on veut la 4 :
        # On règle l'index sur 3.
        # On stoppe le son.
        # La boucle reprend, fait 3 + 1 = 4.
        # La chanson 4 se lance.
        
        self.current_playlist_index -= 2
        
        # Gestion des limites (si on est au début, on va à la fin)
        if self.current_playlist_index < -1:
            self.current_playlist_index = len(self.playlist) - 2

        # On force l'arrêt pour déclencher le changement
        self.audio_service.stop()

    def _playlist_loop(self):
        while self.is_playing_playlist and self.current_playlist_index < len(self.playlist):
            audio = self.playlist[self.current_playlist_index]
            
            # Mise à jour de l'interface
            meta = audio.metadata
            self.view.update_footer(f"Playlist {self.current_playlist_index+1}/{len(self.playlist)}", 
                                    title=meta.title, 
                                    artist=meta.artist)
            
            # --- AJOUT IMPORTANT ICI ---
            self.is_paused = False # On réinitialise la pause car c'est une nouvelle chanson
            # ---------------------------

            self.audio_service.play(audio.path)
            
            # Petit délai pour laisser le temps à pygame de lancer le statut "busy"
            time.sleep(1)
            
            # Attente active (tant que la musique joue OU qu'elle est en pause)
            # Si on ne vérifie pas self.is_paused, la boucle passerait à la suite dès qu'on met pause !
            while (self.audio_service.is_playing() or self.is_paused) and self.is_playing_playlist:
                time.sleep(0.5)
            
            # Passage au suivant (seulement si on n'a pas stoppé brutalement)
            if self.is_playing_playlist:
                self.current_playlist_index += 1
        
        self.is_playing_playlist = False
        self.view.update_footer("Fin de la playlist.")
        # On remet le bouton visuellement sur Play
        self.view.update_play_button("▶", "#E040FB")

    def handle_rename_file(self):
        """Renomme le fichier physique et met à jour l'interface"""
        if not self.selected_audio: return

        new_name = self.view.get_filename_input()
        if not new_name: return

        # On s'assure que l'extension est là (ex: .mp3)
        old_path = self.selected_audio.path
        extension = os.path.splitext(old_path)[1]
        
        if not new_name.lower().endswith(extension.lower()):
            new_name += extension

        # Construction du nouveau chemin complet
        directory = os.path.dirname(old_path)
        new_path = os.path.join(directory, new_name)

        if new_path == old_path: return # Pas de changement

        # 1. Arrêter la lecture (CRUCIAL pour éviter les crashs)
        self.audio_service.stop()

        try:
            # 2. Renommer sur le disque
            os.rename(old_path, new_path)
            
            # 3. Mettre à jour l'objet en mémoire
            self.selected_audio.path = new_path
            # Important : mettre à jour le chemin dans les métadonnées aussi pour l'affichage
            self.selected_audio.metadata.file_path = new_path 
            
            # 4. Rafraîchir l'interface
            self.view.update_file_list(self.current_directory.files)
            self.view.show_message("Succès", f"Fichier renommé en : {new_name}")
            
        except OSError as e:
            self.view.show_message("Erreur", f"Impossible de renommer le fichier.\nVérifiez qu'il n'existe pas déjà.\n{e}", is_error=True)

    def _start_new_song(self, path):
        """Lance une nouvelle musique (Remise à zéro de la pause)"""
        self.audio_service.play(path)
        self.is_paused = False # Important : on n'est plus en pause
        
        # Mise à jour UI
        meta = self.selected_audio.metadata
        self.view.update_footer("Lecture en cours...", title=meta.title, artist=meta.artist)
        
        # On lance le compteur de temps
        self.check_time_loop()

    # Dans controler/maincontroler.py

    def handle_open_playlist(self):
        """Ouvre une playlist XSPF et la charge dans l'interface"""
        # 1. Demander le fichier
        path = self.view.ask_open_playlist()
        if not path: return

        # 2. Parser le fichier via le Modèle
        # On utilise la méthode statique qu'on vient de créer
        new_files = Directory.parse_xspf_playlist(path)
        
        if new_files:
            # 3. Remplacer la playlist actuelle (ou self.playlist.extend(new_files) pour ajouter)
            self.playlist = new_files
            
            # 4. Mettre à jour l'interface
            self.view.update_playlist_view(self.playlist)
            self.view.show_message("Succès", f"Playlist chargée : {len(new_files)} titres.")
            self.view.update_footer(f"Playlist chargée ({len(new_files)} titres)")
        else:
            self.view.show_message("Info", "La playlist semble vide ou les fichiers ont été déplacés.", is_error=True)
