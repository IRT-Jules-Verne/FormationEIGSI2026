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

## 3. Cloner le dépôt

Placez-vous dans le dossier qui doit contenir le projet, puis lancez :

```powershell
git clone https://github.com/IRT-Jules-Verne/FormationEIGSI2026.git ros2_ws
cd ros2_ws
```

> Conseil : choisissez un chemin court et sans espaces ni accents, par exemple `C:\ros2_ws`.

## 4. Installer l’environnement Pixi

Depuis le dossier `ros2_ws` :

```powershell
pixi install
```

Cette commande télécharge et installe ROS 2 Humble et les outils du cours. Elle peut prendre plusieurs minutes.
L’environnement est créé dans le dossier `.pixi/` du projet. Une fois installé, il fonctionne sans connexion Internet.
