# Lab 01 — Fondamentaux Linux CLI pour la criminalistique numérique

**Sujet :** dix questions couvrant les commandes de base indispensables en investigation (recherche de fichiers, lecture, hachage, identification de type), avec un challenge pratique de récupération d'une image PNG corrompue via analyse et correction des magic bytes.

## Énoncé

> **Questions**
>
> 1. If we wanted to list all the `.txt` files in the current directory, what command would we want to use?
> 2. What command can we use to read the contents of the file `/etc/passwd`?
> 3. If we wanted to search for the string `Error` in all files in the `/var/log` directory, what would our command be?
> 4. What would be the commands to calculate MD5 and SHA1 hashes of the file `/etc/passwd`?
> 5. Use the `file` command to determine the type of the file `/usr/bin/cat` and explain the output in 2-3 sentences.
> 6. What command can we use to display all printable strings of length ≥ 8 in the file `/bin/bash`?
> 7. Given the following output of the `file` command, can you determine what's wrong with this file?
>    ```
>    $ file image.jpg
>    image.jpg: ELF 64-bit LSB pie executable, x86-64, version 1 (SYSV), dynamically linked, interpreter /lib64/ld-lin[...]
>    ```
> 8. If we wanted to look for files modified in the last 30 minutes in `/home` directory, what command would we want to use? *Hint: Explore how you can use `find` command to achieve this.*
> 9. What command can we use to display information about all active TCP connections on the system?
> 10. Given [this corrupted image file](https://raw.githubusercontent.com/vonderchild/digital-forensics-lab/main/Lab%2001/files/challenge.png), can you find a way to recover and view its contents? *Hint 1: A quick google search for "magic bytes" might help. Hint 2: Explore how `hexedit` can help you here.*

![Énoncé de l'exercice](screenshots/01-enonce.png)

---

## Environnement

- Système : Ubuntu, ligne de commande native
- Outils utilisés : `ls`, `cat`, `grep`, `md5sum`, `sha1sum`, `file`, `strings`, `find`, `ss`, `netstat`, `exiftool`, `hexedit`
- Fichier cible du challenge pratique : `challenge.png`, téléchargé depuis le dépôt du lab

---

## Méthodologie et réponses

### Q1 — Lister les fichiers `.txt` du répertoire courant

```bash
cd ~/digital-forensics-lab/Lab\ 01/files
mkdir test-Lab_01 && cd test-Lab_01
touch a.txt b.txt c.txt
ls *.txt
find . -name "*.txt"
```

**Réponse :** `ls *.txt` pour un listage simple du répertoire courant, ou `find . -name "*.txt"` si on veut inclure les sous-répertoires.

![Q1 — lister les fichiers .txt](screenshots/02-q1-lister-txt.png)

### Q2 — Lire le contenu de `/etc/passwd`

```bash
cat /etc/passwd
```

**Réponse :** `cat` affiche l'intégralité du fichier — ici la liste des comptes système (nom, UID, GID, shell par défaut).

![Q2 — cat /etc/passwd](screenshots/03-q2-cat-etc-passwd.png)

### Q3 — Chercher la chaîne `Error` dans `/var/log`

```bash
sudo grep -r "Error" /var/log/
```

**Réponse :** `grep -r` effectue une recherche récursive dans tous les fichiers du répertoire donné ; `sudo` est nécessaire car certains fichiers de `/var/log` ne sont lisibles que par root.

![Q3 — grep Error dans /var/log](screenshots/04-q3-grep-error-varlog.png)

### Q4 — Calculer les hash MD5 et SHA1 de `/etc/passwd`

```bash
md5sum /etc/passwd
sha1sum /etc/passwd
```

**Réponse :** deux commandes dédiées, une par algorithme. Ces hash serviraient à vérifier l'intégrité du fichier (détecter toute modification ultérieure).

![Q4 — md5sum et sha1sum](screenshots/05-q4-md5-sha1.png)

### Q5 — Type du fichier `/usr/bin/cat`, expliqué

```bash
file /usr/bin/cat
```

Sortie obtenue :
```
/usr/bin/cat: ELF 64-bit LSB pie executable, x86-64, version 1 (SYSV), dynamically linked, interpreter /lib64/ld-linux-x86-64.so.2, BuildID[sha1]=99d5c06a27f7c82eb86afb59e053f4f69c88c6fd, for GNU/Linux 3.2.0, stripped
```

**Explication (2-3 phrases) :** `/usr/bin/cat` est un exécutable au format **ELF** (le format binaire standard sous Linux), compilé pour une architecture **64 bits**. Il est **dynamiquement lié** (`dynamically linked`), ce qui signifie qu'il dépend de bibliothèques partagées chargées au lancement plutôt que d'embarquer tout son code — d'où la présence d'un interpréteur (`/lib64/ld-linux-x86-64.so.2`), le loader chargé de résoudre ces dépendances au démarrage. `stripped` indique enfin que les symboles de débogage ont été retirés du binaire.

![Q5 — file /usr/bin/cat](screenshots/06-q5-file-usr-bin-cat.png)

### Q6 — Chaînes imprimables de longueur ≥ 8 dans `/bin/bash`

```bash
strings -8 /bin/bash
```

**Réponse :** l'option `-8` (équivalent de `-n 8`) fixe la longueur minimale des chaînes affichées à 8 caractères, filtrant le bruit des chaînes plus courtes peu informatives.

![Q6 — strings sur /bin/bash](screenshots/07-q6-strings-bin-bash.png)

### Q7 — Analyse d'une sortie `file` fournie

Sortie donnée par l'énoncé :
```
$ file image.jpg
image.jpg: ELF 64-bit LSB pie executable, x86-64, version 1 (SYSV), dynamically linked, interpreter /lib64/ld-lin[...]
```

**Ce qui ne va pas :** le fichier porte l'extension `.jpg` (censé être une image), mais `file` révèle que son contenu réel est un **exécutable ELF Linux**. L'extension a été falsifiée — volontairement ou par accident — pour faire passer un exécutable pour une image inoffensive. C'est une technique classique de dissimulation utilisée pour contourner des contrôles de sécurité basés uniquement sur l'extension d'un fichier (par exemple sur un serveur qui n'autorise que l'upload d'images).

### Q8 — Fichiers modifiés dans les 30 dernières minutes dans `/home`

```bash
find /home/ -mmin -30
```

**Réponse :** `-mmin -30` cible les fichiers dont le contenu a été modifié il y a **moins de** 30 minutes.

![Q8 — find /home -mmin -30](screenshots/08-q8-find-home-mmin.png)

### Q9 — Connexions TCP actives

```bash
ss -tn
netstat -tn
```

**Réponse :** `ss -tn` est la commande moderne recommandée (`-t` pour TCP, `-n` pour des adresses numériques sans résolution DNS). `netstat -tn` reste une alternative equivalente, plus ancienne mais toujours largement utilisée.

![Q9 — ss et netstat, connexions TCP](screenshots/09-q9-ss-netstat-tcp.png)

### Q10 — Récupération de l'image corrompue

#### Étape 1 — Constat de la corruption

```bash
cd ~/digital-forensics-lab/Lab\ 01/files
file challenge.png
exiftool challenge.png
```

`file` renvoie simplement `data` — le fichier n'est pas reconnu comme une image, et `exiftool` confirme avec une erreur explicite : `File format error`.

![Q10 — exploration et confirmation de la corruption](screenshots/10-q10-exploration-corruption.png)

#### Étape 2 — Inspection des octets bruts avec `hexedit`

```bash
hexedit challenge.png
```

Les huit premiers octets du fichier sont `17 29 4E 47 0D 0A 1A 0A`, alors que la signature PNG correcte doit être `89 50 4E 47 0D 0A 1A 0A`. Seuls les deux premiers octets sont altérés (`17 29` au lieu de `89 50`) — le reste de la signature (`4E 47 0D 0A 1A 0A`, soit "PNG" + les octets de détection de corruption CR/LF) est resté intact.

![Q10 — en-tête corrompu vu dans hexedit](screenshots/11-q10-hexedit-avant.png)

#### Étape 3 — Correction de la signature

Dans `hexedit`, remplacement des deux premiers octets par les valeurs correctes :

```
17 → 89
29 → 50
```

![Q10 — en-tête corrigé dans hexedit](screenshots/12-q10-hexedit-apres.png)
![Q10 — gros plan sur la signature corrigée](screenshots/13-q10-header-corrige-zoom.png)

Sauvegarde des modifications (`Ctrl+X` dans hexedit).

#### Étape 4 — Vérification de la réparation

```bash
file challenge.png
exiftool challenge.png
```

`file` reconnaît maintenant correctement le fichier : `PNG image data, 562 x 424, 8-bit/color RGB, non-interlaced`. `exiftool` confirme avec le détail complet des métadonnées, sans erreur.

![Q10 — fichier réparé, confirmé par file et exiftool](screenshots/14-q10-file-exiftool-apres.png)

#### Étape 5 — Ouverture et récupération du contenu

```bash
eog challenge.png
```

L'image s'ouvre et révèle un message manuscrit "hello world", accompagné du texte :

> *Use the string 'flag{d1g1tal_f0r3ns1cs_101}' as an answer to the original question. This is an example of a capture the flag challenge. Hopefully you learnt something new today! :)*

![Q10 — image récupérée avec le flag](screenshots/15-q10-flag-recupere.png)

**Réponse finale :** la correction des deux premiers octets de la signature PNG (`17 29` → `89 50`) suffit à restaurer un fichier PNG valide et lisible, révélant le flag `flag{d1g1tal_f0r3ns1cs_101}`.

---

## Conclusions

Ce lab couvre les réflexes de base indispensables avant d'aborder des cas plus complexes : recherche et lecture de fichiers, hachage pour l'intégrité, et surtout la compréhension du principe des **magic bytes** — un fichier n'est pas défini par son extension mais par son contenu binaire réel, et une corruption (volontaire ou accidentelle) de sa signature peut être diagnostiquée et corrigée chirurgicalement une fois qu'on sait où regarder.
