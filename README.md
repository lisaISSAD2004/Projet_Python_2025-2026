# 🎵 Gestionnaire Musical MP3/FLAC

## 📋 Description du Projet

Application complète de gestion de fichiers musicaux MP3 et FLAC avec extraction de métadonnées, lecture audio, gestion de playlists XSPF et recherche d'informations via API. Ce projet universitaire (L3 Informatique - CY Cergy Paris Université) permet d'explorer des arborescences de fichiers, d'afficher et modifier les tags ID3/Vorbis, de télécharger des covers d'albums et de récupérer les paroles via des services en ligne.

## 👥 Équipe - Groupe 

- 👩‍💻 **ACHAB Ouardia**  
  📧 Email : ouardia.achab@etu.cyu.fr
    
- 👩‍💻 **ISSAD Lisa**  
  📧 Email : lisa.issad@etu.cyu.fr
    
- 👩‍💻 **HACHANI Omar**  
  📧 Email : omar.hachani@etu.cyu.fr

**Responsable de formation :** Jean-luc BOURDON
**Période :** octobre 2025 - Décembre 2025

## 🎯 Objectifs

- ✅ Extraire et afficher les métadonnées des fichiers MP3 (ID3) et FLAC (Vorbis Comment)
- ✅ Explorer récursivement des dossiers pour lister tous les fichiers audio
- ✅ Créer et sauvegarder des playlists au format XSPF
- ✅ Modifier et sauvegarder les tags audio (titre, artiste, album, année, genre)
- ✅ Lire des fichiers audio individuels ou des playlists complètes
- ✅ Télécharger des covers d'albums depuis iTunes et MusicBrainz
- ✅ Récupérer les paroles via API (Lyrics.ovh)
- ✅ Rechercher des informations complètes d'albums via MusicBrainz API

## ✨ Fonctionnalités Principales

### Mode Console (CLI)
- **Exploration de dossiers** : Analyse récursive d'une arborescence avec filtre MP3/FLAC
- **Affichage des métadonnées** : Extraction et affichage complet des tags ID3/Vorbis
- **Lecture audio** : Lecture de fichiers individuels ou de playlists XSPF
- **Modification des tags** : Mise à jour des métadonnées via ligne de commande
- **Génération de playlists** : Création automatique de fichiers XSPF

### Mode Graphique (GUI)
- **Explorateur de fichiers** : Liste interactive avec recherche/filtrage en temps réel
- **Éditeur de métadonnées** : Modification visuelle des tags avec sauvegarde instantanée
- **Gestion de covers** : Affichage, téléchargement et sauvegarde des images d'albums
- **Playlist interactive** : Ajout/suppression par drag & drop, lecture séquentielle
- **Recherche API** : Récupération automatique des paroles et informations d'albums
- **Lecture audio intégrée** : Player embarqué avec contrôles stop/play

## 🏗️ Architecture Technique

### 1. **Bibliothèques Python Utilisées**
```
tkinter              # Widgets GUI de base
Pillow (PIL)         # Manipulation d'images (covers)
mutagen              # Lecture/écriture des tags MP3/FLAC
pygame               # Lecture audio
requests             # Appels API (iTunes, Lyrics.ovh)
xml.etree.ElementTree # Parsing/génération XSPF
argparse             # Gestion des arguments CLI
threading            # Gestion de la lecture audio en arrière-plan
```

### 2. **Structure du Projet**
```
ACHAB_ISSAD_HACHANI/
│
├── src/
│   ├── library/
│   │   ├── Directory.py      # Exploration de dossiers
│   │   ├── Mp3File.py        # Gestion des fichiers MP3
│   │   ├── FlacFile.py       # Gestion des fichiers FLAC
│   │   └── Metadata.py       # Extraction de métadonnées
│   │
│   ├── cli/
│   │   └── Cli.py            # Interface ligne de commande
│   │
│   └── gui/
│       └── Gui.py            # Interface graphique
│
├── doc/
│   ├── diaporama/            # Présentation de soutenance
│   ├── documentation/        # Documentation technique (Doxygen/Pydoc)
│   └── rapport/              # Rapport de projet (ODT + PDF)
│
└── README.md
```

### 3. **APIs Externes Intégrées**
- ** iTunes Search API ** : Recherche de covers d'albums haute résolution (600x600)
- ** Lyrics.ovh API **: Téléchargement automatique des paroles de chansons

## 🚀 Installation et Configuration

### 1. **Prérequis**
```bash
# Python 3.8+ requis
python3 --version

# Installation des dépendances
pip install pillow mutagen pygame requests
```

### 2. **Lancement du Mode Console (CLI)**
```bash
# Afficher l'aide
python3 src/cli/Cli.py -h

# Explorer un dossier et lister les fichiers
python3 src/cli/Cli.py -d /chemin/vers/musique/

# Afficher les métadonnées d'un fichier
python3 src/cli/Cli.py -f chanson.mp3

# Générer une playlist XSPF
python3 src/cli/Cli.py -d ./music/ -o ma_playlist.xspf

# Lire un fichier audio
python3 src/cli/Cli.py -p chanson.mp3

# Lire une playlist XSPF
python3 src/cli/Cli.py -p ma_playlist.xspf

# Modifier les tags d'un fichier
python3 src/cli/Cli.py -u file=chanson.mp3 title="Nouveau Titre" artist="Artiste" album="Album" year="2025"
```

### 3. **Lancement du Mode Graphique (GUI)**

```bash
python3 src/gui/Gui.py
```

**Fonctionnalités GUI :**
1. **Ouvrir Dossier** : Explore une arborescence et liste tous les fichiers MP3/FLAC
2. **Sélectionner un fichier** : Clic sur un fichier pour afficher ses métadonnées
3. **Modifier les tags** : Éditer les champs et cliquer sur "💾 Sauvegarder"
4. **Télécharger cover** : Recherche automatique sur Internet avec validation visuelle
5. **Ajouter à playlist** : Bouton "+" pour construire une liste de lecture
6. **Lire la playlist** : Lecture séquentielle de tous les morceaux
7. **Recherche API** : Onglet dédié pour récupérer paroles et infos d'albums
8. **Ouvrir Playlist** : Importer un fichier XSPF existant

## 📖 Exemples d'Utilisation

### Cas d'usage 1 : Explorer et créer une playlist
```bash
# 1. Explorer un dossier de musique
python3 src/cli/Cli.py -d ~/Musique/

# 2. Générer une playlist de tous les fichiers trouvés
python3 src/cli/Cli.py -d ~/Musique/ -o toute_ma_musique.xspf

# 3. Lire la playlist générée
python3 src/cli/Cli.py -p toute_ma_musique.xspf
```

### Cas d'usage 2 : Corriger les métadonnées
```bash
# Afficher les tags actuels
python3 src/cli/Cli.py -f chanson.mp3

# Corriger les informations
python3 src/cli/Cli.py -u file=chanson.mp3 title="Titre Correct" artist="Artiste Correct" year="2024"

# Vérifier les modifications
python3 src/cli/Cli.py -f chanson.mp3
```

### Cas d'usage 3 : Télécharger des covers (GUI)
1. Lancer l'interface graphique
2. Ouvrir un dossier de musique
3. Sélectionner un fichier sans cover
4. Cliquer sur "Télécharger depuis Internet"
5. Valider ou refuser la cover proposée
6. La cover est sauvegardée dans le fichier ET dans le dossier (cover.jpg)

## 🔐 Validation et Conformité

### 1. **Format XSPF**
Les playlists générées sont conformes au standard XSPF et validables sur :
```
https://validator.xspf.org/
```

### 2. **Formats Audio Supportés**
- **MP3** : Tags ID3v2.3/ID3v2.4 (lecture/écriture)
- **FLAC** : Vorbis Comments (lecture/écriture)

### 3. **Vérification MIME Type**
Le programme vérifie l'extension ET le type MIME de chaque fichier pour garantir qu'il s'agit bien d'un fichier audio valide.

## 📝 Documentation

### Génération de la documentation
```bash
# Documentation Doxygen 
doxygen Doxyfile
```

## 🎓 Évaluation

### Livrables
- ✅ **Diagramme de Gantt** (PNG) - Semaine 42
- ✅ **Point d'avancement 1** - 7 novembre (Semaine 45)
- ✅ **Point d'avancement 2** - 28 novembre (Semaine 48)
- ✅ **Vidéo de démonstration** (max 5 min) - 11 décembre 22h00
- ✅ **Rapport de projet** (5-10 pages ODT + PDF) - 12 décembre 22h00
- ✅ **Code source complet** + Documentation - 12 décembre 22h00
- ✅ **Soutenance** (15 min : 8 min présentation + 7 min questions) - 19 décembre

### Notation
- Diagramme de Gantt : 1 point
- Points d'avancement : 3 points (2 + 1)
- Vidéo de démonstration : 5 points
- Soutenance : 4 points
- Livrables finaux : 7 points

## 🐛 Résolution de Problèmes

### Erreur : "Module customtkinter not found"
```bash
pip install customtkinter
```

### Erreur : "pygame.error: No available audio device"
Vérifiez que votre système a un périphérique audio fonctionnel et que les pilotes sont à jour.

### Les covers ne se téléchargent pas
- Vérifiez votre connexion Internet
- Assurez-vous que les champs "Artiste" et "Album" sont correctement renseignés
- Certains albums peuvent ne pas avoir de cover disponible

### La playlist XSPF n'est pas valide
Utilisez le validateur en ligne : https://validator.xspf.org/
Les chemins de fichiers doivent être au format `file:///chemin/absolu/vers/fichier.mp3`

## 📧 Contact et Support

Pour toute question concernant le projet :
- **Ouardia ACHAB** : ouardia.achab@etu.cyu.fr
- **Lisa ISSAD** : lisa.issad@etu.cyu.fr
- **Omar HACHANI** : omar.hachani@etu.cyu.fr

**Responsable pédagogique** : Jean-luc BOURDON  
---

*Projet réalisé dans le cadre du module Python - L3 Informatique - CY Cergy Paris Université - 2025/2026*
