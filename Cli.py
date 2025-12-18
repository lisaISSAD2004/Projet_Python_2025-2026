"""!
@file Cli.py
@brief Interface en ligne de commande pour la gestion de fichiers audio MP3/FLAC.

... (Métadonnées inchangées) ...
"""

import argparse
import sys
import os
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, unquote
import time # Nécessaire pour time.sleep dans la boucle de playlist
import select # Nécessaire pour la détection de 'q' dans la boucle de playlist
try:
    import pygame # Importé ici pour être utilisé dans la boucle de playlist
except ImportError:
    pygame = None

# --- Imports ajustés pour la nouvelle architecture (library.model) ---
try:
    from library.model.Directory import Directory
    from library.model.Mp3File import Mp3File
    from library.model.FlacFile import FlacFile
    from library.model.Metadata import Metadata
except ImportError as e:
    # Fallback pour le développement local si les packages ne sont pas installés
    print(f"Erreur d'importation du modèle (vérifiez votre PYTHONPATH): {e}")
   


def main():
    """
    @brief Point d'entrée principal du programme en ligne de commande.
    ...
    """
    parser = argparse.ArgumentParser(
        prog="python3 Cli.py",
        description=(
            "Interface en ligne de commande pour gérer les fichiers audio MP3/FLAC.\n\n"
            "Vous pouvez lister, lire, inspecter ou modifier les métadonnées de vos chansons."
        ),
        add_help=False,
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument("-h", "--help", action="help", help="afficher l'aide et quitter")
    parser.add_argument("-d", "--directory", help="Explorer un dossier et lister tous les fichiers audio à l’intérieur (MP3/FLAC).")
    parser.add_argument("-f", "--file", help="Afficher les informations de métadonnées d’un fichier audio.")
    parser.add_argument("-p", "--play", help="Lire un fichier audio (MP3 ou FLAC) ou une playlist XSPF.")
    parser.add_argument("-o", "--output", help="Spécifier un fichier de sortie pour la playlist (ex: playlist.xspf)")
    parser.add_argument("-u", "--update-tags", nargs=argparse.REMAINDER, help=("Mettre à jour les métadonnées de la chanson (file=<path> title=v artist=v album=v year=v)."))

    args = parser.parse_args()

    # --- Aucun argument ---
    if len(sys.argv) == 1:
        print("Erreur : aucun paramètre fourni.")
        print("Tapez 'python3 Cli.py -h' ou '--help' pour afficher l’aide.")
        sys.exit(1)

    # ====================================================================
    # --- Cas 1 : Exploration d’un dossier (-d / --directory) ---
    # ====================================================================
    if args.directory:
        directory = Directory(args.directory)
        directory.dir_exist()
        directory.exploration_dir()

        # AFFICHAGE DE L'EXPLORATION
        print("\n📂 Fichiers audio trouvés (MP3/FLAC) :")
        if directory.files:
            for i, audio_file_obj in enumerate(directory.files):
                print(f"  {i+1}. {audio_file_obj.path}")
        else:
            print("  Aucun fichier MP3 ou FLAC valide trouvé dans le répertoire.")
            
        if args.output:
            try:
                directory.generate_xspf_playlist(args.output)
                print(f"\n✅ Playlist XSPF générée avec succès dans : {args.output}")
            except Exception as e:
                print(f"Erreur lors de la génération de la playlist : {e}")


    # ====================================================================
    # --- Cas 2 : Affichage des métadonnées (-f / --file) ---
    # ====================================================================
    elif args.file:
        file_path = args.file
        
        if not os.path.exists(file_path):
            print(f"Erreur : Fichier non trouvé ou extension inconnue à ce chemin : {file_path}")
            sys.exit(1)
            
        if not (file_path.lower().endswith(".mp3") or file_path.lower().endswith(".flac")):
            print(f"Erreur : Extension non supportée pour l'affichage des métadonnées. Utilisez MP3 ou FLAC : {file_path}")
            sys.exit(1)
        
        if file_path.lower().endswith(".mp3"):
            audio_file = Mp3File(file_path)
        elif file_path.lower().endswith(".flac"):
            audio_file = FlacFile(file_path)
        
        meta = audio_file.metadata
        
        meta.display_tags()
        print("\n📥 Récupération des paroles...")
        meta.fetch_lyrics()
        
        try:
            if meta.lyrics:
                meta.display_lyrics()
            else:
                print("✗ Les paroles n'ont pas été chargées.")
        
        except AttributeError:
            print("✗ Les paroles n'ont pas été chargées.")

    # ====================================================================
    # --- Cas 3 : Lire un fichier ou playlist (-p / --play) ---
    # ====================================================================
    elif args.play:
        path = args.play

        try:
            # Lecture d'une playlist XSPF
            if path.lower().endswith(".xspf"):
                print(f"Ouverture de la playlist : {path}")

                tree = ET.parse(path)
                root = tree.getroot()
                ns = {"xspf": "http://xspf.org/ns/0/"}

                tracks = []
                for track_xml in root.findall("xspf:trackList/xspf:track", ns):
                    location = track_xml.find("xspf:location", ns)
                    
                    if location is not None and location.text:
                        
                        # CORRECTION DE LA LOGIQUE DE DÉCODAGE XSPF
                        uri_path = urlparse(location.text).path
                        real_path = unquote(uri_path)
                        
                        # Création de l'objet AudioFile avec le chemin réel, si le fichier existe
                        if os.path.exists(real_path):
                            if real_path.lower().endswith(".mp3"):
                                tracks.append(Mp3File(real_path))
                            elif real_path.lower().endswith(".flac"):
                                tracks.append(FlacFile(real_path))
                        else:
                            # Tente de corriger le chemin pour un cas Windows /...
                            if os.name == 'nt' and real_path.startswith('/') and ':' in real_path:
                                corrected_path = real_path.lstrip('/')
                                if os.path.exists(corrected_path):
                                    if corrected_path.lower().endswith(".mp3"): tracks.append(Mp3File(corrected_path))
                                    elif corrected_path.lower().endswith(".flac"): tracks.append(FlacFile(corrected_path))
                            # Attention : Le chemin non trouvé sera ignoré par défaut

                if not tracks:
                    print("Aucune piste audio valide trouvée dans la playlist.")
                    sys.exit(1)

                print(f"🎵 {len(tracks)} morceau(x) trouvé(s). Lecture en cours...\n")

                for audio_file in tracks:
                    # Lecture de la playlist: wait_for_end=False pour ne pas bloquer
                    audio_file.play(wait_for_end=False) 
                    
                # -------------------------------------------------------------------
                # CORRECTION : Boucle d'attente pour maintenir Pygame actif (lecture de la playlist)
                # -------------------------------------------------------------------
                if pygame and pygame.mixer.get_init():
                    print("\n▶ Lecture de la playlist en cours. Tapez 'q' suivi de [Entrée] pour arrêter la playlist.")
                    
                    # Cette boucle attend que la lecture soit terminée ou que l'utilisateur tape 'q'
                    while pygame.mixer.music.get_busy():
                        # Vérifie si l'utilisateur a tapé 'q'
                        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                            line = sys.stdin.readline().strip()
                            if line.lower() == 'q':
                                pygame.mixer.music.stop()
                                print("⏹ Lecture de la playlist arrêtée par l'utilisateur (q).")
                                break
                        time.sleep(0.1)
                # -------------------------------------------------------------------


            # Lecture d’un fichier audio unique
            else:
                if path.lower().endswith(".mp3"):
                    audio = Mp3File(path)
                elif path.lower().endswith(".flac"):
                    audio = FlacFile(path)
                else:
                    print("Format non supporté. Utilisez MP3, FLAC ou XSPF.")
                    sys.exit(1)

                # Lecture d'un seul fichier: wait_for_end=True gère la boucle d'attente/arrêt
                audio.play(wait_for_end=True) 

        except Exception as e:
            print(f"Erreur lors de la lecture : {e}")
    

    # ====================================================================
    # --- Cas 4 : Mise à jour des tags (-u / --update-tags) ---
    # ====================================================================
    elif args.update_tags:
        update_data = {}
        for pair in args.update_tags:
            if "=" not in pair:
                print(f"Argument invalide : {pair}. Format requis : clé=valeur")
                sys.exit(1)
            key, value = pair.split("=", 1)
            update_data[key] = value.strip('"').strip("'")

        if "file" not in update_data:
            print("Vous devez spécifier le fichier à modifier : file=<nom_fichier>")
            sys.exit(1)

        file_path = update_data["file"]

        if file_path.lower().endswith(".mp3"):
            audio = Mp3File(file_path)
        elif file_path.lower().endswith(".flac"):
            audio = FlacFile(file_path)
        else:
            print("Format non supporté. Utilisez MP3 ou FLAC.")
            sys.exit(1)

        # Préparation des tags pour la nouvelle signature save_tags(new_tags: dict)
        if "file" in update_data:
            del update_data["file"] 
            
        audio.save_tags(update_data)

        print(f"✅ Métadonnées mises à jour avec succès pour : {file_path}")


if __name__ == "__main__":
    main()
