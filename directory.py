from typing import List
import os
import magic 
from Metadata import Metadata


class Directory:
    def __init__( self,path):
         self.path=path
         self.files: List["Metadata"] = []


    def dir_exist(self):
        """
        Vérifie si le dossier existe.
        """
        if os.path.isdir(self.path):
            print("Le dossier existe.")
        else:
            print("Le dossier n'existe pas.",self.path)
    

    def type_mime(self, full_path: str) -> str:
        """Retourne le type MIME d’un fichier"""
        try:
            mime = magic.Magic(mime=True)
            return mime.from_file(full_path)
        except Exception as e:
            print(f"Impossible de lire le type MIME pour {full_path}: {e}")
            return ""
    
    def exploration_dir(self, path: str = None):
        """Parcourt le dossier et tous ses sous-dossiers, ne garde que MP3 et FLAC"""
        if path is None:
            path = self.path

        try:
            for f in os.listdir(path):
                full_path = os.path.join(path, f)
                if os.path.isdir(full_path):
                    # Appel récursif pour les sous-dossiers
                    self.exploration_dir(full_path)
                elif os.path.isfile(full_path):
                    file_type = self.type_mime(full_path)
                    if file_type in ('audio/mpeg', 'audio/flac'):
                        # Crée un objet Metadata pour chaque fichier audio
                        metadata = Metadata(full_path)
                        self.files.append(metadata)
                        print(f"Audio trouvé : {full_path} -> {file_type}")
        except Exception as e:
            print(f"Erreur lors de l'exploration de {path}: {e}")

    def generate_xspf_playlist(self, playlist_name="playlist.xspf"):
        with open(playlist_name, "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<playlist version="1" xmlns="http://xspf.org/ns/0/">\n')
            f.write('  <title>Ma playlist</title>\n')
            f.write('  <trackList>\n')
            for file in self.files:
                f.write('    <track>\n')
                f.write(f'      <title>{file}</title>\n')
                full_path = os.path.abspath(file.file_path)
                f.write(f'      <location>file://{full_path}</location>\n')
                
                f.write('    </track>\n')
            f.write('  </trackList>\n')
            f.write('</playlist>\n')
        print(f"Playlist XSPF générée : {playlist_name}")


# --- Test ---
if __name__ == "__main__":
    d = Directory(".")
    d.dir_exist()
    d.exploration_dir()
    d.generate_xspf_playlist()
    print("\nListe des fichiers audio trouvés :")
    for metadata in d.files:
        # Affiche le chemin complet et le titre/artiste
        print(f"{metadata.file_path} -> {metadata.artist} - {metadata.title}")
        metadata.display_tags()

        


   
