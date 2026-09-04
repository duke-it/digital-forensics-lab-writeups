# Digital Forensics Lab — Write-ups

Write-ups structurés des 10 labs du cours de criminalistique numérique (LPSIC, Université de Kara), couvrant l'analyse de journaux, la détection d'intrusions web, et l'investigation post-incident.

Chaque lab est traité comme une véritable investigation : reconstitution de la chronologie d'attaque, identification des preuves, et conclusions à partir des journaux fournis — pas de simples réponses aux questions, mais une méthodologie documentée.

## Labs

| # | Lab | Thématique | Techniques couvertes | Statut |
|---|---|---|---|---|
| 01 | — | — | — | ⏳ |
| 02 | — | — | — | ⏳ |
| 03 | — | — | — | ⏳ |
| 04 | [Applications Web & journaux WAF](./Lab-04-web-waf-logs/) | Compromission d'un serveur Apache via LFI, RCE et SQLi ; analyse croisée `access.log` / `error.log` / `modsec_audit.log` | Path Traversal, Remote Command Execution, SQL Injection, ModSecurity/OWASP CRS, Docker | ✅ |
| 05 | — | — | — | ⏳ |
| 06 | — | — | — | ⏳ |
| 07 | — | — | — | ⏳ |
| 08 | — | — | — | ⏳ |
| 09 | — | — | — | ⏳ |
| 10 | — | — | — | ⏳ |

## Source

Les labs proviennent du dépôt [vonderchild/digital-forensics-lab](https://github.com/vonderchild/digital-forensics-lab). Ils sont déployés localement via Docker à partir des `Dockerfile` fournis, et l'analyse se fait entièrement à partir des journaux système et applicatifs générés par chaque environnement (Apache, ModSecurity, MySQL, etc.).

## À propos

Cette pratique s'inscrit dans une démarche personnelle de montée en compétence en criminalistique numérique, née de ma découverte des CTF. L'objectif est de consolider mes compétences en réponse à incident et en analyse forensique, et d'être un atout solide pour mon équipe lors des compétitions.
