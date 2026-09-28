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

Compte : **varlet99**. Dépôt public : [varlet99/omarchy-tablet](https://github.com/varlet99/omarchy-tablet). La lecture du registre public actuel n’a trouvé aucune entrée `surface.tablet`. La validation de soumission doit encore confirmer sa disponibilité, notamment pour les identifiants retirés ou réservés. L’identifiant existant est conservé pour rester compatible avec les installations locales.

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

Après cette relecture, les commandes suivantes préparent le commit et le push. Compte utilisé : `varlet99`. Ces commandes documentent le premier envoi; ne pas recréer le dépôt distant lors des mises à jour :

```sh
git add .
git diff --cached --stat
git commit -m "Prepare Omarchy Tablet for public testing"
git remote add origin https://github.com/varlet99/omarchy-tablet.git
git push -u origin main
```

Le dépôt est public et les jobs Python 3.11/3.14 de [GitHub Actions](https://github.com/varlet99/omarchy-tablet/actions) ont réussi. Le parcours standard d’installation, commande de mise à jour, désactivation, réactivation, retrait et réinstallation est vérifié : [résultats](marketplace-install-check.json).

## Soumission au catalogue

Utiliser le [formulaire officiel](https://github.com/omacom/omarchy-plugin-marketplace/issues/new?template=submit-plugin.yml), avec l’URL racine réelle du dépôt et les métadonnées ci-dessus. Confirmer personnellement les déclarations du formulaire concernant le code, les ressources et l’installation. Le [contrat CLI](https://github.com/omacom/omarchy-plugin-marketplace/blob/main/SUBMISSION.md) fournit aussi le format exact si une soumission en ligne de commande est souhaitée.

Notes suggérées pour les mainteneurs :

> Full-bar, service and menu plugin for touch-friendly Omarchy navigation. Developed on Surface Pro 4 with linux-surface, Omarchy 4.0.4, Quickshell 0.3.1 and Hyprland 0.56.2. Uses a Python backend, user systemd/D-Bus for optional Squeekboard, and configurable external dictation. It temporarily yields the known Omarchy fcitx5 service while owning the keyboard and restores prior input settings. Standard Omarchy installation is intended; install.py is an alternative developer workflow. See README and docs/release-readiness.md for dependencies, removal and validation limits.

La validation et le contrôle statique portent sur un commit précis; l’approbation d’un mainteneur reste nécessaire. Ce mécanisme n’est pas une certification de sécurité. Les essais physiques restant à confirmer sont déclarés dans le [bilan](release-readiness.md); la version est présentée comme une préversion.

Publication demandée par le propriétaire. La soumission au catalogue fera l’objet d’une issue publique; une demande envoyée ne signifie pas que le plugin est déjà accepté.
