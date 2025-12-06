r"""!
@file Gui.py
@brief Interface graphique (GUI) basée sur Tkinter pour la gestion de fichiers audio.

@details Fournit une interface complète permettant d'explorer des dossiers, d'afficher et de modifier
les tags (métadonnées) des fichiers MP3 et FLAC, de gérer la pochette d'album via téléchargement iTunes,
et d'assurer la lecture audio (morceau unique ou playlist) via \c pygame et \c threading.

@section utils Fonctions Utilitaires
* \c fetch_cover_from_itunes() : Recherche et télécharge une pochette depuis l'API iTunes.

@section classes Classes Interagissant
* \c Directory : Pour l'exploration de dossiers et la génération/lecture de playlists XSPF.
* \c Metadata : Objet conteneur pour les tags et la durée d'un fichier.
* \c Mp3File / \c FlacFile : Classes audio spécialisées pour la lecture et la sauvegarde des tags.

@note L'initialisation de la lecture audio nécessite la librairie \c pygame et est gérée dans des threads séparés
afin de ne pas bloquer l'interface Tkinter.
"""
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import requests
import io
from PIL import Image, ImageTk 
from typing import List, Optional , Union
import threading
import xml.etree.ElementTree as ET
import pygame
import time
from urllib.parse import quote

# ============================================================
# 🚨 ATTENTION : IMPORTS DES CLASSES EXTERNES 🚨
# Assurez-vous que ces fichiers existent dans le même dossier.
# ============================================================
from Directory import Directory
from Metadata import Metadata
from Mp3File import Mp3File
from FlacFile import FlacFile


# --- Dépendances Mutagen (conservées pour les fonctions hors classe) ---
from mutagen.id3 import ID3, APIC 
from requests.exceptions import RequestException
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC, Picture
from mutagen import File


# ============================================================
# FONCTIONS DE TÉLÉCHARGEMENT DE COVER
# ============================================================
def fetch_cover_from_itunes(artist: str, album: str) -> Optional[bytes]:
    r"""!
    @brief Recherche et télécharge une cover d'album depuis l'API iTunes.

    @details Cherche d'abord l'album via l'artiste et le titre de l'album, puis
    télécharge la version haute résolution de l'illustration (600x600).

    @param artist [in] Nom (str) de l'artiste.
    @param album [in] Nom (str) de l'album.
    @return Optional[bytes] Les données binaires de l'image JPEG, ou \c None en cas d'échec ou de timeout.
    """
    if not artist or not album:
        return None
    
    search_term = f"{artist} {album}"
    url = "https://itunes.apple.com/search"
    params = {
        "term": search_term, "media": "music",
        "entity": "album", "limit": 1
    }
    
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code != 200: return None
        data = response.json()
        if data.get("resultCount", 0) == 0: return None
        
        artwork_url = data["results"][0].get("artworkUrl100")
        if not artwork_url: return None
        
        artwork_url = artwork_url.replace("100x100", "600x600") 
        img_response = requests.get(artwork_url, timeout=5)
        
        if img_response.status_code == 200:
            return img_response.content
        else:
            return None
            
    except RequestException as e:
        print(f"Erreur lors de la recherche iTunes : {e}")
        return None

# ============================================================
# INTERFACE GRAPHIQUE TKINTER (CORRIGÉE)
# ============================================================

class Gui(tk.Tk):
    r"""!
    @class Gui
    @brief Classe principale de l'interface graphique du gestionnaire musical.

    @details Hérite de \c tk.Tk. Gère l'affichage des panneaux (Explorateur, Métadonnées, Playlist),
    les événements utilisateur, et toute la logique de lecture audio via \c pygame et \c threading.

    @var playlist
    @details Liste (\c List) des objets \c Mp3File ou \c FlacFile actuellement dans la playlist.

    @var current_directory
    @details Instance \c Directory du dernier dossier exploré.

    @var selected_file
    @details Instance \c Metadata du fichier actuellement sélectionné dans l'explorateur.

    @var is_playing_playlist
    @details Booléen indiquant si la lecture d'une playlist est active.

    @var playlist_thread
    @details Référence au thread gérant la boucle de lecture de la playlist.
    """
    def __init__(self):
        r"""!
        @brief Constructeur. Initialise la fenêtre principale et la structure des panneaux.

        @details Masque le panneau central de métadonnées au démarrage, tant qu'aucun fichier n'est sélectionné.
        """
        super().__init__()
        self.playlist: List[Union['Mp3File', 'FlacFile']] = []
        self.title("Gestionnaire Musical Simple (Tkinter)")
        self.geometry("1000x600")
        self.resizable(True, True) 
        
        self.current_directory: Directory = None
        self.selected_file: Metadata = None
        self.cover_image_tk = None
        self.is_playing_playlist: bool = False
        self.playlist_thread: Optional[threading.Thread] = None
        self.current_playlist_index: int = 0
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Header 
        header_frame = tk.Frame(self, padx=10, pady=10)
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)
        
        tk.Button(header_frame, text="Ouvrir Playlist", command=self.open_playlist).pack(side="right", padx=5)
        tk.Button(header_frame, text="Ouvrir Dossier", command=self.open_directory).pack(side="right", padx=5)
        
        # 2. Contenu principal
        main_content = tk.Frame(self)
        main_content.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        main_content.grid_columnconfigure(0, weight=1)
        main_content.grid_columnconfigure(1, weight=2)
        main_content.grid_columnconfigure(2, weight=1)
        main_content.grid_rowconfigure(0, weight=1)

        self.create_left_panel(main_content)
        self.create_center_panel(main_content)
        self.create_right_panel(main_content)
        
        # 🟢 MASQUER LE PANNEAU MÉTADONNÉES AU DÉMARRAGE
        self.center_frame.grid_remove()

        # 3. Footer
        self.footer_label = tk.Label(self, text="Prêt | 0 fichiers trouvés", anchor="w")
        self.footer_label.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        

    # ============================================================
    # PANNEAUX ET UI
    # ============================================================

    def create_left_panel(self, parent):
        r"""!
        @brief Crée le panneau d'exploration de fichiers (Liste des fichiers et filtre).

        @param parent [in] Le conteneur parent (\c tk.Frame).
        """
        frame = tk.LabelFrame(parent, text="Explorateur de Fichiers", padx=5, pady=5)
        frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        tk.Label(frame, text="Filtrer:").grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.search_entry = tk.Entry(frame)
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(50, 0), pady=(0, 5))
        self.search_entry.bind("<KeyRelease>", self.filter_files)

        scrollbar = tk.Scrollbar(frame)
        scrollbar.grid(row=1, column=1, sticky="ns")
        
        self.file_listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set, selectmode=tk.SINGLE)
        self.file_listbox.grid(row=1, column=0, sticky="nsew")
        self.file_listbox.bind('<<ListboxSelect>>', self.on_file_select)
        
        scrollbar.config(command=self.file_listbox.yview)

    def create_center_panel(self, parent):
        r"""!
        @brief Crée le panneau central de métadonnées.

        @details Stocke la référence du panneau principal dans \c self.center_frame pour l'affichage/masquage dynamique.

        @param parent [in] Le conteneur parent (\c tk.Frame).
        """
        self.center_frame = tk.LabelFrame(parent, text="Métadonnées", padx=10, pady=5)
        self.center_frame.grid(row=0, column=1, sticky="nsew", padx=10)
        self.center_frame.grid_columnconfigure(0, weight=1)
        
        frame = self.center_frame
        
        canvas = tk.Canvas(frame)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        self.meta_scroll_frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=self.meta_scroll_frame, anchor="nw", width=450)
        self.meta_scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion = canvas.bbox("all")))

        # 1. 🖼️ ZONE DE COUVERTURE FIXE
        cover_frame = tk.Frame(self.meta_scroll_frame, width=300, height=300)
        cover_frame.pack(pady=10)
        cover_frame.pack_propagate(False)
        
        self.cover_label = tk.Label(cover_frame, 
                                    text="🖼\nCouverture d'album", 
                                    bg="lightgray", 
                                    relief=tk.RIDGE)
        self.cover_label.pack(fill="both", expand=True)

        
        self.btn_download_cover = tk.Button(self.meta_scroll_frame, text="⬇ Télécharger Cover (iTunes)", 
                                            command=self.download_and_save_cover)
        self.btn_download_cover.pack(pady=5)
        
        # --- Champs d'Entrée ---
        fields_frame = tk.Frame(self.meta_scroll_frame)
        fields_frame.pack(fill="x", padx=10, pady=10)
        fields_frame.grid_columnconfigure(1, weight=1)

        labels_mapping = [
            ("Titre", "title"),
            ("Artiste", "artist"),
            ("Album", "album"),
            ("Année", "year"),
            ("Durée", "duration"),
            ("Genre", "genre")
        ]
        
        self.entries = {}
        
        for i, (label_text, key) in enumerate(labels_mapping):
            tk.Label(fields_frame, text=f"{label_text}:").grid(row=i, column=0, sticky="w", pady=5, padx=(0, 10))
            entry = tk.Entry(fields_frame)
            entry.grid(row=i, column=1, sticky="ew", pady=5)
            self.entries[key] = entry
            
        self.entries['duration'].config(state='readonly')

        self.btn_save_tags = tk.Button(self.meta_scroll_frame, 
                                       text="💾 Sauvegarder les Tags Modifiés", 
                                       command=self.save_metadata, 
                                       bg="#5cb85c", fg="white")
        self.btn_save_tags.pack(fill="x", padx=10, pady=10)


       # --- Boutons de Lecture/Contrôle ---
        self.btn_play_file = tk.Button(self.meta_scroll_frame, text="▷ Lire le Morceau", 
                                       command=self.play_selected_file)
        self.btn_play_file.pack(fill="x", padx=10, pady=5)
        
        self.btn_stop_file = tk.Button(self.meta_scroll_frame, text="⏹ Arrêter la Lecture", 
                                       command=self.stop_playback) 
        self.btn_stop_file.pack(fill="x", padx=10, pady=5)

        self.btn_show_lyrics = tk.Button(self.meta_scroll_frame, 
                                         text="🎤 Afficher les Paroles", 
                                         command=self.show_lyrics)
        self.btn_show_lyrics.pack(fill="x", padx=10, pady=5)


    def create_right_panel(self, parent):
        r"""!
        @brief Crée le panneau de gestion de la playlist.

        @param parent [in] Le conteneur parent (\c tk.Frame).
        """
        frame = tk.LabelFrame(parent, text="Playlist Actuelle", padx=5, pady=5)
        frame.grid(row=0, column=2, sticky="nsew", padx=(10, 0))
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        self.playlist_listbox = tk.Listbox(frame, selectmode=tk.EXTENDED)
        self.playlist_listbox.grid(row=0, column=0, sticky="nsew", pady=5)
        
        btn_frame = tk.Frame(frame)
        btn_frame.grid(row=1, column=0, sticky="ew")
        
        tk.Button(btn_frame, text="+ Ajouter", command=self.add_from_file_dialog).pack(side="left", expand=True, fill="x", padx=(0, 5))
        tk.Button(btn_frame, text="- Retirer", command=self.remove_from_playlist).pack(side="left", expand=True, fill="x", padx=(5, 0))
        tk.Button(btn_frame, text="💾 XSPF", command=self.save_playlist_dialog).pack(side="right", padx=5)
        
        tk.Button(btn_frame, text="▷ Lire", command=self.play_playlist).pack(side="left", expand=True, fill="x", padx=5)
        tk.Button(btn_frame, text="⏭ Suivant", command=self.next_track).pack(side="right", expand=True, fill="x", padx=(5, 0))
    
    
    # ============================================================
    # MÉTHODES D'AFFICHAGE/MASQUAGE DU PANNEAU CENTRAL
    # ============================================================
    
    def show_metadata_panel(self):
        r"""!
        @brief Affiche le panneau de métadonnées (\c self.center_frame).
        """
        self.center_frame.grid()

    def hide_metadata_panel(self):
        r"""!
        @brief Masque le panneau de métadonnées (\c self.center_frame).
        """
        self.center_frame.grid_remove()


    # ============================================================
    # FONCTIONS DE LOGIQUE
    # ============================================================

    def open_directory(self):
        r"""!
        @brief Ouvre une boîte de dialogue pour sélectionner un dossier et lance l'exploration.
        """
        directory_path = filedialog.askdirectory(title="Sélectionner un dossier")
        if not directory_path: return
            
        self.footer_label.config(text="Exploration en cours...")
        self.update()
        
        self.current_directory = Directory(directory_path)
        self.current_directory.exploration_dir()
        
        self.update_file_list()
        
    def filter_files(self, event=None):
        r"""!
        @brief Filtre la liste des fichiers de l'explorateur en fonction du texte entré.

        @param event [in] Événement déclencheur (ignoré).
        """
        search_text = self.search_entry.get().lower()
        self.file_listbox.delete(0, tk.END)
        if not self.current_directory: return
            
        for metadata in self.current_directory.files:
            title = (metadata.title or metadata.file_name).lower()
            artist = (metadata.artist or "").lower()
            
            if search_text in title or search_text in artist:
                display_title = metadata.title or metadata.file_name
                display_artist = metadata.artist or "Artiste inconnu"
                self.file_listbox.insert(tk.END, f"{display_title} - {display_artist}")

    def update_file_list(self):
        r"""!
        @brief Met à jour la Listbox de l'explorateur de fichiers.

        @details Masque le panneau de métadonnées si la liste est vide après l'exploration.
        """
        self.search_entry.delete(0, tk.END)
        self.file_listbox.delete(0, tk.END)
        
        if not self.current_directory or not self.current_directory.files:
            self.hide_metadata_panel() 
            self.footer_label.config(text="Prêt | 0 fichiers trouvés")
            return

        for metadata in self.current_directory.files:
            title = metadata.title or metadata.file_name
            artist = metadata.artist or "Artiste inconnu"
            self.file_listbox.insert(tk.END, f"{title} - {artist}")
            
        count = len(self.current_directory.files)
        self.footer_label.config(text=f"Prêt | {count} fichiers trouvés")

    def on_file_select(self, event):
        r"""!
        @brief Gère la sélection d'un fichier dans la Listbox de l'explorateur.

        @details Affiche le panneau de métadonnées et appelle \c display_metadata().

        @param event [in] Événement de sélection de Listbox.
        """
        selected_indices = self.file_listbox.curselection()
        if not selected_indices: return
            
        index = selected_indices[0]
        
        search_text = self.search_entry.get().lower()
        filtered_files = []
        for metadata in self.current_directory.files:
            title = (metadata.title or metadata.file_name).lower()
            artist = (metadata.artist or "").lower()
            if search_text in title or search_text in artist:
                filtered_files.append(metadata)

        if index < len(filtered_files):
            self.selected_file = filtered_files[index]
            self.show_metadata_panel() 
            self.display_metadata(self.selected_file)

    def display_metadata(self, metadata: Metadata):
        r"""!
        @brief Affiche les métadonnées et la pochette du fichier sélectionné dans le panneau central.

        @param metadata [in] L'objet \c Metadata à afficher.
        """
        self.selected_file = metadata
        if not metadata: return
            
        # Remplir les champs
        for key, entry in self.entries.items():
            value = getattr(metadata, key, "") 
            
            entry.config(state='normal')
            entry.delete(0, tk.END)
            entry.insert(0, str(value or ""))
            if key == 'duration': 
                entry.config(state='readonly')
        
        # Gérer la Cover
        self.cover_label.config(image="", text="🖼\nCouverture d'album", bg="lightgray")
        if metadata.cover:
            try:
                metadata.cover.seek(0)
                img = Image.open(metadata.cover).resize((300, 300))
                self.cover_image_tk = ImageTk.PhotoImage(img)
                self.cover_label.config(image=self.cover_image_tk, text="", bg="white")
            except Exception:
                self.cover_image_tk = None


    def save_metadata(self):
        r"""!
        @brief Récupère les tags modifiés des champs d'entrée et les sauvegarde dans le fichier audio.
        """
        if not self.selected_file:
            messagebox.showinfo("Info", "Aucun fichier sélectionné.")
            return

        new_tags = {}
        for key, entry in self.entries.items():
            if key != 'duration':
                new_tags[key] = entry.get()

        try:
            if self.selected_file.save_tags(**new_tags):
                
                self.selected_file.extract_tags() 
                
                for tag_key, tag_value in new_tags.items():
                    setattr(self.selected_file, tag_key, tag_value)
                
                self.update_file_list()
                self.display_metadata(self.selected_file)
                
                messagebox.showinfo("Succès", "Métadonnées sauvegardées avec succès.")
            else:
                messagebox.showerror("Erreur", "La sauvegarde des métadonnées a échoué.")
        
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de sauvegarder: {e}")

    def download_and_save_cover(self):
        r"""!
        @brief Télécharge la pochette depuis iTunes et demande à l'utilisateur de la sauvegarder.
        """
        if not self.selected_file:
            messagebox.showinfo("Info", "Veuillez sélectionner un fichier d'abord.")
            return
            
        artist = self.entries['artist'].get().strip() 
        album = self.entries['album'].get().strip()

        if not artist or not album:
            messagebox.showwarning("Attention", "Veuillez renseigner **l'artiste** et **l'album**.")
            return

        self.btn_download_cover.config(text="Recherche en cours...", state=tk.DISABLED)
        self.update()

        def fetch_in_thread():
            cover_data = fetch_cover_from_itunes(artist, album)
            self.after(0, lambda: self._handle_cover_result(cover_data))

        threading.Thread(target=fetch_in_thread, daemon=True).start()

    def _handle_cover_result(self, cover_data):
        r"""!
        @brief Gestionnaire post-thread pour le résultat du téléchargement de la cover.

        @details Affiche l'image trouvée et propose sa sauvegarde dans le fichier audio et le dossier local.

        @param cover_data [in] Les données binaires (bytes) de l'image, ou \c None.
        """
        self.btn_download_cover.config(text="⬇ Télécharger Cover (iTunes)", state=tk.NORMAL)

        if not cover_data:
            messagebox.showwarning("Info", "Aucune cover trouvée en ligne.")
            return
        
        try:
            img = Image.open(io.BytesIO(cover_data)).resize((300, 300))
            self.cover_image_tk = ImageTk.PhotoImage(img)
            self.cover_label.config(image=self.cover_image_tk, text="", bg="white")

            if messagebox.askyesno("Confirmation", "Cover trouvée! Voulez-vous la sauvegarder dans le fichier?"):
                
                if self.selected_file.save_cover(cover_data):
                
                    album_dir = os.path.dirname(self.selected_file.file_path)
                    cover_path = os.path.join(album_dir, "cover.jpg")
                    with open(cover_path, "wb") as f:
                         f.write(cover_data)
                         
                    self.selected_file.extract_cover() 
                    self.display_metadata(self.selected_file)
                    messagebox.showinfo("Succès", "Cover sauvegardée avec succès!")
                else:
                    messagebox.showerror("Erreur", "Échec de la sauvegarde de la cover dans le fichier audio.")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'afficher ou de sauvegarder la cover: {e}")
            self.display_metadata(self.selected_file)

    def play_selected_file(self):
        r"""!
        @brief Lit le morceau sélectionné.

        @details Arrête toute lecture en cours, puis lance la lecture du fichier
        en utilisant la méthode \c play() dans un thread séparé.
        """
        if not self.selected_file:
            messagebox.showinfo("Info", "Aucun fichier sélectionné.")
            return
            
        file_path = self.selected_file.file_path

        self.stop_playback(silent=True) 

        if file_path.lower().endswith(".mp3"):
            audio_instance = Mp3File(file_path)
        elif file_path.lower().endswith(".flac"):
            audio_instance = FlacFile(file_path)
        else:
            messagebox.showwarning("Erreur", "Format non supporté pour la lecture.")
            return
            
        threading.Thread(target=audio_instance.play, daemon=True).start()
        
        self.footer_label.config(text=f"▶ Lecture en cours : {self.selected_file.title or self.selected_file.file_name}")

    def stop_playback(self, silent: bool = False):
        r"""!
        @brief Arrête immédiatement toute lecture audio en cours (morceau ou playlist).

        @details Utilise \c pygame.mixer.music.stop(). Réinitialise l'état de la lecture de playlist.

        @param silent [in] Booléen. Si \c True, ne montre pas de message d'information ou d'arrêt.
        """
        if pygame and pygame.mixer.get_init():
            pygame.mixer.music.stop()
            self.is_playing_playlist = False
            self.playlist_thread = None
            if not silent:
                 self.footer_label.config(text="⏹ Lecture arrêtée.")
        elif not silent:
            messagebox.showinfo("Info", "Aucune lecture audio en cours.")

    def play_playlist(self):
        r"""!
        @brief Lance la lecture de la playlist en série dans un thread dédié.
        """
        if not self.playlist:
            messagebox.showinfo("Info", "La playlist est vide.")
            return

        self.stop_playback(silent=True) 
        
        self.current_playlist_index = 0
        self.is_playing_playlist = True
        
        self.playlist_thread = threading.Thread(target=self._playlist_playback_loop, daemon=True)
        self.playlist_thread.start()
        self.footer_label.config(text="▶ Démarrage de la playlist...")

    def _playlist_playback_loop(self):
        r"""!
        @brief Boucle de lecture de playlist exécutée dans un thread séparé.
        """
        while self.is_playing_playlist and self.current_playlist_index < len(self.playlist):
            audio_object = self.playlist[self.current_playlist_index]
            meta = audio_object.metadata
            
            self.after(0, lambda m=meta: self.footer_label.config(
                text=f"▶ Playlist ({self.current_playlist_index+1}/{len(self.playlist)}) : {m.title or m.file_name}"))

            file_path = audio_object.path
            
            try:
                audio_instance = audio_object
                audio_instance.play(wait_for_end=False)
            except Exception as e:
                print(f"Erreur de lecture pour {file_path}: {e}")
                self.current_playlist_index += 1
                continue

            index_before_wait = self.current_playlist_index
            while pygame.mixer.music.get_busy() and self.is_playing_playlist:
                time.sleep(0.1) 
            
            if not self.is_playing_playlist:
                break
                
            if not pygame.mixer.music.get_busy() and self.current_playlist_index == index_before_wait:
                self.current_playlist_index += 1
        
        if self.current_playlist_index >= len(self.playlist) and self.is_playing_playlist:
            self.after(0, lambda: self.footer_label.config(text="Fin de la playlist. 🏁"))

        self.is_playing_playlist = False
        self.playlist_thread = None

    def next_track(self):
        r"""!
        @brief Force l'arrêt du morceau en cours et passe immédiatement au morceau suivant de la playlist.
        """
        if not self.is_playing_playlist:
            messagebox.showinfo("Info", "Aucune playlist en cours de lecture.")
            return

        if pygame and pygame.mixer.get_init():
            pygame.mixer.music.stop()
            
        self.current_playlist_index += 1
        
        if self.current_playlist_index >= len(self.playlist):
            self.is_playing_playlist = False
            self.after(0, lambda: self.footer_label.config(text="Fin de la playlist. 🏁"))
        else:
            self.after(0, lambda: self.footer_label.config(text="⏭ Morceau suivant..."))

    def add_to_playlist(self, metadata: Metadata):
        r"""!
        @brief Ajoute un objet Metadata à la playlist (si non déjà présent) et met à jour l'affichage.

        @param metadata [in] L'objet \c Metadata à ajouter.
        """
        if metadata not in self.playlist:
            self.playlist.append(metadata)
            self.update_playlist_display()
            
    def add_from_file_dialog(self):
        r"""!
        @brief Ouvre un dialogue pour ajouter des fichiers MP3/FLAC à la playlist.
        """
        file_paths = filedialog.askopenfilenames(
             title="Ajouter des fichiers à la playlist",
             filetypes=[("Fichiers audio supportés", "*.mp3 *.flac")]
         )
        
        if not file_paths: return
        
        added_count = 0
        failed_files = []
        
        for path in file_paths:
            try:
                if path.lower().endswith(".mp3"):
                    audio_object = Mp3File(path)
                elif path.lower().endswith(".flac"):
                    audio_object = FlacFile(path)
                else:
                    continue
                
                self.playlist.append(audio_object)
                added_count += 1
            except Exception as e:
                failed_files.append(os.path.basename(path))
                print(f"Erreur lors du traitement de {path}: {e}")
        
        self.update_playlist_display()
        
        if added_count > 0:
            messagebox.showinfo("Playlist", f"✅{added_count} fichier(s) ajouté(s) à la playlist.")
        
        if failed_files:
            messagebox.showwarning("Avertissement", 
                                   f" {len(failed_files)} fichier(s) n'a/ont pas pu être ajouté(s) : " +
                                   ", ".join(failed_files))
            
    def remove_from_playlist(self):
        r"""!
        @brief Retire les éléments sélectionnés de la Listbox de la playlist.
        """
        selected_indices = self.playlist_listbox.curselection()
        if not selected_indices:
            messagebox.showinfo("Info", "Veuillez sélectionner un morceau à retirer.")
            return

        for index in reversed(selected_indices):
            del self.playlist[index]

        self.update_playlist_display()
        
    def update_playlist_display(self):
        r"""!
        @brief Met à jour la Listbox de la playlist pour refléter le contenu de \c self.playlist.
        """
        self.playlist_listbox.delete(0, tk.END)
        
        for idx, audio_object in enumerate(self.playlist):
            
            if hasattr(audio_object, 'metadata') and audio_object.metadata is not None:
                meta = audio_object.metadata
                
                title = meta.title or meta.file_name 
                artist = meta.artist or "Artiste inconnu"
                
                self.playlist_listbox.insert(tk.END, f"{idx+1}. {title} - {artist}")
            else:
                path = getattr(audio_object, 'path', 'Fichier inconnu')
                self.playlist_listbox.insert(tk.END, f"{idx+1}. ⚠️ Erreur d'extraction : {os.path.basename(path)}")
                
    def open_playlist(self):
        r"""!
        @brief Ouvre un dialogue pour charger une playlist XSPF et peuple \c self.playlist.
        """
        filename = filedialog.askopenfilename(
            title="Ouvrir une playlist",
            filetypes=[("XSPF Playlist", ".xspf"), ("Tous les fichiers", ".*")]
        )
        
        if not filename: return
        
        try:
            ns = {'xspf': 'http://xspf.org/ns/0/'}
            tree = ET.parse(filename)
            root = tree.getroot()
            self.playlist.clear()
            
            loaded_count = 0
            for track in root.findall('.//xspf:track', ns):
                location = track.find('xspf:location', ns)
                if location is not None:
                    file_path = location.text.replace('file://', '')
                    
                    if os.path.exists(file_path):
                        if file_path.lower().endswith(".mp3"):
                            metadata = Mp3File(file_path)
                        elif file_path.lower().endswith(".flac"):
                            metadata = FlacFile(file_path)
                        else:
                            continue
                            
                        self.playlist.append(metadata)
                        loaded_count += 1
            
            self.update_playlist_display()
            messagebox.showinfo("Succès", f"Playlist chargée: {loaded_count} morceaux ajoutés.")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir la playlist: {e}")

    def save_playlist_dialog(self):
        r"""!
        @brief Ouvre un dialogue pour sauvegarder \c self.playlist au format XSPF.
        """
        if not self.playlist:
            messagebox.showwarning("Attention", "La playlist est vide.")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".xspf",
            filetypes=[("XSPF Playlist", ".xspf"), ("Tous les fichiers", ".*")]
        )
        
        if not filename: return
            
        try:
            temp_dir = Directory(".") 
            temp_dir.files = self.playlist
            temp_dir.generate_xspf_playlist(filename)
            
            messagebox.showinfo("Succès", f"Playlist sauvegardée: {filename}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de sauvegarder: {e}")

    def _display_lyrics_window(self, title: str, lyrics: str):
        r"""!
        @brief Ouvre une fenêtre secondaire pour afficher les paroles.

        @param title [in] Titre (str) du morceau (pour le titre de la fenêtre).
        @param lyrics [in] Texte (str) des paroles à afficher.
        """
        top = tk.Toplevel(self)
        top.title(f"Paroles : {title}")
        top.geometry("600x450")
        
        scrollbar = tk.Scrollbar(top)
        scrollbar.pack(side="right", fill="y")
        
        text_widget = tk.Text(top, yscrollcommand=scrollbar.set, wrap="word", font=("Arial", 10))
        text_widget.insert(tk.END, lyrics)
        text_widget.config(state="disabled") # Lecture seule
        text_widget.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        scrollbar.config(command=text_widget.yview)

    def _fetch_lyrics_worker(self, metadata: 'Metadata'):
        r"""!
        @brief Fonction worker (exécutée dans un thread) pour récupérer les paroles via API (lyrics.ovh).

        @param metadata [in] L'objet \c Metadata contenant l'artiste et le titre.
        """
        artist = metadata.artist
        title = metadata.title
        lyrics = None
        
        if not artist or not title:
            self.after(0, lambda: messagebox.showwarning("Paroles", "⚠ Artiste ou titre manquant pour rechercher les paroles."))
            return
            
        url = f"https://api.lyrics.ovh/v1/{quote(artist)}/{quote(title)}"
        
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status() 

            if resp.status_code == 200:
                data = resp.json()
                if 'lyrics' in data:
                    lyrics = data['lyrics']
        
        except requests.exceptions.Timeout:
            self.after(0, lambda: messagebox.showerror("Erreur Paroles", "✗ Le temps d'attente a été dépassé."))
        except requests.exceptions.ConnectionError:
            self.after(0, lambda: messagebox.showerror("Erreur Paroles", "✗ Impossible de se connecter à l'hôte."))
        except requests.exceptions.HTTPError as e:
            self.after(0, lambda: messagebox.showwarning("Paroles", f"✗ Paroles introuvables (Erreur HTTP {e.response.status_code})."))
        except requests.exceptions.RequestException:
            self.after(0, lambda: messagebox.showerror("Erreur Paroles", "✗ Problème lors de la requête HTTP."))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Erreur Paroles", f"✗ Erreur inattendue : {e}"))
        
        self.after(0, lambda: self._handle_lyrics_result(metadata, lyrics))


    def _handle_lyrics_result(self, metadata: 'Metadata', lyrics: Optional[str]):
        r"""!
        @brief Gère le résultat de la recherche de paroles (sur le thread principal).

        @details Affiche les paroles dans une nouvelle fenêtre ou affiche un message si elles sont introuvables.

        @param metadata [in] L'objet \c Metadata original.
        @param lyrics [in] Le texte (str) des paroles, ou \c None si non trouvé.
        """
        self.btn_show_lyrics.config(text="🎤 Afficher les Paroles", state=tk.NORMAL)
        
        if lyrics:
            self._display_lyrics_window(metadata.title or metadata.file_name, lyrics)
        else:
            messagebox.showinfo("Paroles", f"Aucune parole trouvée pour {metadata.artist} - {metadata.title}.")

    def show_lyrics(self):
        r"""!
        @brief Lance la récupération des paroles dans un thread au clic du bouton.

        @details Désactive le bouton et démarre \c _fetch_lyrics_worker().
        """
        if not self.selected_file:
            messagebox.showinfo("Info", "Aucun fichier sélectionné.")
            return

        self.btn_show_lyrics.config(text="Recherche en cours...", state=tk.DISABLED)
        self.update()

        metadata_to_fetch = self.selected_file 
        
        threading.Thread(target=lambda: self._fetch_lyrics_worker(metadata_to_fetch), daemon=True).start()
        
if __name__ == "__main__":
    # L'initialisation de Pygame est nécessaire si la lecture audio est utilisée
    try:
        pygame.init()
        pygame.mixer.init()
    except Exception as e:
        print(f"Avertissement : Pygame/Mixer non initialisé. La lecture audio pourrait ne pas fonctionner. Erreur: {e}")
        
    app = Gui()
    app.mainloop()
