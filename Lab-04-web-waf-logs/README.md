# Lab 04 — Applications Web & Journaux WAF

**Sujet :** analyse post-incident d'une compromission d'un serveur web Apache (LFI, RCE, SQLi), à partir des journaux Apache (`access.log`, `error.log`) et ModSecurity (`modsec_audit.log`).

**Contexte fourni :** un serveur web PHP/MySQL protégé par Apache + ModSecurity (règles OWASP CRS) a été compromis. L'objectif est de reconstituer la chronologie et les intentions de l'attaquant à partir des journaux uniquement.

---

## Environnement

- Serveur cible : Apache 2.4.41/2.4.52 (Ubuntu), PHP 7.4, MySQL, ModSecurity 2.9.x + OWASP CRS 3.2/3.3 (mode `DETECTION_ONLY`)
- Déploiement : conteneur Docker (`Dockerfile` fourni par le lab)
- Journaux analysés : `/var/log/apache2/access.log`, `error.log`, `modsec_audit.log`

---

## 1. Adresse IP de l'attaquant

`192.168.0.106` (identifiée dans l'ensemble des journaux fournis par le lab via `access.log`).

## 2. Vulnérabilités exploitées

| Vulnérabilité | Preuve |
|---|---|
| **Path Traversal / LFI** | `GET /view.php?image=../../../etc/passwd` → HTTP 200, contenu de `/etc/passwd` renvoyé. Alertes ModSecurity 930100 ("Path Traversal Attack") et 930120 ("OS File Access Attempt") |
| **RCE (Remote Command Execution)** | `command.php` exécute directement des commandes shell arbitraires côté serveur (`cat /etc/passwd` exécuté avec succès). Alerte ModSecurity 932160 ("Remote Command Execution: Unix Shell Code Found") |
| **SQL Injection** | Requêtes sur `users.php` détectées par libinjection : `user1' AND 1=1 #` puis `user1' UNION SELECT username, email, password FROM users #`. Alerte ModSecurity 942100 |

## 3. Navigateur utilisé par l'attaquant

Le User-Agent constant sur l'ensemble des requêtes manuelles est :

```
Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0
```

→ **Firefox 102** sous un système Linux.

## 4. Outil automatisé détecté

`sqlmap/1.6.11#stable (https://sqlmap.org)`, visible tel quel dans le champ User-Agent des requêtes vers `users.php` en fin de chronologie.

**Rôle :** sqlmap est un outil open-source d'automatisation de la détection et de l'exploitation d'injections SQL (énumération de bases, extraction de données, prise de contrôle via SQLi). Son apparition marque le passage d'une phase d'exploitation manuelle à une phase d'automatisation/industrialisation de l'attaque sur `users.php`.

## 5. Fichier convoité mais inaccessible

`/etc/shadow`. Tentatives répétées via LFI (`view.php?image=`) et RCE (`command.php`, `cat /etc/shadow`), systématiquement bloquées :
- Alertes ModSecurity 930120/932160 déclenchées (mêmes règles que pour `/etc/passwd`)
- `error.log` : `cat: /etc/shadow: Permission denied` — l'utilisateur système exécutant Apache (`www-data`) n'a pas les droits de lecture sur ce fichier, indépendamment du blocage WAF

## 6. Données confidentielles compromises

Oui. Au minimum :
- Contenu intégral de `/etc/passwd` (comptes système du serveur, obtenu à plusieurs reprises via LFI et RCE)

L'attaquant a également tenté d'extraire le contenu de la table `users` (colonnes `username`, `email`, `password`) via une injection SQL de type UNION sur `users.php`. *(Vérifier dans les journaux si une réponse HTTP contenant les données extraites a été capturée, pour confirmer si l'extraction a abouti.)*

## 7. Le secret compromis

L'indice précisait que le secret ne se trouve « ni dans un fichier `.sql` ni dans un fichier `.php` » — la clé était donc de chercher dans le **contenu généré/affiché**, pas dans le code source.

Le secret a été retrouvé dans le corps de réponse HTML de `command.php`, capturé par `modsec_audit.log` (section réponse de la transaction) : un message caché dans une `<div>` du template contient un mot de passe en clair.

*(Point à trancher dans la version finale : le mot de passe trouvé dans ce message et celui présent dans `database.sql` pour l'utilisateur MySQL `user`@`localhost` diffèrent légèrement — à documenter comme piège volontaire du lab ou à clarifier lequel constitue la véritable réponse attendue.)*

## 8. Message laissé à l'administrateur

Trouvé au même endroit qu'au point 7 — dans le corps de réponse HTML de `command.php`, visible uniquement via l'inspection du corps de réponse capturé par ModSecurity (invisible dans une simple lecture du code source PHP, puisqu'il s'agit de contenu généré/inclus dynamiquement).

Le message est un avertissement ironique adressé par les développeurs à eux-mêmes/à l'administrateur, sur l'absence de contrôles de sécurité mis en place — révélant par la même occasion un mot de passe sensible en clair, exposé « sur un panneau publicitaire » selon leurs propres mots.

## 9. Indicateurs confirmant l'attaque

- Alertes ModSecurity de sévérité **CRITICAL** répétées, correspondant à des règles OWASP CRS distinctes (LFI, RCE, SQLi)
- **Anomaly score** en augmentation progressive au fil des requêtes, jusqu'à **43** sur les tentatives LFI les plus poussées (seuil de blocage largement dépassé, bien qu'aucun blocage effectif ne soit appliqué en mode `DETECTION_ONLY`)
- Erreurs applicatives PHP corrélées (`file_get_contents(...): Failed to open stream`) confirmant les tentatives d'accès à des chemins hors périmètre
- Présence d'un User-Agent d'outil d'exploitation automatisé (`sqlmap`)
- Séquence logique et progressive de l'attaque : reconnaissance → découverte LFI → élévation vers RCE → pivot vers SQLi automatisé

## 10. Indicateurs de compromission (IOC) pour la détection future

- Adresse IP source de l'attaque (`192.168.0.106` dans ce cas)
- Motifs de traversée de répertoire (`../`, `%2e%2e%2f`, encodages équivalents) dans les paramètres GET/POST
- User-Agent contenant des signatures d'outils connus (`sqlmap`, autres scanners automatisés)
- Requêtes vers des endpoints sensibles (`command.php`, `view.php`) avec des paramètres contenant des chemins système (`etc/passwd`, `etc/shadow`)
- Règles ModSecurity/OWASP CRS déclenchées : `930100`, `930120`, `932160`, `942100`, `949110`, `980130`
- Score d'anomalie ModSecurity anormalement élevé sur une session/IP donnée

---

## Méthodologie

1. Déploiement de l'environnement via Docker (`docker build` + `docker run`, cf. `Dockerfile` du lab)
2. Accès au conteneur (`docker exec -it <container> bash`) pour consulter les journaux dans `/var/log/apache2/`
3. Lecture chronologique de `access.log` pour reconstituer la séquence de requêtes de l'attaquant
4. Croisement avec `modsec_audit.log` pour chaque requête suspecte, afin d'identifier la règle OWASP CRS déclenchée et son niveau de sévérité
5. Vérification côté `error.log` pour confirmer les échecs applicatifs et les refus au niveau système (permissions)
6. Reconstitution du corps de réponse HTTP pour les requêtes clés (`command.php`), révélant le secret et le message caché

---

## Captures d'écran

*(à insérer dans `/screenshots` : logs `access.log`, `modsec_audit.log`, exécution de commande via `command.php`, extrait `/etc/shadow` refusé, détection sqlmap, message caché découvert)*
