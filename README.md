# Pronostic quinté du jour

Analyse de performance du Quinté+ du jour (Equidia), générée automatiquement.
La page d'accueil redirige vers le pronostic le plus récent.

Les cotes ne sont pas utilisées. Jeu responsable, interdit aux mineurs.

## Résultat, rapports et analyse

- `src/quinte.py` relève, une heure après le départ, l'arrivée officielle et les rapports PMU sur turfin.fr (une page
  par course, robots.txt respecté). Les données sont dans `data/quinte/jours.json`.
- `src/page.py` ajoute à la page du jour le résultat, les rapports et la comparaison avec ce que la page proposait
  (ordre probable, box de tiercé, quarté et quinté, simple placé). La zone 9 indique le rang de chaque cheval à l'arrivée.
- `.github/workflows/quinte.yml` lance ces deux étapes toutes les dix minutes, de 9 h à 23 h 50 (heure de Paris), et
  n'envoie que les changements.

Les pages du jour (`AAAA-MM-JJ.html`) sont produites séparément : `src/page.py` ne fait que compléter celles qui existent.
