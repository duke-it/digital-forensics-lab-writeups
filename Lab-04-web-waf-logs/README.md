# Lab 04 — Applications Web & Journaux WAF

**Sujet :** analyse post-incident d'une compromission d'un serveur web Apache (LFI, RCE, SQLi), à partir des journaux Apache (`access.log`, `error.log`) et ModSecurity (`modsec_audit.log`).

## Énoncé

> Vous êtes un spécialiste de la cybersécurité qui a été appelé à enquêter sur une grave violation de cybersécurité. Le serveur web de l'entreprise a été compromis, et l'attaquant a tenté d'exploiter plusieurs vulnérabilités. On vous a confié la tâche de reconstituer les intentions de l'assaillant et de découvrir l'étendue des dégâts. Dans cet esprit, votre défi est de répondre aux questions suivantes :
>
> 1. De quelle adresse IP semble provenir l'attaque ?
> 2. Quelles vulnérabilités pensez-vous être exploitées, et quelles preuves avez-vous pour étayer vos conclusions ?
> 3. Comment pouvons-nous déterminer quel navigateur web l'attaquant utilise ?
> 4. L'attaquant a-t-il utilisé des outils automatisés pendant l'attaque ? Si oui, pouvez-vous identifier le nom de l'outil et son but ?
> 5. Quel fichier l'attaquant essayait-il d'accéder mais n'a pas pu à cause de l'accès limité au serveur ?
> 6. L'attaquant a-t-il eu accès à des données confidentielles ? Si oui, quelle quantité de données a été compromise ?
> 7. Un secret important a été compromis. Tu peux trouver une solution ? Indice : le secret que vous cherchez ne se trouve ni dans un fichier `.sql` ni dans un fichier `.php`.
> 8. L'attaquant a laissé un message à l'administrateur du serveur. Renseignez-vous sur ce que disait le message, et mentionnez aussi comment vous avez pu le trouver.
> 9. Quels étaient certains indicateurs confirmant qu'une attaque avait eu lieu ? Quelles ont été vos principales conclusions de cette attaque ?
> 10. Sur la base de cette attaque, quels indicateurs de compromission peuvent être utilisés pour détecter de futures attaques ?

![Énoncé de l'exercice](screenshots/01-exercice-enonce.png)

---

## Environnement

- Serveur cible : Apache 2.4.41/2.4.52 (Ubuntu), PHP 7.4, MySQL, ModSecurity 2.9.x + OWASP CRS 3.2/3.3 (mode `DETECTION_ONLY`)
- Déploiement : conteneur Docker (`Dockerfile` fourni par le lab)
- Journaux analysés : `/var/log/apache2/access.log`, `error.log`, `modsec_audit.log`

---

## Méthodologie — déroulé réel de l'investigation

### 1. Déploiement de l'environnement

```bash
cd digital-forensics-lab/Lab\ 04/files/app
sudo docker build -t app:latest .
sudo docker run -p 9090:80 app:latest
```

### 2. Accès au conteneur pour consulter les journaux

```bash
sudo docker exec -it great_chebyshev bash
cd /var/log/apache2
```

### 3. Lecture chronologique de `access.log`

```bash
cat access.log
```

Première lecture des requêtes de l'attaquant : reconnaissance, puis tentatives de path traversal sur `images.php` et `view.php`.

![access.log — séquence d'attaque LFI](screenshots/02-access-log-attaque-lfi.png)

### 4. Croisement avec `modsec_audit.log`

```bash
cat modsec_audit.log
```

Pour chaque requête suspecte repérée dans `access.log`, vérification de la règle OWASP CRS déclenchée et de son niveau de sévérité.

![modsec_audit.log — alerte LFI/RCE sur etc/passwd](screenshots/03-modsec-audit-lfi-rce-alert.png)
![modsec_audit.log — détail de la transaction](screenshots/04-modsec-audit-lfi-rce-suite.png)
![modsec_audit.log — nouvelle transaction](screenshots/05-modsec-audit-nouvelle-transaction.png)
![modsec_audit.log — fin de transaction](screenshots/06-modsec-audit-fin-transaction.png)

### 5. Reproduction de l'attaque RCE via `command.php`

Test manuel dans le navigateur pour confirmer l'exécution de commande arbitraire :

![command.php — exécution de cat /etc/passwd](screenshots/07-command-php-cat-etc-passwd.png)

Confirmation dans les journaux :

```bash
cat access.log
```
![access.log — requêtes POST vers command.php](screenshots/08-access-log-post-command-php.png)

```bash
cat modsec_audit.log
```
![modsec_audit.log — corps de requête POST cmd=cat+/etc/passwd](screenshots/09-modsec-audit-post-body-cmd.png)
![modsec_audit.log — correspondance etc/passwd](screenshots/10-modsec-audit-etc-passwd-matched.png)

### 6. Tentative d'accès à `/etc/shadow`

```bash
cat modsec_audit.log
```
![modsec_audit.log — tentative sur etc/shadow](screenshots/11-modsec-audit-etc-shadow-tentative.png)

Vérification directe côté conteneur, en tant que root, pour comprendre pourquoi l'attaquant (lui, en tant qu'utilisateur `www-data`) échoue :

```bash
cat /etc/shadow
```
![Contenu de /etc/shadow (lu en root, à titre de comparaison)](screenshots/12-cat-etc-shadow-output.png)

```bash
cat error.log | grep "Permission denied"
```
![error.log — refus d'accès à etc/shadow](screenshots/13-error-log-permission-denied-shadow.png)

### 7. Détection de l'injection SQL automatisée

```bash
cat error.log | grep SQLi
```
![error.log — détection SQLi via libinjection sur users.php](screenshots/14-error-log-sqli-detection.png)

### 8. Analyse du second jeu de journaux (fourni par le lab, `logs.zip`)

```bash
cd Lab\ 04/files/Exercice/apache2
ls
cat other_vhosts_access.log
cat access.log
```
![Extraction de logs.zip et lecture de access.log](screenshots/15-terminal-logs-zip-access-log.png)
![access.log — suite de la chronologie](screenshots/16-access-log-suite-1.png)
![access.log — path traversal vers etc/shadow, puis command.php](screenshots/17-access-log-suite-2.png)
![access.log — requêtes users.php et apparition de sqlmap](screenshots/18-access-log-users-php-sqlmap.png)
![access.log — sqlmap et découverte de important_note.txt](screenshots/19-access-log-sqlmap-important-note.png)

### 9. Analyse détaillée des alertes ModSecurity sur ce second jeu de logs

![modsec_audit.log — alerte sur le Host header](screenshots/20-modsec-host-header-warning.png)
![modsec_audit.log — LFI détaillée sur images.php](screenshots/21-modsec-lfi-images-php-detail.png)
![Requête/réponse HTTP — view.php?image=/etc/passwd](screenshots/22-view-php-etc-passwd-request.png)
![modsec_audit.log — détail de la règle Path Traversal](screenshots/23-modsec-path-traversal-detail.png)
![error.log — anomaly score à 43, échec PHP file_get_contents](screenshots/24-apache-error-anomaly-score-43.png)

### 10. Découverte du secret et du message caché

En inspectant le corps de réponse HTTP de `command.php` capturé par ModSecurity :

![command.php — message caché révélant un mot de passe](screenshots/25-command-php-secret-message.png)
![command.php — réponse complète avec message et warning Host header](screenshots/27-command-php-full-response-host-warning.png)

Comparaison avec le mot de passe MySQL réel trouvé dans `database.sql` :

![database.sql — CREATE USER avec mot de passe](screenshots/26-database-sql-password.png)

---

## Réponses aux questions

### 1. Adresse IP de l'attaquant

`192.168.0.106` (jeu de journaux officiel du lab, `access.log`).

### 2. Vulnérabilités exploitées

| Vulnérabilité | Preuve |
|---|---|
| **Path Traversal / LFI** | `GET /view.php?image=../../../etc/passwd` → HTTP 200, contenu de `/etc/passwd` renvoyé. Alertes ModSecurity 930100 ("Path Traversal Attack") et 930120 ("OS File Access Attempt") |
| **RCE (Remote Command Execution)** | `command.php` exécute directement des commandes shell arbitraires côté serveur (`cat /etc/passwd` exécuté avec succès). Alerte ModSecurity 932160 ("Remote Command Execution: Unix Shell Code Found") |
| **SQL Injection** | Requêtes sur `users.php` détectées par libinjection : `user1' AND 1=1 #` puis `user1' UNION SELECT username, email, password FROM users #`. Alerte ModSecurity 942100 |

### 3. Navigateur utilisé par l'attaquant

User-Agent constant sur l'ensemble des requêtes manuelles :

```
Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0
```

→ **Firefox 102** sous Linux.

### 4. Outil automatisé détecté

`sqlmap/1.6.11#stable (https://sqlmap.org)`, visible tel quel dans le champ User-Agent des requêtes vers `users.php` en fin de chronologie.

**Rôle :** sqlmap est un outil open-source d'automatisation de la détection et de l'exploitation d'injections SQL (énumération de bases, extraction de données, prise de contrôle via SQLi). Son apparition marque le passage d'une phase d'exploitation manuelle à une phase d'automatisation sur `users.php`.

### 5. Fichier convoité mais inaccessible

`/etc/shadow`. Tentatives répétées via LFI (`view.php?image=`) et RCE (`command.php`, `cat /etc/shadow`), systématiquement bloquées :
- Alertes ModSecurity 930120/932160 déclenchées (mêmes règles que pour `/etc/passwd`)
- `error.log` : `cat: /etc/shadow: Permission denied` — l'utilisateur système exécutant Apache (`www-data`) n'a pas les droits de lecture sur ce fichier, indépendamment du blocage WAF

### 6. Données confidentielles compromises

Oui, au minimum le contenu intégral de `/etc/passwd` (comptes système du serveur), obtenu à plusieurs reprises via LFI et RCE.

L'attaquant a également tenté d'extraire le contenu de la table `users` (colonnes `username`, `email`, `password`) via une injection SQL de type UNION sur `users.php`, automatisée avec sqlmap.

### 7. Le secret compromis

L'indice précisait que le secret ne se trouve « ni dans un fichier `.sql` ni dans un fichier `.php` » — la clé était donc de chercher dans le **contenu généré/affiché**, pas dans le code source.

Le secret a été retrouvé dans le corps de réponse HTML de `command.php`, capturé par `modsec_audit.log` : un message caché dans une `<div>` du template contient un mot de passe en clair (`sup3r_s3cr3t_4nd_1mp0rt4nt_p4ssw0rd`).

À noter : ce mot de passe diffère légèrement de celui présent dans `database.sql` pour l'utilisateur MySQL `user`@`localhost` (`$up3rs3cr3tp4ssw0rd`) — probablement un piège volontaire du lab pour tester la rigueur de lecture.

### 8. Message laissé à l'administrateur

Trouvé au même endroit qu'au point 7 — dans le corps de réponse HTML de `command.php`, visible uniquement via l'inspection du corps de réponse capturé par ModSecurity (invisible en lisant simplement le code source PHP, puisqu'il s'agit de contenu généré/inclus dynamiquement).

Le message est un avertissement ironique adressé par les développeurs à eux-mêmes/à l'administrateur, sur l'absence de contrôles de sécurité mis en place — révélant par la même occasion un mot de passe sensible en clair.

### 9. Indicateurs confirmant l'attaque

- Alertes ModSecurity de sévérité **CRITICAL** répétées, correspondant à des règles OWASP CRS distinctes (LFI, RCE, SQLi)
- **Anomaly score** en augmentation progressive, jusqu'à **43** sur les tentatives LFI les plus poussées
- Erreurs applicatives PHP corrélées (`file_get_contents(...): Failed to open stream`)
- Présence d'un User-Agent d'outil d'exploitation automatisé (`sqlmap`)
- Séquence logique et progressive de l'attaque : reconnaissance → découverte LFI → élévation vers RCE → pivot vers SQLi automatisé

### 10. Indicateurs de compromission (IOC) pour la détection future

- Adresse IP source de l'attaque
- Motifs de traversée de répertoire (`../`, `%2e%2e%2f`, encodages équivalents) dans les paramètres GET/POST
- User-Agent contenant des signatures d'outils connus (`sqlmap`, autres scanners automatisés)
- Requêtes vers des endpoints sensibles (`command.php`, `view.php`) avec des paramètres contenant des chemins système
- Règles ModSecurity/OWASP CRS déclenchées : `930100`, `930120`, `932160`, `942100`, `949110`, `980130`
- Score d'anomalie ModSecurity anormalement élevé sur une session/IP donnée
