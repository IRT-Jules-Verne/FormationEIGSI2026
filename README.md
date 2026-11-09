# Environnement ROS 2 pour le cours

Ce dépôt contient l’environnement ROS 2 Humble du cours, géré avec [Pixi](https://pixi.sh).
Les instructions ci-dessous concernent **Windows** et doivent être suivies **avant la séance**, avec un accès à Internet.

## 1. Installer Pixi

Dans un terminal **PowerShell** :

```powershell
powershell -ExecutionPolicy ByPass -c "irm -useb https://pixi.sh/install.ps1 | iex"
```

Autre possibilité, avec winget :

```powershell
winget install prefix-dev.pixi
```

**Fermez puis rouvrez le terminal**, puis vérifiez l’installation :

```powershell
pixi --version
```

## 2. Installer Git

Avec winget :

```powershell
winget install --id Git.Git -e --source winget
```

Sinon, téléchargez l’installeur sur <https://git-scm.com/download/win> et gardez les options par défaut.

**Fermez puis rouvrez le terminal**, puis vérifiez l’installation :

```powershell
git --version
```

## 3. Installer Visual Studio Code

Avec winget :

```powershell
winget install -e --id Microsoft.VisualStudioCode
```

Sinon, téléchargez l’installeur sur <https://code.visualstudio.com/download> (bouton **Windows**, « User Installer »). Pendant l’installation, cochez :

- **Ajouter à PATH**, pour pouvoir lancer `code` depuis un terminal ;
- **Ajouter l’action « Ouvrir avec Code »** au menu contextuel des fichiers et des dossiers (conseillé).

**Fermez puis rouvrez le terminal**, puis vérifiez l’installation :

```powershell
code --version
```

Installez ensuite les extensions utiles au cours :

```powershell
code --install-extension ms-python.python
code --install-extension bierner.markdown-mermaid
```

- **Python** : coloration, autocomplétion et navigation dans le code des nœuds ROS 2.
- **Markdown Preview Mermaid Support** : affiche les schémas des énoncés de TP dans l’aperçu Markdown (Ctrl+Maj+V).

## 4. Cloner le dépôt

Placez-vous dans le dossier qui doit contenir le projet, puis lancez :

```powershell
git clone https://github.com/IRT-Jules-Verne/FormationEIGSI2026.git ros2_ws
cd ros2_ws
```

> **Important :** le chemin du dossier ne doit contenir **ni espace ni accent** (par exemple `C:\ros2_ws`). Sinon, `pixi shell` ne trouve pas la commande `ros2`, et certains outils ROS 2 échouent avec `failed to create process`.

## 5. Installer l’environnement Pixi

Depuis le dossier `ros2_ws` :

```powershell
pixi install
```

Cette commande télécharge et installe ROS 2 Humble et les outils du cours. Elle peut prendre plusieurs minutes.
L’environnement est créé dans le dossier `.pixi/` du projet. Une fois installé, il fonctionne sans connexion Internet.

## 6. Ouvrir le projet dans VS Code

Depuis le dossier `ros2_ws` :

```powershell
code .
```

Pour que VS Code reconnaisse les bibliothèques ROS 2 (`rclpy`, messages…), choisissez l’interpréteur Python de Pixi :

1. Ouvrez un fichier `.py`.
2. Lancez `Ctrl+Maj+P` > **Python: Select Interpreter**.
3. Choisissez `.\.pixi\envs\default\python.exe`. S’il n’apparaît pas, utilisez **Enter interpreter path…** et indiquez ce chemin.

Le terminal intégré (`Ctrl+ù`) est un PowerShell. Lancez-y `pixi shell` comme dans un terminal normal.
