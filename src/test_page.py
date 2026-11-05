"""Contrôles de l’insertion du résultat dans une page du Quinté+ : constats, zone 9, relance sans changement."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import page  # noqa: E402

PAGE = """<!doctype html><html><body><main>
<section id="zone-1" class="card"><div class="ordre"><span class='pastille r1'>6</span><span class='pastille r2'>4</span><span class='pastille '>5</span><span class='pastille '>9</span><span class='pastille '>12</span></div><p class="note">Le favori</p></section>
<section id="zone-3" class="card">Simple placé n°6 Probabilité estimée : 42.4 %. Tiercé Box 5 Chevaux : 6, 4, 5, 9, 12 10 combinaisons 7.1 % de chances Quarté Box 5 Chevaux : 6, 4, 5, 9, 12 5 combinaisons 1.8 % de chances Quinté Box 6 Chevaux : 6, 4, 5, 9, 12, 17 6 combinaisons 1.3 % de chances</section>
<section id="zone-6" class="card"><table><tr><td>1</td><td>6</td><td>HUMANITY PELLINI</td><td>D. BEKAERT</td><td>0.933</td><td>15.7 %</td><td>42.4 %</td><td>63.1 %</td></tr>
<tr><td>2</td><td>4</td><td>JOKER DES CHALIERS</td><td>G. GELORMINI</td><td>0.795</td><td>9.0 %</td><td>26.6 %</td><td>43.4 %</td></tr>
<tr><td>13</td><td>15</td><td>COMPETIVO</td><td>B. ROCHARD</td><td>0.570</td><td>3.7 %</td><td>11.6 %</td><td>20.2 %</td></tr></table></section>
<section id="zone-9" class="card"><div class="label">9 · Statistiques des chevaux suivis</div><p>Aucune course réelle enregistrée.</p></section>
</main></body></html>"""

ENTREE = {
    'date': '2026-11-05',
    'course': {'reunion': 1, 'numero': 1, 'hippodrome': 'Vincennes', 'nom': "Prix D'avranches", 'heure': '13:55',
               'discipline': 'Attelé', 'distance_m': 2100, 'partants': 17, 'corde': 'gauche', 'allocation_eur': 59000},
    'arrivee': {'ordre': [9, 6, 15, 1, 5],
                'arrivants': [{'rang': 1, 'numero': 9, 'nom': 'Ready Star'}, {'rang': 2, 'numero': 6, 'nom': 'Humanity Pellini'},
                              {'rang': 3, 'numero': 15, 'nom': 'Competivo'}, {'rang': 4, 'numero': 1, 'nom': 'Kotkie'},
                              {'rang': 5, 'numero': 5, 'nom': 'Every Time Winner'}],
                'rapports': [{'pari': 'Simple placé', 'type': 'simple', 'combinaison': [6], 'rapport': 3.6},
                             {'pari': 'Tiercé', 'type': 'ordre', 'combinaison': [9, 6, 15], 'rapport': 98.4},
                             {'pari': 'Quinté+', 'type': 'ordre', 'combinaison': [9, 6, 15, 1, 5], 'rapport': 3439.7}]},
}


class Constats(unittest.TestCase):
    def test_ordre_probable_et_box(self):
        phrases = page.analyse(PAGE, ENTREE['arrivee'])
        self.assertIn('L’ordre probable de la page (6 – 4 – 5 – 9 – 12) : 3 chevaux de ses cinq premiers sont '
                      'dans les cinq premiers de l’arrivée (6, 5, 9).', phrases)
        self.assertIn('Tiercé box 5 (6, 4, 5, 9, 12), 10 combinaisons : perdu, il manquait n° 15 (3e).', phrases)
        self.assertIn('Quinté box 6 (6, 4, 5, 9, 12, 17), 6 combinaisons : perdu, il manquait n° 15 (3e), n° 1 (4e).', phrases)
        self.assertIn('Simple placé n° 6 : gagné, 3,60 € pour 1 €.', phrases)

    def test_favori_et_absents_de_l_ordre_probable(self):
        phrases = page.analyse(PAGE, ENTREE['arrivee'])
        self.assertIn('Le favori du modèle, n° 6 Humanity Pellini, a fini 2e, dans les trois premiers : '
                      'la page le donnait à 42,4 %.', phrases)
        self.assertTrue(any(p.startswith('Le n° 15 Competivo (3e à l’arrivée) n’était que 13e') for p in phrases))


class Insertion(unittest.TestCase):
    def test_bloc_et_zone_9(self):
        nouvelle = page.inserer(PAGE, page.bloc_resultat(ENTREE, PAGE), page.zone9(PAGE, ENTREE))
        self.assertIn('Arrivée officielle : 9-6-15-1-5', nouvelle)
        self.assertIn('ordre 3 439,70 € · désordre —', nouvelle)
        self.assertIn('<td>6</td><td>Humanity Pellini</td>', nouvelle)
        self.assertIn('<td>2e</td>', nouvelle)  # rang d’arrivée du n° 6
        self.assertNotIn('Aucune course réelle enregistrée.', nouvelle)  # la zone 9 est remplacée

    def test_relance_sans_changement(self):
        une_fois = page.inserer(PAGE, page.bloc_resultat(ENTREE, PAGE), page.zone9(PAGE, ENTREE))
        deux_fois = page.inserer(une_fois, page.bloc_resultat(ENTREE, une_fois), page.zone9(une_fois, ENTREE))
        self.assertEqual(une_fois, deux_fois)
        self.assertEqual(une_fois.count('<!-- resultat:debut -->'), 1)


if __name__ == '__main__':
    unittest.main()
