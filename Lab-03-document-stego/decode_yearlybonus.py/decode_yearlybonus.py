#!/usr/bin/env python3
"""
Lab 03 - Exercice 1 : décodage du secret caché dans la macro de YearlyBonus.docm

Contexte :
    La macro VBA du document construit un tableau de 101 octets (byteArray),
    ajoute 3 à chacun, puis affiche le résultat sous forme de texte.
    Ce texte reste illisible : il existe une seconde couche d'encodage,
    non visible dans le code, que l'on retrouve par analyse de fréquence.

Principe :
    On n'exécute JAMAIS la macro. On réécrit sa logique en Python
    (analyse statique) : c'est sûr, reproductible et vérifiable.

Préparation (dans le dossier contenant YearlyBonus.docm) :
    olevba YearlyBonus.docm | grep -oP 'byteArray\(\d+\) = \K\d+' > bytes.txt

Utilisation :
    python3 decode_yearlybonus.py
"""

# Counter est un outil de Python qui compte combien de fois
# chaque élément apparaît dans une séquence (ici : chaque caractère).
from collections import Counter


# ---------------------------------------------------------------------------
# Étape 1 : lire les 101 octets extraits de la macro
# ---------------------------------------------------------------------------
# bytes.txt contient un nombre par ligne, recopié depuis le code VBA :
#     byteArray(0) = 77   ->  77
#     byteArray(1) = 101  ->  101
#     ...
# open(...).read()  lit tout le fichier en une seule chaîne de texte ;
# .split()          la découpe en morceaux, un morceau par nombre ;
# int(x)            transforme chaque morceau de texte ("77") en nombre (77).
b = [int(x) for x in open('bytes.txt').read().split()]
print("Nombre d'octets lus :", len(b))          # doit afficher 101


# ---------------------------------------------------------------------------
# Étape 2 : reproduire exactement ce que fait la macro (couche 1)
# ---------------------------------------------------------------------------
# Dans le VBA :
#     For iter = 0 To 100
#         byteArray(iter) = byteArray(iter) + 3
#     Next
#     ... StrConv(byteArray, vbUnicode)   ' octets -> texte
#
# En Python :
#     v + 3     ajoute 3 à chaque octet, comme la boucle VBA ;
#     chr(n)    donne le caractère dont le code ASCII est n
#               (exemple : chr(80) = 'P') ;
#     ''.join   colle tous les caractères bout à bout en une seule chaîne.
s = ''.join(chr(v + 3) for v in b)

# repr() affiche la chaîne en rendant visibles les caractères non imprimables,
# sous la forme \xNN (code hexadécimal). Exemple : '\x19' = code 25.
print("Après la couche 1 (+3) :", repr(s))       # encore illisible


# ---------------------------------------------------------------------------
# Étape 3 : analyse de fréquence pour trouver la couche 2
# ---------------------------------------------------------------------------
# Counter(s)          compte chaque caractère de s ;
# .most_common(1)     renvoie le plus fréquent sous la forme [(caractère, nombre)] ;
# [0]                 prend le premier (et seul) couple de la liste ;
# [0]                 prend le caractère dans ce couple (sans le nombre).
plus_frequent = Counter(s).most_common(1)[0][0]
print("Caractère le plus fréquent :", repr(plus_frequent))

# Hypothèse : dans une phrase en anglais, le caractère le plus fréquent
# est presque toujours l'espace, dont le code ASCII est 32.
# ord(c) fait l'inverse de chr() : il donne le code ASCII d'un caractère.
# Ici ord('\x19') = 25, donc le décalage manquant vaut 32 - 25 = 7.
decalage = 32 - ord(plus_frequent)
print("Décalage déduit :", decalage)


# ---------------------------------------------------------------------------
# Étape 4 : appliquer la couche 2 et lire le message
# ---------------------------------------------------------------------------
# On ajoute le décalage à chaque caractère, puis on reconstruit le texte.
# Si l'hypothèse est juste, le résultat est de l'anglais lisible.
message = ''.join(chr(ord(c) + decalage) for c in s)
print()
print(message)

# Bilan : le secret était encodé par un décalage total de +10
# (+3 visible dans la macro, +7 caché et retrouvé par analyse de fréquence).
