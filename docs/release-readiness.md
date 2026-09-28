# Bilan avant publication — 27 septembre 2026

## Avis

**Le dépôt est préparé pour une première publication GitHub en préversion.** La structure attendue par le marketplace est présente. Le dépôt public est [varlet99/omarchy-tablet](https://github.com/varlet99/omarchy-tablet). Le parcours standard d’installation a été vérifié et la CI Python 3.11/3.14 a réussi. La version est soumise comme préversion, avec les essais physiques encore non réalisés explicitement déclarés.

Le code est organisé de façon cohérente : frontend QML, backend Python, gestion des fenêtres séparée et tests de restauration ciblés. Les commandes de dictée utilisent une liste d’arguments, les adresses de fenêtres sont validées et un journal précède les modifications de disposition. Cela constitue une bonne base maintenable. Cette revue ne prouve pas l’absence de tous les défauts ni une compatibilité universelle.

## Corrections de cette revue

| Problème observé dans le code | Correction / preuve |
| --- | --- |
| `install.py` pouvait remplacer l’installateur et le manifeste d’un checkout géré par le marketplace. | Refus avant écriture si la destination contient `.git`; test de non-modification du checkout et de la configuration. |
| Une sauvegarde créée alors que la barre tablette était déjà sélectionnée pouvait restaurer la tablette vers elle-même. | Repli sur la barre Omarchy d’origine quand la sauvegarde manque ou pointe sur `surface.tablet`; tests sur les deux situations. |
| Un payload incomplet ou un manifeste JSON illisible pouvait créer une sauvegarde prématurée. | Lecture du payload et du manifeste avant mutation; tests d’échec sans installation ni sauvegarde. |
| La restauration ne vérifiait pas la version de configuration. | Refus d’une version inconnue sans écriture; test dédié. |
| Des fenêtres voisines flottantes, épinglées ou groupées pouvaient entrer dans le journal de restauration alors qu’elles étaient annoncées comme exclues. | Même filtre d’éligibilité pour les voisines; test vérifiant l’absence de journalisation et de dispatch vers elles. |
| Les chemins des scripts QML conservaient l’encodage URL, problématique pour les espaces ou accents. | Décodage de l’URL locale avant lancement Python. Analyse QML effectuée; démarrage dans un répertoire avec espaces non testé en session. |
| Le chemin du fond ignorait `XDG_STATE_HOME`. | Respect du répertoire d’état configuré. |
| Documentation contradictoire : ancienne barre sur deux rangées, bureau annoncé identique au stock, activation du clavier et consignes de retrait incomplètes. | README restructuré, présentation française, procédures séparées, dépendances et limites explicites; anciennes preuves identifiées comme historiques. |

La CI compile désormais tous les fichiers Python et prévoit les tests sur Python 3.11 et 3.14. Les deux jobs ont réussi sur GitHub : [exécution initiale](https://github.com/varlet99/omarchy-tablet/actions/runs/36375565630). La licence MIT, l’auteur, l’identifiant et la version 0.2.0 sont conservés. Les modifications locales préexistantes n’ont pas été annulées.

## Vérifications effectuées

| Contrôle | Résultat et portée |
| --- | --- |
| `python3 -m unittest discover -s tests -v` | **52 tests passent** sous Python 3.14.7; état initial : 45 tests. Installation testée dans des répertoires temporaires, sans écriture dans la configuration réelle. |
| `python3 -m py_compile *.py scripts/*.py tests/*.py` | Réussi. |
| `omarchy plugin validate .` | Réussi avec le validateur installé Omarchy 4.0.4. |
| `git diff --check` | Réussi. |
| `python3 scripts/lint_qml.py` | Code de sortie 0 avec les imports Omarchy résolus. Des avertissements subsistent : types dynamiques `Style`/`Color`, accès non qualifiés, métadonnées Quickshell `PanelWindow` et `QProcess::ExitStatus`. Ce n’est pas un résultat « zéro avertissement ». |
| Revue des fichiers texte | Pas de secret manifeste repéré par recherche ciblée; pas d’audit exhaustif de secrets ou de dépendances. |
| Navigation réelle de la révision candidate installée | Tablet → Home → Apps → Settings → Windows → fermeture → Desktop : état IPC attendu. Le passage Desktop libère le service clavier; aucun message d’erreur du plugin ni erreur de configuration Hyprland observé. |
| Restauration de la session | Mode initial `desktop` rétabli. Pas de dictée lancée ni de test physique du clavier. |
| Aperçu | `preview.png` et `docs/screenshots/release-settings.png` capturés et examinés visuellement. |

Le parcours graphique a été rejoué sur la révision candidate `202f10f19e2ea410`, installée depuis le dépôt après les corrections. Les 52 tests passent également sur cette révision; le mode Desktop initial a été rétabli après le parcours. Voir [preuve du parcours](release-smoke.json). Les anciens rapports du dépôt ne sont pas présentés comme de nouveaux essais.

Machine inspectée : Surface Pro 4, noyau `6.19.8-arch1-3-surface`, Omarchy `4.0.4-1`, Hyprland `0.56.2-2`, Quickshell `0.3.1-1`, Squeekboard `1.43.1-5`, Python `3.14.7-1`, PyGObject `3.56.3-1`.

## À faire avant la soumission

- [x] Dépôt public créé sur `varlet99/omarchy-tablet`; CI réussie sur Python 3.11 et 3.14.
- [x] Vérifier le registre public actuel : aucune entrée `surface.tablet` trouvée. La validation de soumission confirmera la disponibilité, y compris les éventuels identifiants réservés ou retirés.
- [x] Installation publique, commande de mise à jour sans changement, désactivation, réactivation, retrait et réinstallation vérifiés sur le commit `7e542ac2c87917d357d4f277a8c083dff37bbb3e`; voir [preuve](marketplace-install-check.json). L’ancienne installation locale a été sauvegardée automatiquement.
- [ ] Compléter les essais de redémarrage du shell et de récupération après panne sur une session dédiée.
- [ ] En mode Automatic, détacher puis rattacher réellement le Type Cover; vérifier Tablet → Desktop et le maintien des choix manuels.
- [ ] Au doigt, essayer la grille, les favoris, la poignée, le défilement des widgets et les réglages en portrait et paysage.
- [ ] Essayer le clavier dans les applications utilisées : saisie, masquage, passage entre champs, terminal, changement d’apparence et retour au clavier physique.
- [ ] Effectuer une dictée complète avec Murmure : démarrage, arrêt, insertion dans le champ attendu et clavier masqué. Aucun enregistrement vocal n’a été fait pendant cette revue.
- [ ] Tester veille/reprise et écran externe si ces usages font partie des promesses de la première version.
- [ ] Confirmer les droits sur le code et les ressources des captures avant diffusion publique et avant de cocher le formulaire du marketplace.

## Limites à conserver dans la présentation

Hyprland est utilisé dans les deux modes. La barre reste celle du plugin en mode Desktop; la désactivation rétablit la barre native. Le support matériel, la rotation et les fonctionnalités de reconnaissance vocale viennent de composants externes. Les autres modèles de tablettes ne sont pas certifiés compatibles.

`NativeHost.qml` reproduit une partie du contrat de barre du shell : une évolution des API Omarchy peut demander une adaptation. Les avertissements QML et cette dépendance au shell méritent un suivi, mais ne démontrent pas à eux seuls une panne de la session actuelle. Les scripts historiques de tests graphiques contiennent des hypothèses spécifiques à la Surface et doivent être relus avant réutilisation.

Les prochaines étapes publiques et les sources du marketplace sont dans [marketplace.md](marketplace.md). La publication GitHub et la soumission sont suivies dans [marketplace.md](marketplace.md).
