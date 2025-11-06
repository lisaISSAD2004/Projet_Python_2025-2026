# cli_simple.py

import argparse
import sys
from Directory import Directory
from Mp3File import Mp3File
from FlacFile import FlacFile


def main():
    parser = argparse.ArgumentParser(
        prog="python3 Cli.py",
        description=(
            "🎧 Command Line Interface for managing MP3/FLAC audio files.\n\n"
            "You can list, play, inspect, or edit metadata tags of your songs."
        ),
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        "-d", "--directory",
        help="Explore a folder and list all audio files inside (MP3/FLAC)."
    )

    parser.add_argument(
        "-f", "--file",
        help="Display metadata information of a specific audio file."
    )

    parser.add_argument(
        "-p", "--play",
        help="Play an audio file (MP3 or FLAC)."
    )

    parser.add_argument(
        "-o", "--output",
        help="Specify an output playlist file (e.g. playlist.xspf)"

    )

    parser.add_argument(
        "-u", "--update-tags",
        nargs=argparse.REMAINDER,
        help=(
            "Update song metadata (title, artist, album, year).\n"
    
        )
    )

    args = parser.parse_args()

    # --- No arguments ---
    if len(sys.argv) == 1:
        print("❌ Error: no parameters provided.")
        print("Type 'python3 Cli.py -h' or '--help' for usage information.")
        sys.exit(1)

    # --- Case 1: Directory exploration ---
    if args.directory:
        directory = Directory(args.directory)
        directory.dir_exist()
        directory.exploration_dir()
        print("\n🎵 Audio files found:")
        for meta in directory.files:
            print(f"{meta.file_path} -> {meta.artist} - {meta.title}")
            meta.display_tags()

        if args.output:
            try:
                directory.generate_xspf_playlist(args.output)
                print(f"✅ Playlist saved as: {args.output}")
            except AttributeError:
                print(" The method generate_xspf_playlist() is not implemented yet.")

    # --- Case 2: Display metadata ---
    elif args.file:
        from Metadata import Metadata
        meta = Metadata(args.file)
        meta.display_tags()
        print("\n🎤 Fetching lyrics...")
        meta.fetch_lyrics()
        meta.display_lyrics()

    # --- Case 3: Play a file ---
    elif args.play:
        path = args.play
        if path.lower().endswith(".mp3"):
            audio = Mp3File(path)
        elif path.lower().endswith(".flac"):
            audio = FlacFile(path)
        else:
            print("❌ Unsupported format. Use MP3 or FLAC.")
            sys.exit(1)

        print(f"Playing file: {path}")
        try:
            audio.play()
        except AttributeError:
            print("⚠️ The play() method is not yet implemented.")

    # --- Case 4: Update tags ---
    elif args.update_tags:
        update_data = {}
        for pair in args.update_tags:
            if "=" not in pair:
                print(f"❌ Invalid argument: {pair}. Must be in key=value format.")
                sys.exit(1)
            key, value = pair.split("=", 1)
            update_data[key] = value.strip('"').strip("'")

        if "file" not in update_data:
            print("❌ You must specify the file to update: file=<filename>")
            sys.exit(1)

        file_path = update_data["file"]

        if file_path.lower().endswith(".mp3"):
            audio = Mp3File(file_path)
        elif file_path.lower().endswith(".flac"):
            audio = FlacFile(file_path)
        else:
            print("❌ Unsupported format. Use MP3 or FLAC.")
            sys.exit(1)
       
        audio.save_tags(
        title=update_data.get("title"),
        artist=update_data.get("artist"),
        album=update_data.get("album"),
        year=update_data.get("year")
    )

        

        print(f"✅ Tags successfully updated for: {file_path}")


if __name__ == "__main__":
    main()
