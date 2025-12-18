"""!
@file Cli.py
@brief Interface en ligne de commande pour la gestion de fichiers audio MP3/FLAC.

@details Ce programme permet d'explorer un dossier, d'afficher ou modifier les métadonnées
d'un fichier audio, de lire un fichier ou une playlist XSPF, et de générer une playlist exportable.

@version v1.0
@date 05/12/2025
"""

import argparse
import sys
import os
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, unquote
import time 
import select 

try:
    import pygame 
except ImportError:
    pygame = None

# --- Imports du modèle ---
try:
    from library.model.Directory import Directory
    from library.model.Mp3File import Mp3File
    from library.model.FlacFile import FlacFile
    from library.model.Metadata import Metadata
except ImportError:
    # Fallback si non installé en package
    try:
        from Directory import Directory
        from Mp3File import Mp3File
        from FlacFile import FlacFile
        from Metadata import Metadata
    except ImportError:
        print("Erreur fatale : Impossible d'importer les classes de modèle.")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        prog="python3 Cli.py",
        description="Gestionnaire de fichiers audio MP3/FLAC.",
        add_help=False,
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument("-h", "--help", action="help", help="Afficher l'aide")
    parser.add_argument("-d", "--directory", help="Explorer un dossier")
    parser.add_argument("-f", "--file", help="Afficher les métadonnées d'un fichier")
    parser.add_argument("-p", "--play", help="Lire un fichier ou une playlist XSPF")
    parser.add_argument("-o", "--output", help="Fichier de sortie pour playlist XSPF")
    parser.add_argument("-u", "--update-tags", nargs=argparse.REMAINDER, help="Modifier les tags (file=path title=v ...)")

    args = parser.parse_args()

    if len(sys.argv) == 1:
        print("Erreur : aucun paramètre fourni. Tapez -h pour l'aide.")
        sys.exit(1)

    # --- CAS 1 : EXPLORATION DOSSIER ---
    if args.directory:
        directory = Directory(args.directory)
        directory.dir_exist()
        directory.exploration_dir()
        print("\n📂 Fichiers trouvés :")
        for i, f in enumerate(directory.files):
            print(f"  {i+1}. {f.path}")
            
        if args.output:
            directory.generate_xspf_playlist(args.output)
            print(f"✅ Playlist générée : {args.output}")

    # --- CAS 2 : AFFICHAGE METADONNEES ---
    elif args.file:
        path = args.file
        if not os.path.exists(path):
            print("Erreur : Fichier introuvable.")
            sys.exit(1)
            
        audio = Mp3File(path) if path.lower().endswith(".mp3") else FlacFile(path)
        meta = audio.metadata
        meta.display_tags()
        print("📥 Récupération des paroles...")
        meta.fetch_lyrics()
        if meta.lyrics:
            print(f"\n📝 PAROLES :\n{meta.lyrics}")

    # --- CAS 3 : LECTURE (FICHIER OU PLAYLIST) ---
    elif args.play:
        path = args.play
        tracks = []

        try:
            if path.lower().endswith(".xspf"):
                tree = ET.parse(path)
                root = tree.getroot()
                ns = {"xspf": "http://xspf.org/ns/0/"}

                for track_xml in root.findall("xspf:trackList/xspf:track", ns):
                    loc = track_xml.find("xspf:location", ns)
                    if loc is not None and loc.text:
                        real_path = unquote(urlparse(loc.text).path)
                        if os.name == 'nt' and real_path.startswith('/'):
                            real_path = real_path.lstrip('/')
                        
                        if os.path.exists(real_path):
                            tracks.append(Mp3File(real_path) if real_path.lower().endswith(".mp3") else FlacFile(real_path))

                if not tracks:
                    print("Aucune piste valide.")
                    sys.exit(1)

                print(f"🎵 Playlist : {len(tracks)} morceaux.")
                for audio_file in tracks:
                    print(f"\n▶ Lecture : {audio_file.path}")
                    print("Tapez 'q' pour SUIVANT, 's' pour STOP TOTAL.")
                    audio_file.play(wait_for_end=False)
                    
                    stop_all = False
                    while pygame.mixer.music.get_busy():
                        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                            cmd = sys.stdin.readline().strip().lower()
                            if cmd == 'q': # SUIVANT
                                pygame.mixer.music.stop()
                                break
                            elif cmd == 's': # STOP TOTAL
                                pygame.mixer.music.stop()
                                stop_all = True
                                break
                        time.sleep(0.1)
                    if stop_all: break
            else:
                # Fichier unique
                audio = Mp3File(path) if path.lower().endswith(".mp3") else FlacFile(path)
                audio.play(wait_for_end=True)

        except Exception as e:
            print(f"Erreur lecture : {e}")

    # --- CAS 4 : MISE À JOUR TAGS ---
    elif args.update_tags:
        data = {}
        for p in args.update_tags:
            if "=" in p:
                k, v = p.split("=", 1)
                data[k] = v.strip('"').strip("'")

        path = data.get("file")
        if not path or not os.path.exists(path):
            print("Erreur : Spécifiez un fichier valide (file=path).")
            sys.exit(1)

        audio = Mp3File(path) if path.lower().endswith(".mp3") else FlacFile(path)
        audio.save_tags(
            title=data.get("title"),
            artist=data.get("artist"),
            album=data.get("album"),
            year=data.get("year"),
            genre=data.get("genre")
        )
        print(f"✅ Tags mis à jour pour {path}")

if __name__ == "__main__":
    main()
