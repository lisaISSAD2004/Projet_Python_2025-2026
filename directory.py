from typing import List
import os
import magic 
from metadata import Metadata


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

# --- Test ---
if __name__ == "__main__":
    d = Directory(".")  # Dossier à explorer
    d.dir_exist()
    d.exploration_dir()

    print("\nListe des fichiers audio trouvés :")
    for filename, mime_type in d.files:
        print(f"{filename} -> {mime_type}")
    
    print("\nListe des fichiers audio trouvés :")
    for metadata in d.files:
        metadata.display_tags()
