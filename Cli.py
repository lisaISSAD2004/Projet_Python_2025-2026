
import argparse
import sys
from Directory import Directory
from Mp3File import Mp3File
from FlacFile import FlacFile


def main():
    parser = argparse.ArgumentParser(
        prog="python3 Cli.py",
        description=(
            "Interface en ligne de commande pour gérer les fichiers audio MP3/FLAC.\n\n"
            "Vous pouvez lister, lire, inspecter ou modifier les métadonnées de vos chansons."
        ),
        add_help=False,
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        "-h", "--help",
        action="help",
        help="afficher l'aide et quitter"
    )
    parser.add_argument(
        "-d", "--directory",
        help="Explorer un dossier et lister tous les fichiers audio à l’intérieur (MP3/FLAC)."
    )

    parser.add_argument(
        "-f", "--file",
        help="Afficher les informations de métadonnées d’un fichier audio."
    )

    parser.add_argument(
        "-p", "--play",
        help="Lire un fichier audio (MP3 ou FLAC)."
    )

    parser.add_argument(
        "-o", "--output",
        help="Spécifier un fichier de sortie pour la playlist (ex: playlist.xspf)"
    )

    parser.add_argument(
        "-u", "--update-tags",
        nargs=argparse.REMAINDER,
        help=(
            "Mettre à jour les métadonnées de la chanson (title, artist, album, year).\n"
        )
    )

    args = parser.parse_args()

    # --- Aucun argument ---
    if len(sys.argv) == 1:
        print("❌ Erreur : aucun paramètre fourni.")
        print("Tapez 'python3 Cli.py -h' ou '--help' pour afficher l’aide.")
        sys.exit(1)

    # --- Cas 1 : Exploration d’un dossier ---
    if args.directory:
        directory = Directory(args.directory)
        directory.dir_exist()
        directory.exploration_dir()

        if args.output:
            try:
                directory.generate_xspf_playlist(args.output)
                print(f"🎵 Playlist enregistrée sous : {args.output}")
            except AttributeError:
                print("⚠️ La méthode generate_xspf_playlist() n’est pas encore implémentée.")

    # --- Cas 2 : Afficher les métadonnées ---
    elif args.file:
        from Metadata import Metadata
        meta = Metadata(args.file)
        meta.display_tags()
        print("\n📥 Récupération des paroles...")
        meta.fetch_lyrics()
        
        # 🎯 CORRECTION : Affichage simplifié des paroles
        try:
            if meta.lyrics:
                meta.display_lyrics()
            else:
                # Si fetch_lyrics a retourné False, n'a pas trouvé de paroles, ou erreur HTTP/réseau
                print("✗ Les paroles n'ont pas été chargées.")
        
        except AttributeError:
            # Gérer le cas où display_lyrics() est manquant (comme convenu)
            print("✗ Les paroles n'ont pas été chargées.")
            
        # --- Cas 3 : Lire un fichier ou playlist ---
    elif args.play:
        path = args.play

        try:
            # Lecture d'une playlist XSPF
            if path.lower().endswith(".xspf"):
                import xml.etree.ElementTree as ET
                print(f"📂 Ouverture de la playlist : {path}")

                tree = ET.parse(path)
                root = tree.getroot()
                ns = {"xspf": "http://xspf.org/ns/0/"}

                tracks = []
                for track in root.findall("xspf:trackList/xspf:track", ns):
                    location = track.find("xspf:location", ns)
                    if location is not None:
                        real_path = location.text.replace("file://", "")
                        tracks.append(real_path)

                if not tracks:
                    print("❌ Aucune piste trouvée dans la playlist.")
                    sys.exit(1)

                print(f"🎵 {len(tracks)} morceau(x) trouvé(s). Lecture en cours...\n")

                for audio_path in tracks:
                    if audio_path.lower().endswith(".mp3"):
                        audio = Mp3File(audio_path)
                    elif audio_path.lower().endswith(".flac"):
                        audio = FlacFile(audio_path)
                    else:
                        print(f"⚠️ Format non supporté dans la playlist : {audio_path}")
                        continue
                    audio.play()

            # Lecture d’un fichier audio unique
            else:
                if path.lower().endswith(".mp3"):
                    audio = Mp3File(path)
                elif path.lower().endswith(".flac"):
                    audio = FlacFile(path)
                else:
                    print("❌ Format non supporté. Utilisez MP3, FLAC ou XSPF.")
                    sys.exit(1)

                print(f"🎧 Lecture du fichier : {path}")
                audio.play()

        except AttributeError:
            print("⚠️ La méthode play() n’est pas encore implémentée.")
        except Exception as e:
            print(f"❌ Erreur lors de la lecture : {e}")
    

    # --- Cas 4 : Mise à jour des tags ---
    elif args.update_tags:
        update_data = {}
        for pair in args.update_tags:
            if "=" not in pair:
                print(f"❌ Argument invalide : {pair}. Format requis : clé=valeur")
                sys.exit(1)
            key, value = pair.split("=", 1)
            update_data[key] = value.strip('"').strip("'")

        if "file" not in update_data:
            print("❌ Vous devez spécifier le fichier à modifier : file=<nom_fichier>")
            sys.exit(1)

        file_path = update_data["file"]

        if file_path.lower().endswith(".mp3"):
            audio = Mp3File(file_path)
        elif file_path.lower().endswith(".flac"):
            audio = FlacFile(file_path)
        else:
            print("❌ Format non supporté. Utilisez MP3 ou FLAC.")
            sys.exit(1)

        audio.save_tags(
            title=update_data.get("title"),
            artist=update_data.get("artist"),
            album=update_data.get("album"),
            year=update_data.get("year")
        )

        print(f"✅ Métadonnées mises à jour avec succès pour : {file_path}")


if __name__ == "__main__":
    main()
