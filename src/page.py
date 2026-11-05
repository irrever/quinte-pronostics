"""Résultat, rapports et analyse dans les pages de pronostic du Quinté+ (AAAA-MM-JJ.html).

Lit data/quinte/jours.json (relevé fait par src/quinte.py) et, pour chaque jour dont l’arrivée est connue et dont la page
existe, insère :
- en tête de page, un bloc « Résultat » : réunion, heure, distance, partants, arrivée officielle et rapports PMU ;
- une comparaison avec ce que la page proposait (ordre probable, box de tiercé, quarté et quinté, simple placé) ;
- dans la zone 9 (statistiques des chevaux suivis) : le rang de chaque cheval à l’arrivée, à côté de sa probabilité de
  figurer dans les cinq premiers.
Les blocs sont encadrés par des commentaires : une nouvelle exécution les remplace, le reste de la page ne bouge pas.

Usage : python3 src/page.py
"""
import html
import json
import pathlib
import re
import sys

RACINE = pathlib.Path(__file__).resolve().parent.parent
DONNEES = RACINE / 'data' / 'quinte' / 'jours.json'
DEBUT, FIN = '<!-- resultat:debut -->', '<!-- resultat:fin -->'
ZONE9_DEBUT, ZONE9_FIN = '<!-- resultat-zone9:debut -->', '<!-- resultat-zone9:fin -->'
NOMBRE_ARRIVES = {'Tiercé': 3, 'Quarté': 4, 'Quinté': 5}
MOIS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre',
        'décembre']


def section(page, zid):
    m = re.search(r'<section id="%s"[^>]*>(.*?)</section>' % re.escape(zid), page, re.S)
    return m.group(1) if m else ''


def texte(fragment):
    fragment = re.sub(r'<style.*?</style>|<script.*?</script>', ' ', fragment, flags=re.S)
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', fragment))).strip()


def virgule(x, decimales=1):
    return ('%.*f' % (decimales, x)).replace('.', ',')


def montant(x, decimales=2):
    """Montant en euros, au format français : 3 439,70 €."""
    return ('{:,.{d}f}'.format(float(x), d=decimales)).replace(',', ' ').replace('.', ',') + ' €'


def ordinal(n):
    return '1er' if n == 1 else '%de' % n


def pluriel(n, singulier, pluriel_):
    return '%d %s' % (n, singulier if n == 1 else pluriel_)


def ordre_probable(page):
    """Les cinq chevaux de la zone 1, dans l’ordre affiché."""
    bloc = re.search(r'<div class="ordre">(.*?)</div>', section(page, 'zone-1'), re.S)
    return [int(n) for n in re.findall(r'<span[^>]*>(\d+)</span>', bloc.group(1))] if bloc else []


def boxes(page):
    """Les box proposés en zone 3 : (pari, taille, chevaux, nombre de combinaisons)."""
    out = []
    for pari, taille, chevaux, combi in re.findall(
            r'(Tiercé|Quarté|Quinté) Box (\d+) Chevaux : ([\d, ]+?) (\d+) combinaisons', texte(section(page, 'zone-3'))):
        out.append((pari, int(taille), [int(x) for x in re.findall(r'\d+', chevaux)], int(combi)))
    return out


def simple_place_favori(page):
    m = re.search(r'Simple placé n°(\d+)', texte(section(page, 'zone-3')))
    return int(m.group(1)) if m else None


def probabilites(page):
    """Chaque cheval de la zone 6, dans l’ordre du modèle : rang, numéro, nom, probabilités de gagner, top 3 et top 5."""
    out = []
    for cellules in re.findall(r'<tr[^>]*>(.*?)</tr>', section(page, 'zone-6'), re.S):
        c = [texte(x) for x in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', cellules, re.S)]
        if len(c) >= 8 and c[0].isdigit() and c[1].isdigit():
            out.append({'rang': int(c[0]), 'numero': int(c[1]), 'nom': c[2].title(),
                        'gagner': float(c[5].replace('%', '')), 'top3': float(c[6].replace('%', '')),
                        'top5': float(c[7].replace('%', ''))})
    return out


def analyse(page, arrivee):
    """Constats de comparaison entre ce que la page proposait et l’arrivée, un par phrase."""
    ordre = arrivee['ordre']
    cinq = ordre[:5]
    phrases = []
    probable = ordre_probable(page)
    if probable:
        touches = [n for n in probable if n in cinq]
        phrases.append('L’ordre probable de la page (%s) : %s de ses cinq premiers sont dans les cinq premiers de l’arrivée (%s).'
                       % (' – '.join(str(n) for n in probable), pluriel(len(touches), 'cheval', 'chevaux'),
                          ', '.join(str(n) for n in touches) or 'aucun'))
    tableau = probabilites(page)
    par_numero = {p['numero']: p for p in tableau}
    if tableau:
        fav = tableau[0]
        if fav['numero'] in ordre:
            rang = ordre.index(fav['numero']) + 1
            if rang <= 3:
                phrases.append('Le favori du modèle, n° %d %s, a fini %s, dans les trois premiers : la page le donnait à %s %%.'
                               % (fav['numero'], fav['nom'], ordinal(rang), virgule(fav['top3'])))
            else:
                phrases.append('Le favori du modèle, n° %d %s, a fini %s : la page ne le donnait qu’à %s %% pour les trois premiers.'
                               % (fav['numero'], fav['nom'], ordinal(rang), virgule(fav['top3'])))
        for n in [x for x in cinq if x not in probable]:
            p = par_numero.get(n)
            if p:
                phrases.append('Le n° %d %s (%s à l’arrivée) n’était que %s au classement du modèle, avec %s %% de chances d’être dans les cinq premiers.'
                               % (n, p['nom'], ordinal(ordre.index(n) + 1), ordinal(p['rang']), virgule(p['top5'])))
    for pari, taille, chevaux, combi in boxes(page):
        premiers = ordre[:NOMBRE_ARRIVES[pari]]
        manquent = [x for x in premiers if x not in chevaux]
        decrit = '%s box %d (%s), %s' % (pari, taille, ', '.join(map(str, chevaux)), pluriel(combi, 'combinaison', 'combinaisons'))
        if not manquent:
            phrases.append('%s : gagné.' % decrit)
        else:
            detail = ', '.join('n° %d (%s)' % (x, ordinal(ordre.index(x) + 1)) for x in manquent)
            phrases.append('%s : perdu, il manquait %s.' % (decrit, detail))
    place = simple_place_favori(page)
    if place is not None:
        gagne = place in ordre[:3]
        rapport = [r['rapport'] for r in arrivee.get('rapports', []) if r['pari'] == 'Simple placé' and r['combinaison'] == [place]]
        if gagne and rapport:
            phrases.append('Simple placé n° %d : gagné, %s pour 1 €.' % (place, montant(rapport[0])))
        else:
            phrases.append('Simple placé n° %d : %s.' % (place, 'gagné' if gagne else 'perdu'))
    return phrases


def rapports_html(arrivee):
    lignes = []
    par_pari = {}
    for r in arrivee.get('rapports', []):
        par_pari.setdefault(r['pari'], []).append(r)
    for pari in ('Quinté+', 'Quarté+', 'Tiercé'):
        ordre = [r for r in par_pari.get(pari, []) if r.get('type') == 'ordre']
        desordre = [r for r in par_pari.get(pari, []) if r.get('type') == 'désordre']
        if ordre:
            lignes.append('<li><strong>%s</strong> : ordre %s · désordre %s</li>' % (
                pari, montant(ordre[0]['rapport']), montant(desordre[0]['rapport']) if desordre else '—'))
    for pari, libelle in (('2sur4', '2 sur 4'), ('Couplé', 'Couplé gagnant'), ('Couplé placé', 'Couplé placé'),
                          ('Simple', 'Simple gagnant'), ('Simple placé', 'Simple placé')):
        items = par_pari.get(pari, [])
        if items:
            lignes.append('<li><strong>%s</strong> : %s</li>' % (libelle, ' · '.join(
                '%s %s' % ('-'.join(str(n) for n in r['combinaison']), montant(r['rapport'])) for r in items)))
    return '<ul class="note">' + ''.join(lignes) + '</ul>'


def infos_course(c):
    morceaux = ['R%d · %s · C%d — %s' % (c['reunion'], c['hippodrome'], c['numero'], c['nom']),
                'départ %s' % c['heure'].replace(':', ' h ')]
    morceaux.append('%s · %s m' % (str(c['discipline']).lower(), '{:,}'.format(c['distance_m']).replace(',', ' ')))
    if c.get('partants'):
        morceaux.append('%d partants' % c['partants'])
    if c.get('corde'):
        morceaux.append('corde à %s' % c['corde'])
    if c.get('allocation_eur'):
        morceaux.append('%s d’allocation' % montant(c['allocation_eur'], 0))
    return ' · '.join(morceaux)


def date_fr(iso):
    d = int(iso[8:10])
    return '%s %s %s' % ('1er' if d == 1 else str(d), MOIS[int(iso[5:7]) - 1], iso[:4])


def bloc_resultat(entree, page):
    c, a = entree['course'], entree['arrivee']
    noms = {x['numero']: x['nom'] for x in a['arrivants']}
    pastilles = ''.join("<span class='pastille r%d'>%d</span>" % (i + 1, n) for i, n in enumerate(a['ordre']))
    noms_txt = ' · '.join('%d %s' % (n, html.escape(noms.get(n, '').title())) for n in a['ordre'])
    constats = ''.join('<li>%s</li>' % html.escape(p) for p in analyse(page, a))
    return (DEBUT + '\n<section class="card accent-vert" id="resultat">'
            '<div class="label">Résultat · Quinté+ du %s</div>'
            '<h2>Arrivée officielle : %s</h2>'
            '<div class="ordre">%s</div>'
            '<p class="note">%s</p><p class="note">%s</p>'
            '<h3>Rapports PMU pour 1 € misé</h3>%s'
            '<h3>Ce que la page proposait, face à l’arrivée</h3><ul class="note">%s</ul>'
            '</section>\n' + FIN) % (
        html.escape(date_fr(entree['date'])), '-'.join(str(n) for n in a['ordre']), pastilles,
        html.escape(infos_course(c)), noms_txt, rapports_html(a), constats)


def zone9(page, entree):
    position = {n: i + 1 for i, n in enumerate(entree['arrivee']['ordre'])}
    lignes = ['<tr><td>%d</td><td>%d</td><td>%s</td><td>%s %%</td><td>%s</td></tr>' % (
        p['rang'], p['numero'], html.escape(p['nom']), virgule(p['top5']),
        ordinal(position[p['numero']]) if p['numero'] in position else '—') for p in probabilites(page)]
    return (ZONE9_DEBUT + '<div class="label">9 · Statistiques des chevaux suivis</div>'
            '<h2>Chaque cheval, face à l’arrivée</h2>'
            '<p class="note">Rang du modèle, probabilité de figurer dans les cinq premiers, rang à l’arrivée.</p>'
            '<table><thead><tr><th>Rang</th><th>N°</th><th>Cheval</th><th>Top 5</th><th>Arrivée</th></tr></thead>'
            '<tbody>%s</tbody></table>' % ''.join(lignes) + ZONE9_FIN)


def inserer(page, bloc, zone):
    """Remplace les blocs déjà insérés, ou les place : le résultat avant la zone 1, la zone 9 à la place de l’ancienne."""
    if DEBUT in page:
        page = re.sub(re.escape(DEBUT) + r'.*?' + re.escape(FIN) + r'\n?', lambda m: bloc, page, flags=re.S)
    else:
        page = page.replace('<section id="zone-1"', bloc + '<section id="zone-1"', 1)
    if ZONE9_DEBUT in page:
        page = re.sub(re.escape(ZONE9_DEBUT) + r'.*?' + re.escape(ZONE9_FIN), lambda m: zone, page, flags=re.S)
    else:
        page = re.sub(r'(<section id="zone-9"[^>]*>)(.*?)(</section>)', lambda m: m.group(1) + zone + m.group(3),
                      page, count=1, flags=re.S)
    return page


def mettre_a_jour(entree, chemin):
    """Ajoute le résultat à la page du jour. Renvoie True si la page a changé."""
    page = chemin.read_text(encoding='utf-8')
    nouvelle = inserer(page, bloc_resultat(entree, page), zone9(page, entree))
    if nouvelle != page:
        chemin.write_text(nouvelle, encoding='utf-8')
        return True
    return False


def main():
    donnees = json.loads(DONNEES.read_text(encoding='utf-8')) if DONNEES.exists() else {}
    modifiees = []
    for jour, entree in sorted(donnees.items()):
        if 'arrivee' not in entree or 'course' not in entree:
            continue
        chemin = RACINE / ('%s.html' % jour)
        if not chemin.exists():
            print('page absente pour %s' % jour)
            continue
        if mettre_a_jour(dict(entree, date=jour), chemin):
            modifiees.append(chemin.name)
    print('pages mises à jour : %s' % (', '.join(modifiees) or 'aucune'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
