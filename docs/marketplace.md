# Préparer GitHub et le marketplace

Vérifié le 27 septembre 2026 auprès du [guide de publication](https://plugins.omarchy.org/publish.html) et du [contrat de soumission](https://github.com/omacom/omarchy-plugin-marketplace/blob/main/SUBMISSION.md). Ces règles peuvent évoluer.

## Exigences

Il faut un compte GitHub pour publier un dépôt public, avec un seul plugin, un manifeste à la racine, un README expliquant installation et retrait, une licence et les dépendances. L’identifiant doit être unique; une image `preview.png` à la racine est optionnelle. La publication au catalogue passe ensuite par une soumission et une décision des mainteneurs. Une description et un compte ne suffisent donc pas.

Ce dépôt fournit les fichiers attendus. Le manifeste est validé localement; l’acceptation au marketplace n’est pas acquise.

## Métadonnées proposées

| Champ | Valeur |
| --- | --- |
| Nom | Omarchy Tablet |
| Dépôt suggéré | `omarchy-tablet` |
| Identifiant actuel | `surface.tablet` |
| Version | `0.2.0` — première publication publique proposée en préversion |
| Auteur / licence | Charles Rivest / MIT |
| Catégorie | Desktop |
| Tags | bar, hyprland, launcher |
| Description | Touch-friendly tablet mode for Omarchy: app launcher, single-app layout, on-screen keyboard and dictation shortcuts. Built on Surface Pro 4 with linux-surface. |

Le compte et l’URL GitHub restent à renseigner. Aucun dépôt distant n’est configuré. La lecture du registre public actuel n’a trouvé aucune entrée `surface.tablet`. La validation de soumission doit encore confirmer sa disponibilité, notamment pour les identifiants retirés ou réservés. Un identifiant lié au futur compte est une alternative; tout renommage devra modifier code, chemins, tests et documentation ensemble.

## Premier push

Créer sur GitHub un dépôt public vide nommé `omarchy-tablet`, sans README ni licence générés. Depuis le clone local, relire les changements et lancer les vérifications :

```sh
python3 -m unittest discover -s tests -v
python3 -m py_compile *.py scripts/*.py tests/*.py
omarchy plugin validate .
git diff --check
git status --short
```

Le dépôt contient des modifications antérieures à cette revue, ainsi que des fichiers nouveaux indispensables. Les examiner ensemble avant le commit. Vérifier les captures et les droits de redistribution des éléments visibles.

Après cette relecture, les commandes suivantes préparent le commit et le push. Remplacer `YOUR_GITHUB_NAME` par le compte réel :

```sh
git add .
git diff --cached --stat
git commit -m "Prepare Omarchy Tablet for public testing"
git remote add origin https://github.com/YOUR_GITHUB_NAME/omarchy-tablet.git
git push -u origin main
```

Attendre le résultat GitHub Actions. Sur une installation compatible de test, vérifier ensuite le parcours standard `omarchy plugin add <repository-url> --enable`, mise à jour, désactivation, réactivation et retrait. Le parcours public complet ne peut être validé avant que cette URL existe.

## Soumission au catalogue

Utiliser le [formulaire officiel](https://github.com/omacom/omarchy-plugin-marketplace/issues/new?template=submit-plugin.yml), avec l’URL racine réelle du dépôt et les métadonnées ci-dessus. Confirmer personnellement les déclarations du formulaire concernant le code, les ressources et l’installation. Le [contrat CLI](https://github.com/omacom/omarchy-plugin-marketplace/blob/main/SUBMISSION.md) fournit aussi le format exact si une soumission en ligne de commande est souhaitée.

Notes suggérées pour les mainteneurs :

> Full-bar, service and menu plugin for touch-friendly Omarchy navigation. Developed on Surface Pro 4 with linux-surface, Omarchy 4.0.4, Quickshell 0.3.1 and Hyprland 0.56.2. Uses a Python backend, user systemd/D-Bus for optional Squeekboard, and configurable external dictation. It temporarily yields the known Omarchy fcitx5 service while owning the keyboard and restores prior input settings. Standard Omarchy installation is intended; install.py is an alternative developer workflow. See README and docs/release-readiness.md for dependencies, removal and validation limits.

La validation et le contrôle statique portent sur un commit précis; l’approbation d’un mainteneur reste nécessaire. Ce mécanisme n’est pas une certification de sécurité. Ne pas envoyer de demande avant d’avoir confirmé les essais restants du [bilan](release-readiness.md).

Aucun push, création de dépôt, message à un mainteneur ou soumission n’a été effectué pendant cette préparation.
