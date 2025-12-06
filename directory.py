"""!
@class Directory
@brief Gère l'exploration de dossiers et la détection de fichiers audio MP3/FLAC.

@details Cette classe permet de parcourir récursivement un répertoire donné et de ses sous-répertoires
pour identifier tous les fichiers audio compatibles (MP3, FLAC). Elle offre également la
fonctionnalité de générer automatiquement une playlist au format XSPF à partir des fichiers trouvés.

@var path
@details Chemin d'accès (str) du dossier racine à explorer.

@var files
@details Liste (`List[Metadata]`) contenant les objets métadonnées de tous les fichiers audio détectés.
"""

from typing import List
import os
import magic 
from Metadata import Metadata


class Directory:
    def __init__( self,path):
         """!
         @brief Constructeur. Initialise un objet Directory.

         @param path [in] Chemin (str) du dossier racine à explorer.
         """
         self.path=path
         self.files: List["Metadata"] = []


    def dir_exist(self):
        """!
        @brief Vérifie l'existence du dossier spécifié.

        @details Cette méthode utilise \c os.path.isdir pour confirmer si le chemin
        d'instance correspond à un dossier valide sur le disque.

        @note Le résultat est affiché dans la console (\c print).
        """

        if os.path.isdir(self.path):
            print("The directory existe.")
        else:
            print("The directory does not exist: ",self.path)
    

    def type_mime(self, full_path: str) -> str:
        """!
        @brief Détermine et retourne le type MIME d’un fichier.

        @param full_path [in] Le chemin complet (str) vers le fichier à analyser.
        @return str Le type MIME du fichier (ex: 'audio/mpeg', 'image/jpeg').
        @retval "" En cas d'échec de la lecture du type MIME.
        """
        try:
            mime = magic.Magic(mime=True)
            return mime.from_file(full_path)
        except Exception as e:
            print(f"Impossible de lire le type MIME pour {full_path}: {e}")
            return ""
    
    def exploration_dir(self, path: str = None):
        """!
        @brief Explore récursivement le dossier et détecte uniquement les fichiers audio MP3/FLAC.

        @details Cette méthode est récursive. Pour chaque fichier audio compatible trouvé
        ('audio/mpeg' ou 'audio/flac'), elle crée un objet \c Metadata et l'ajoute à la liste \c files.

        @param path [in,out] Chemin (str) du dossier à explorer. Par défaut, utilise \c self.path.
        """
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

    # Fichier: Directory.py (Méthode generate_xspf_playlist corrigée)

    def generate_xspf_playlist(self, playlist_name="playlist.xspf"):
        with open(playlist_name, "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<playlist version="1" xmlns="http://xspf.org/ns/0/">\n')
            f.write('  <title>Ma playlist</title>\n')
            f.write('  <trackList>\n')
            
            # 🆕 MODIFICATION CRITIQUE ICI : file contient Mp3File ou FlacFile
            for audio_object in self.files:
                
                # 🆕 Accès aux métadonnées via l'attribut .metadata
                # Ceci fonctionne car Mp3File/FlacFile ont un attribut .metadata (qui est un objet Metadata)
                meta = audio_object.metadata
                
                f.write('    <track>\n')
                # Utiliser meta.title (ou le nom de fichier si le titre est vide)
                f.write(f'      <title>{meta.title or os.path.basename(meta.file_path)}</title>\n')
                
                # Utiliser meta.file_path pour le chemin
                full_path = os.path.abspath(meta.file_path)
                f.write(f'      <location>file://{full_path}</location>\n')
                
                f.write('    </track>\n')
            f.write('  </trackList>\n')
            f.write('</playlist>\n')
        print(f"Playlist XSPF générée ")


# --- Test ---
if __name__ == "__main__":
    d = Directory(".")
    d.dir_exist()
    d.exploration_dir()
    d.generate_xspf_playlist()
    print("\n List of audio files found:")
    for metadata in d.files:
        # Affiche le chemin complet et le titre/artiste
        print(f"{metadata.file_path} -> {metadata.artist} - {metadata.title}")
        metadata.display_tags()
