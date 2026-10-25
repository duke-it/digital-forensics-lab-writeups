# Digital Forensics Lab Write-ups

Bienvenue ! Ce dépôt rassemble mes write-ups de criminalistique numérique : une série d'investigations menées sur les 10 labs du projet [digital-forensics-lab](https://github.com/vonderchild/digital-forensics-lab).

Ma règle pour chaque lab : ne pas me contenter de trouver la réponse, mais **raconter l'enquête**. Reconstituer la chronologie, identifier les preuves, et expliquer chaque outil comme chaque raisonnement. On apprend autant de la démarche que du résultat.

## Les write-ups publiés

| # | Write-up | Ce qu'on y pratique |
|:---:|---|---|
| 01 | [**Fondamentaux Linux (CLI)**](./Lab-01-linux-fundamentals/) | `find`, `grep`, hachage MD5/SHA1, `file`, `strings`, hexedit, magic bytes |
| 03 | [**Documents & stéganographie**](./Lab-03-document-stego/) | `olevba`, désobfuscation VBA, OOXML, `exiftool`, `steghide`, CyberChef, Audacity |
| 04 | [**Applications web & journaux WAF**](./Lab-04-web-waf-logs/) | Path Traversal, RCE, SQL Injection, ModSecurity / OWASP CRS, Docker |

Les labs 02, puis 05 à 10, arrivent au fil de ma progression.

## Comment je travaille

Les labs proviennent du dépôt [vonderchild/digital-forensics-lab](https://github.com/vonderchild/digital-forensics-lab). Chaque environnement est reconstitué localement, et l'analyse se fait sur les artefacts fournis (journaux, documents, images, captures réseau…) avec des outils open source. Les fichiers bruts et les échantillons sensibles ne sont jamais redistribués : seules les captures d'analyse accompagnent les write-ups.

## À propos

Cette pratique s'inscrit dans une démarche personnelle de montée en compétence, née de ma passion pour les CTF. Mon objectif : consolider mes réflexes en réponse à incident et en analyse forensique, et être un atout solide pour mon équipe en compétition.
