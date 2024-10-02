# Introduction :

Ce projet met en œuvre un système permettant de suivre quotidiennement les insertions de données dans des tables spécifiques d'une base de données SQL Server. L'objectif est de fournir un moyen simple d'identifier les tables qui ont reçu de nouvelles données un jour donné et, surtout, les tables qui n'ont pas reçu les données attendues, ce qui indique potentiellement un problème dans le pipeline de données ou les processus système.

# Structure :
Le système suit les insertions pour les tables suivantes :
1. facturation
2. transaction
3. shop
4. recharge
5. city
6. produit
7. client
8. account
9. employee
10. ATM-card

# Solutions mises en œuvre
Nous avons mis en œuvre deux solutions différentes pour suivre les insertions de tables. Les deux solutions utilisent une table TrackingInsert pour stocker la date et l'heure de la premeir insertion pour chaque table surveillée aujourd'hui.

# Solution 1 : approche du contexte de session
Cette solution utilise le contexte de session de SQL Server pour optimiser les performances en réduisant les mises à jour inutiles de la table TrackingInsert.
Composants clés :

- Procédure stockée UpdateTrackingInsert
- Déclencheurs pour chaque table surveillée
- Variables de contexte de session pour stocker la dernière date d'insertion pour chaque table au sein d'une session

# Solution 2 : approche de mise à jour directe
Cette solution met à jour directement la table TrackingInsert pour chaque insertion, garantissant ainsi que les informations de suivi sont toujours à jour.
Composants clés :

- Procédure stockée UpdateTrackingInsert
- Déclencheurs pour chaque table surveillée

# Solution 3 : approche d'analyse du journal des transactions
Cette solution avancée en utilisant transactionnal LOG de SQL Server pour suivre les insertions dans toutes les tables sans nécessiter de déclencheurs individuels, on doit ajouter des modification et executer la procedure chaque fois puisque le transactionnal Log ne garde pas l'historique pour longtemps.
Composants clés :

Procédure stockée UpdateTrackingInsert
Utilise sys.fn_dblog pour analyser le journal des transactions
Mise à jour de la table TrackingInsert en fonction du transactionnal LOG 

# Comparaison des solutions

- Performances :

Solution 1 : efficace pour plusieurs insertions au sein d'une session.
Solution 2 : exécute une écriture pour chaque insertion, ce qui peut avoir un impact sur les performances.
Solution 3 : analyse périodiquement le LOG, offrant potentiellement de meilleures performances pour les scénarios à volume élevé.

- Complexité :

Solution 1 : complexité modérée avec utilisation du contexte de session.
Solution 2 : implémentation simple avec mises à jour directes.
Solution 3 : la plus complexe, nécessitant une analyse du LOG des transactions mais offrant un suivi complet.

- Évolutivité :

Solutions 1 et 2 : nécessitent des déclencheurs individuels pour chaque table.
Solution 3 : suit automatiquement toutes les tables sans avoir besoin de déclencheurs individuels don c'est plus pratique meme si on doit ajouter des modification et executer la procedure chaque fois puisque le transactionnal Log ne garde pas l'historique pour longtemps.
