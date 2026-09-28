# Architecture — Omarchy Tablet

Le plugin `surface.tablet` remplace la barre et héberge ses widgets natifs. Il s’appuie sur les registres, tokens et composants installés d’Omarchy ; aucun fichier de `/usr/share/omarchy` n’est modifié.

## Frontend

- `Bar.qml` crée une barre par écran. Un `Instantiator` conserve une instance de chaque `NativeWidget` : la répartition des widgets suit les sections configurées, dans une seule rangée; le changement de mode conserve leurs instances. Les handlers IPC et les panneaux natifs survivent au basculement.
- `NativeHost.qml` fournit le contrat de barre attendu par les widgets Omarchy. Il conserve les dimensions natives dans la barre actuelle (`tablet: false` à l’injection); son mécanisme optionnel d’agrandissement par `Binding` reste disponible, mais n’est pas activé par ce layout.
- `Service.qml` possède le backend et l’état de navigation. Accueil et fenêtres sont mutuellement exclusifs. Il expose les commandes `tablet` et publie uniquement les réponses JSON du backend.
- Une seule `PanelWindow` transitoire héberge `HomeContent.qml` ou `SwitcherOverlay.qml` via un `Loader`. Son contenu est détruit quand elle est fermée. Aucun accueil permanent n’est rendu sous les applications.
- `HomeContent.qml` utilise la bibliothèque d’applications du shell, une grille virtualisée, la recherche et les favoris. Les noms peuvent occuper deux lignes. Un appui long permet de modifier les favoris.
- `SwitcherOverlay.qml` utilise les toplevels Wayland : activation et fermeture ciblent directement leur objet. Les cartes affichent icône et titre, sans capture GPU continue.
- Une poignée inférieure étroite ouvre l’accueil par toucher et les fenêtres par glissement ou appui long. Elle est masquée lorsque le clavier est visible. Le bouton de fermeture de l’application appartient désormais à la barre.

Surfaces mappées du plugin sur la Surface : **1 en bureau ; 2 en tablette avec une application ; 3 avec accueil/fenêtres/réglages ouverts**. Les panneaux Omarchy et Squeekboard ont leurs propres surfaces.

## Backend

`tablet.py` échange des lignes JSON avec Quickshell. `select` attend les commandes et le socket d’événements Hyprland. Les rafales utiles sont regroupées sur 40 ms ; les répétitions de `activewindowv2` pour la même adresse sont ignorées. Hyprland les émet aussi quand seul le titre change.

Une maintenance toutes les deux secondes vérifie la topologie clavier. Les contrôles systemd du clavier sont espacés d’au moins cinq secondes ; les animations sont relues toutes les trente secondes ou lors du rechargement Hyprland. Si le socket est indisponible, le backend reconnecte et conserve une vérification de disposition périodique de secours.

`layout.py` gère la maximisation interne avec un journal écrit avant les modifications. Il conserve l’identité stable, le PID, la classe initiale et les états fullscreen client/interne, sans enregistrer les titres. Les fenêtres flottantes, épinglées, groupées, spéciales et externes sont exclues. Les états explicitement fullscreen sont respectés.

Omarchy peut transmettre la maximisation à une nouvelle fenêtre avant son événement de focus. Le gestionnaire distingue les fenêtres présentes à l’activation et celles nouvellement examinées, pour que cet héritage soit rendu au tiling lors du retour au bureau. Les erreurs de dispatch restent rejouables ; les adresses réutilisées ne récupèrent pas le bail d’un ancien objet.

## Installation et restauration

L’installation publique utilise les commandes `omarchy plugin add/update/disable/remove`. Le parcours alternatif de développement via `install.py` calcule une révision du contenu, prépare les fichiers hors de l’arbre surveillé et publie le répertoire complet par renommage. Le manifeste pointe sur les URLs de cette révision. L’installateur attend d’abord le rechargement automatique ; un rescan n’est demandé qu’en secours.

La sauvegarde initiale de la sélection de barre est conservée. `--restore` remet l’ID et la position antérieurs sans écraser les changements de widgets ou de paramètres indépendants. Le lanceur stable installé résout le script de la révision active.

## Limites assumées

L’accueil est explicite, via son bouton ou la poignée ; il ne remplace plus en permanence le fond du bureau. Les cartes ne sont pas des miniatures en direct. Le pilote graphique, la rotation physique, le service externe `surface-autorotate` et les fonctions des widgets natifs restent du ressort de leurs composants respectifs. Les mesures de temps IPC ne permettent pas de conclure à une fréquence d’affichage donnée.
