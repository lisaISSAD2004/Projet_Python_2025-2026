import argparse
import sys
from Directory import Directory
from Mp3File import Mp3File
from FlacFile import FlacFile

class CLI:
    def display_metadata(self, metadata):
        """Display metadata of a specific audio file."""
        print("=== Metadata ===")
        print(f"Artist : {metadata.artist}")
        print(f"Album  : {metadata.album}")
        print(f"Title  : {metadata.title}")
        print(f"Year   : {metadata.year}\n")

    def display_file_list(self, audio_files):
        """Display a list of found audio files."""
        print("=== Audio files found ===")
        for f in audio_files:
            print(f"- {f.path}")
        print()

    def run(self):
        """Parse command line arguments and execute the requested command."""
        parser = argparse.ArgumentParser(
            prog="python3 cli.py",
            description="🎧 Command Line Interface for managing MP3/FLAC audio files",
            formatter_class=argparse.RawTextHelpFormatter
        )

        parser.add_argument(
            "-f", "--file",
            help="Analyze a specific audio file (MP3 or FLAC)"
        )
        parser.add_argument(
            "-d", "--directory",
            help="Explore a folder and list all audio files inside"
        )
        parser.add_argument(
            "-p", "--play",
            help="Play an audio file (MP3 or FLAC)"
        )
        parser.add_argument(
            "-o", "--output",
            help="Specify an output playlist file (e.g. playlist.xspf)"
        )

        args = parser.parse_args()
        
        # No arguments → show error
        if len(sys.argv) == 1:
            print("❌ Error: no parameters provided.")
            print("Type 'python3 Cli.py -h' or '--help' for usage information.")
            sys.exit(1)

        # --- Case 1: analyze a file ---
        if args.file:
            if args.file.lower().endswith(".mp3"):
                audio = Mp3File(args.file)
            elif args.file.lower().endswith(".flac"):
                audio = FlacFile(args.file)
            else:
                print("❌ Unsupported format. Use an MP3 or FLAC file.")
                sys.exit(1)

            metadata = audio.extract_metadata()
            self.display_metadata(metadata)

        # --- Case 2: explore a directory ---
        elif args.directory:
            directory = Directory(args.directory)
            audio_files = directory.scan_recursively()
            self.display_file_list(audio_files)

            if args.output:
                print(f"🎵 Playlist will be saved as: {args.output}")

        # --- Case 3: play a file ---
        elif args.play:
            if args.play.lower().endswith(".mp3"):
                audio = Mp3File(args.play)
            elif args.play.lower().endswith(".flac"):
                audio = FlacFile(args.play)
            else:
                print("❌ Unsupported format. Use an MP3 or FLAC file.")
                sys.exit(1)

            audio.play()


if __name__ == "__main__":
    cli = CLI()
    cli.run()
