# cli_simple.py

import argparse
import sys
from Directory import Directory
from Mp3File import Mp3File
from FlacFile import FlacFile

def main():
    parser = argparse.ArgumentParser(
        description="Gestion de fichiers audio MP3/FLAC"
    )

    parser.add_argument("-d", "--directory", help="Explorer un dossier et lister les fichiers audio")
    parser.add_argument("-f", "--file", help="Afficher les métadonnées d'un fichier audio")
    parser.add_argument("-p", "--play", help="Lire un fichier audio MP3 ou FLAC")
    parser.add_argument("-o", "--output", help="Nom du fichier playlist XSPF à créer (avec -d)")

    args = parser.parse_args()

    if len(sys.argv) == 1:
        print(" Aucun paramètre fourni. Utilisez -h pour l'aide.")
        sys.exit(1)

    # --- Explorer un dossier et éventuellement créer une playlist ---
    if args.directory:
        directory = Directory(args.directory)
        directory.dir_exist()
        directory.exploration_dir()
        print("\n🎵 Fichiers audio trouvés :")
        for meta in directory.files:
            print(f"{meta.file_path} -> {meta.artist} - {meta.title}")
            meta.display_tags()

        if args.output:
            # Méthode generate_xspf_playlist() à implémenter dans Directory
            try:
                directory.generate_xspf_playlist(args.output)
                print(f" Playlist sauvegardée sous : {args.output}")
            except AttributeError:
                print(" La méthode generate_xspf_playlist n'est pas encore implémentée.")

    # --- Afficher les métadonnées d'un fichier ---
    elif args.file:
        from Metadata import Metadata
        meta = Metadata(args.file)
        meta.display_tags()
        print("\nRécupération des paroles...")
        meta.fetch_lyrics()
        meta.display_lyrics()

    # --- Lire un fichier audio ---
    elif args.play:
        path = args.play
        if path.lower().endswith(".mp3"):
            audio = Mp3File(path)
        elif path.lower().endswith(".flac"):
            audio = FlacFile(path)
        else:
            print("Format non supporté. Utilisez MP3 ou FLAC.")
            sys.exit(1)
        print(f"Lecture du fichier : {path}")
        try:
            audio.play()  # à implémenter dans Mp3File / FlacFile si nécessaire
        except AttributeError:
            print("La méthode play() n'est pas encore implémentée.")

if __name__ == "__main__":
    main()
