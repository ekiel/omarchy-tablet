# Claviers tactiles et apparences

Recherche du 27 septembre 2026. Les alternatives ci-dessous n'ont pas été installées ni validées sur cette Surface.

| Projet | Personnalisation documentée | Choix pour ce projet |
| --- | --- | --- |
| [Squeekboard](https://gitlab.gnome.org/World/Phosh/squeekboard) | Dispositions YAML et rendu CSS (`sq_view`, `sq_button`). | Conservé : saisie Wayland et disposition canadienne déjà intégrées. Trois nouveaux styles originaux suivent les couleurs Omarchy. |
| [Sysboard](https://github.com/System64fumo/sysboard) | Thème GTK4, CSS personnalisé et dispositions full/mobile/mobile_numbers. | Alternative intéressante pour un clavier plus proche d'un clavier PC. Compatibilité et langue à tester avant remplacement. |
| [Maliit](https://github.com/maliit/keyboard) | Clavier libre pour Linux, Wayland et X11. | Autre moteur possible ; intégration Hyprland et remplacement de l'interface de contrôle à étudier. |
| [wvkbd](https://github.com/jjsullivan5196/wvkbd) | Clavier pour wlroots, configuration et dispositions dans le projet. | Piste légère ; pas intégrée dans cette modification esthétique. |

## Trois styles disponibles

- **Omarchy** : touches discrètes, petits arrondis, contours fins et touche Entrée accentuée.
- **Rounded** : arrondis plus généreux, même palette.
- **High contrast** : contours épais et caractères noirs ou blancs choisis selon la luminosité du fond. La couleur d'accent reste celle du thème.

Les trois styles suivent le thème actif. Les choisir dans Settings → Keyboard appearance. Masquer puis rouvrir le clavier pour appliquer le changement. Le style Omarchy est celui installé par défaut. La langue et la disposition des touches restent indépendantes du style.

## Intégration

La [source du chargeur de styles Squeekboard](https://world.pages.gitlab.gnome.org/Phosh/squeekboard/doc/src/rs/style.rs.html) décrit la sélection de ressources CSS. Les [overlays de ressources GLib](https://docs.gtk.org/gio/struct.Resource.html#overlays) permettent de remplacer une ressource uniquement dans le processus lancé. Le plugin utilise cette capacité, sans recompiler ni modifier Squeekboard ou le GTK des autres applications. Les sélecteurs ont été vérifiés contre les styles amont et le rendu installé.

Ce mécanisme dépend des chemins de ressources et des sélecteurs de Squeekboard : une mise à jour amont peut demander une adaptation. L'apparence ne change pas les limites de saisie des applications qui ne prennent pas en charge Wayland text-input.
