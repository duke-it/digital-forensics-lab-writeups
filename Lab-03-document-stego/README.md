# Lab 03 : Analyse de documents et stéganographie

> Write-up de la série sur le dépôt [vonderchild/digital-forensics-lab](https://github.com/vonderchild/digital-forensics-lab).
> Chaque exercice est traité comme une investigation : démarche, outils et raisonnement, pas seulement la réponse.

## L'énoncé

> **Exercice 1.** Une attaque par phishing a été signalée : un employé a reçu par mail un document Word piégé, en apparence envoyé par une source de confiance. En l'ouvrant, il a déclenché les macros qu'il contenait, et l'attaquant a pris la main sur son poste. Un secret révélant l'identité de l'attaquant est caché dans le code de la macro. Mission : analyser ce code et extraire le secret, au format `flag{s0me_str1ng}`. Fichier : `YearlyBonus.docm`.
>
> **Exercice 2.** Une taupe au sein du gouvernement a transmis une information top secrète à un espion. Elle l'a cachée par stéganographie dans une image, que l'espion a ensuite collée dans un PowerPoint, recouverte de nombreuses images aléatoires. Mission : extraire la première image, l'information top secrète, ainsi que le nom et la localisation de la source. Fichier : `Presentation.pptx`.
>
> **Exercice 3.** À partir du fichier audio fourni, trouver comment afficher son spectrogramme dans Audacity et récupérer le flag. Fournir une capture. Fichier : `super_secret_audio.wav`.

## Introduction

Un document Office, une image ou un fichier audio ont l'air inoffensifs. C'est justement ce qui en fait de bons vecteurs : un document peut embarquer du code qui s'exécute à l'ouverture, une image peut transporter un fichier caché, un son peut contenir un message qu'aucune oreille n'entendra.

Ce lab explore ces trois façons de dissimuler de l'information. Le premier exercice est une **macro VBA malveillante** dont le secret est obfusqué sur deux couches. Le deuxième cache une **image porteuse** au milieu de cinquante leurres dans un PowerPoint, avec des indices dans ses métadonnées et un fichier dissimulé à l'intérieur. Le troisième dessine un **message dans les fréquences** d'un fichier audio.

## Rappels : les notions du lab

**Les macros VBA.** Les documents Office peuvent contenir du code écrit en VBA (Visual Basic for Applications). Un fichier dont l'extension finit par `m` (`.docm`, `.xlsm`, `.pptm`) est un document « à macros ». Certaines fonctions se lancent toutes seules, comme `AutoOpen()` à l'ouverture du document : c'est ce qui en fait un vecteur de phishing redoutable.

**L'analyse statique.** Analyser un fichier piégé de façon statique, c'est lire son code **sans jamais l'exécuter**. C'est la règle de base face à un document suspect : on ne l'ouvre pas dans Word, on l'inspecte avec des outils dédiés.

**Le format OOXML.** Depuis Office 2007, un `.docx`, `.pptx` ou `.xlsx` est en réalité une **archive ZIP** qui contient des fichiers XML et des médias. On peut donc l'ouvrir avec `unzip` et explorer son contenu comme un simple dossier. Les images d'un PowerPoint se trouvent dans `ppt/media/`.

**Les métadonnées EXIF.** Une photo embarque souvent des informations cachées : appareil utilisé, date, auteur, et parfois coordonnées GPS. Elles sont précieuses pour une enquête, mais se falsifient très facilement : c'est une piste, jamais une preuve à elle seule.

**La stéganographie.** C'est l'art de cacher un message dans un support anodin, de sorte que personne ne soupçonne qu'il y a quelque chose à chercher. Le choix de l'outil dépend du format :

| Format du support | Outil adapté |
|---|---|
| JPEG, BMP, WAV, AU | `steghide` |
| PNG, BMP | `zsteg` |
| Audio (message dessiné dans le son) | Audacity ou Sonic Visualiser, vue spectrogramme |

**L'analyse de fréquence.** Dans un texte anglais, certains caractères reviennent bien plus souvent que d'autres, l'espace en tête. Si un texte a été décalé d'une valeur fixe (comme dans un chiffre de César), le caractère le plus fréquent du texte chiffré correspond très probablement à l'espace. L'écart entre les deux donne le décalage.

## La boîte à outils

| Étape | Outils |
|---|---|
| Système d'analyse | Ubuntu, poste isolé des fichiers bruts |
| Document et macro | `oletools` (`oleid`, `olevba`), Python 3, CyberChef |
| Image et métadonnées | `file`, `unzip`, `exiftool`, `steghide` |
| Audio | Audacity (vue spectrogramme) |

> **Manipulation responsable.** Le `.docm` contient une macro active et l'image porte un fichier caché. Toute l'analyse est **statique** : les fichiers ne sont jamais exécutés ni ouverts dans une suite bureautique, et le travail se fait sur des copies.

## Le fil du lab, en une phrase

On lit une macro piégée sans l'exécuter et on casse son obfuscation par analyse de fréquence, on retrouve une image porteuse par son format, on lui fait cracher ses métadonnées puis son fichier caché, et on finit par regarder un son au lieu de l'écouter.

---

## Résolution, exercice par exercice

## Exercice 1 : la macro VBA malveillante (`YearlyBonus.docm`)

### Étape 1 : le triage

Premier réflexe face à un document suspect : savoir ce qu'il contient, sans l'ouvrir.

```bash
file YearlyBonus.docm
oleid YearlyBonus.docm
```

`file` confirme un document Word 2007 et plus récent. `oleid` passe le fichier au crible et le classe tout de suite en **risque élevé** : il contient des macros VBA et des mots clés suspects.

![oleid signale des macros VBA suspectes](screenshots/01-exo1-oleid.png)

> Réflexe : `oleid` d'abord, pour savoir en dix secondes s'il y a des macros et si elles sont inquiétantes.

### Étape 2 : lire la macro sans l'exécuter

```bash
olevba YearlyBonus.docm
```

`olevba` extrait le code VBA à froid. Deux fonctions ressortent :

* `AutoOpen()` se lance à l'ouverture du document, affiche « You have been hacked! », puis appelle `doShenanigans`.
* `doShenanigans()` construit un tableau de **101 octets**, **ajoute 3 à chacun**, puis convertit le tout en texte.

![olevba affiche le code de la macro](screenshots/02-exo1-olevba-macro.png)

Je refais mentalement le calcul : même après ce `+3`, le texte reste illisible. Il existe donc une **seconde couche** d'encodage, qui n'apparaît nulle part dans le code. C'est elle qu'il faut retrouver.

### Étape 3 : décoder, première méthode avec Python

Plutôt que de lancer la macro, je réécris sa logique en Python. C'est sûr, reproductible, et ça oblige à comprendre ce que fait le code. J'extrais d'abord les 101 octets en une commande :

```bash
olevba YearlyBonus.docm | grep -oP 'byteArray\(\d+\) = \K\d+' > bytes.txt
```

Le script applique ensuite la couche connue (`+3`, comme la macro), puis **déduit la couche manquante par analyse de fréquence**. Après le `+3`, le caractère le plus fréquent est `\x19`, soit 25 en ASCII. Dans une phrase anglaise, le caractère le plus fréquent est l'espace, soit 32. Le décalage manquant vaut donc `32 − 25 = 7`, pour un décalage total de **+10**.

```python
from collections import Counter

b = [int(x) for x in open('bytes.txt').read().split()]   # les 101 octets
s = ''.join(chr(v + 3) for v in b)                        # couche 1 : +3 (la macro)
decalage = 32 - ord(Counter(s).most_common(1)[0][0])      # couche 2 déduite : 7
message = ''.join(chr(ord(c) + decalage) for c in s)      # couche 2 appliquée
print(message)
```

> Le script complet et commenté est fourni : [`decode_yearlybonus.py`](./decode_yearlybonus.py).

![Le script affiche le message décodé et le flag](screenshots/03-exo1-decode-python.png)

### Étape 4 : décoder, seconde méthode avec CyberChef

Pour confirmer sans code, je rejoue la même chose dans CyberChef : `From Decimal`, puis `ADD 3`, puis `ADD 7`. L'opération **Frequency distribution** permet de *voir* le décalage : le pic de fréquence montre le caractère dominant, et donc la valeur à ajouter.

![Recette CyberChef : From Decimal, ADD 3, ADD 7](screenshots/04-exo1-cyberchef.png)

Les deux méthodes donnent le même résultat :

```
flag{such_m4cr0_much_w0w!}
```

> Réflexe : quand un texte reste illisible après une transformation connue, chercher une seconde couche. L'analyse de fréquence est souvent la clé d'un simple décalage.

## Exercice 2 : l'image cachée dans un PowerPoint (`Presentation.pptx`)

### Étape 1 : ouvrir le PowerPoint comme une archive

Un `.pptx` est un ZIP. Pas besoin de PowerPoint pour voir ce qu'il contient :

```bash
mkdir pptx_extract && cd pptx_extract
unzip ../Presentation.pptx
ls ppt/media/
```

Le dossier `ppt/media/` contient **51 images**, de `image1` à `image51`. L'image cherchée est quelque part là dedans, noyée parmi les leurres.

### Étape 2 : repérer l'intrus par son format

Plutôt que d'ouvrir les 51 images une par une, je demande à `file` de toutes les identifier d'un coup :

```bash
file ppt/media/image*
```

![file révèle que image1.jpg est le seul JPEG](screenshots/05-exo2-file-intrus.png)

Toutes les images sont des **PNG de 800 × 600**, sauf une : `image1.jpg`, le seul **JPEG**, en 800 × 450. C'est notre porteuse.

> Réflexe : face à un grand nombre de fichiers semblables, chercher celui qui diffère. L'anomalie est presque toujours la piste.

### Étape 3 : les métadonnées, pour le nom et la localisation

Premier réflexe sur toute image : `exiftool`.

```bash
exiftool image1.jpg
```

![exiftool affiche l'auteur et les coordonnées GPS](screenshots/06-exo2-exiftool-gps.png)

Deux champs répondent directement à la mission :

* **Artist : `Michael Scott`**, le nom de la source.
* **GPS : `34°12'39.33"N 118°26'11.15"W`**, sa localisation.

Je convertis ces coordonnées en degrés décimaux (`34.2109, -118.4364`, Nord et Ouest, donc les États-Unis) et je les place sur une carte : la source se trouve à **Van Nuys, Los Angeles, en Californie**.

![Géolocalisation des coordonnées GPS à Van Nuys](screenshots/07-exo2-geoloc.png)

### Étape 4 : extraire le fichier caché

Reste l'information top secrète, cachée par stéganographie. Ici, le format choisit l'outil : pour un **JPEG**, c'est `steghide` (et non `zsteg`, qui ne travaille que sur le PNG et le BMP).

```bash
steghide extract -sf image1.jpg
cat top_secret.txt
```

La passphrase est vide : un simple appui sur Entrée suffit.

![steghide extrait top_secret.txt](screenshots/08-exo2-steghide.png)

`steghide` extrait `top_secret.txt`, qui contient le message : *« I have obtained information regarding a top secret mission… »*

> Réflexe : une image suspecte cache souvent deux choses à deux endroits différents. Les métadonnées d'un côté (`exiftool`), le contenu caché de l'autre (`steghide` ou `zsteg` selon le format).

## Exercice 3 : la stéganographie audio (`super_secret_audio.wav`)

### Étape 1 : identifier le fichier

```bash
file super_secret_audio.wav
audacity super_secret_audio.wav
```

`file` confirme un fichier WAVE, PCM 16 bits, stéréo, à 22050 Hz. À l'écoute, rien d'intelligible. Mais dans la vue habituelle (la forme d'onde), on remarque des salves régulières tout au long du fichier : c'est souvent le signe qu'un texte a été dessiné dans le spectre.

### Étape 2 : passer en vue spectrogramme

Dans Audacity, j'ouvre le menu de la piste et je remplace **Forme d'onde** par **Spectrogramme**. Cette vue affiche les fréquences présentes à chaque instant. Le message n'est pas dans les octets du fichier : il est **dessiné dans les fréquences**, et il apparaît en toutes lettres.

![Le spectrogramme révèle le flag](screenshots/09-exo3-spectrogramme.png)

```
flag{h1dd3n_1n_th3_n01s3}
```

> Réflexe : face à un fichier audio suspect, le spectrogramme est le premier geste. Certains messages ne s'écoutent pas, ils se regardent.

---

## Récapitulatif

| Exercice | Ce qui était demandé | Réponse |
|:---:|---|---|
| 1 | Le secret caché dans la macro | `flag{such_m4cr0_much_w0w!}` |
| 2 | La première image | `image1.jpg`, le seul JPEG parmi 51 images |
| 2 | L'information top secrète | `top_secret.txt` : *« I have obtained information regarding a top secret mission… »* |
| 2 | Le nom et la localisation de la source | Michael Scott, à Van Nuys, Los Angeles (34.2109, −118.4364) |
| 3 | Le flag caché dans l'audio | `flag{h1dd3n_1n_th3_n01s3}` |

| Exercice | Vecteur | Outils clés | Concept |
|:---:|---|---|---|
| 1 | Macro VBA (`.docm`) | `oleid`, `olevba`, Python, CyberChef | Analyse statique, obfuscation sur deux couches, analyse de fréquence |
| 2 | Image dans un `.pptx` | `unzip`, `file`, `exiftool`, `steghide` | OOXML est un ZIP, anomalie de format, métadonnées et GPS, stéganographie JPEG |
| 3 | Audio (`.wav`) | Audacity | Stéganographie spectrale |

### Ce que j'ai appris

* Un document à macros (`.docm`, `.pptm`, `.xlsm`) s'analyse **sans l'ouvrir** : `oleid` pour le triage, `olevba` pour lire le code.
* Une obfuscation peut avoir **plusieurs couches**, dont une absente du code. L'analyse de fréquence permet de la retrouver, exactement comme pour casser un chiffre de César.
* Réécrire la logique d'un malware en Python est plus sûr et plus formateur que de l'exécuter.
* Les documents Office sont des **archives ZIP** : on explore `ppt/media/` ou `word/media/` directement.
* Le **format choisit l'outil** : `steghide` pour le JPEG, `zsteg` pour le PNG.
* Une métadonnée EXIF se falsifie en quelques secondes : c'est une **piste**, pas une preuve.
* En audio, le **spectrogramme** est le premier réflexe.

## Note éthique

Les artefacts bruts du lab (document à macro, image porteuse, fichier audio) ne sont pas redistribués dans ce dépôt ; seules les captures d'analyse et le script de décodage le sont. L'analyse a été menée de façon statique, sans jamais exécuter les fichiers piégés.

## Source

Lab issu de [vonderchild/digital-forensics-lab, Lab 03](https://github.com/vonderchild/digital-forensics-lab/tree/main/Lab%2003).
