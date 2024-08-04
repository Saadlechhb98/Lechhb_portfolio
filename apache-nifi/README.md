# ETL - APACHE-NIFI
Ce projet vise à développer une solution robuste d'intégration et warehousing de données à l'aide d'Apache NiFi, un outil d'intégration de données puissant et évolutif. L'objectif principal est de créer un système efficace et automatisé permettant d'extraire des données de plusieurs tables sources dans une base de données SQL Server, de transformer ces données si nécessaire et de les charger dans les tables de destination correspondantes dans un environnement d'entrepôt de données, outre cela chaque modification de données dans la source sera capture et executer dans la destination. Ce processus, communément appelé ETL (Extract, Transform, Load), est essentiel pour les entreprises qui cherchent à consolider et à analyser efficacement leurs données.

Le projet aborde plusieurs défis clés en matière d'intégration de données, notamment le chargement incrémentiel des données, la transformation des données et le maintien de la cohérence des données entre différents systèmes.

Les données sources proviennent de diverses tables opérationnelles, chacune représentant différents aspects de l'entreprise, tels que les informations sur les produits, les détails de la boutique, les transactions financières et les recharges des clients, il s'agit du meme modèle utilisés dans le project Airflow.

NiFi est plus faisable que Airflow pour les projets ETL car il permet de créer des flux de données complexes sans écrire de code, grâce à son interface visuelle intuitive, contrairement à Airflow qui nécessite souvent des scripts Python pour définir les tâches et les workflows. De plus, NiFi offre des fonctionnalités intégrées pour la gestion des données en temps réel et le traitement des flux, simplifiant ainsi la synchronisation et la transformation des données.

# Implementation
Notre approche de réalisation de ce projet d'intégration de données a suivi plusieurs étapes :

1- creation Database Connections:
Tout d'abord, nous devons configurer les connexions à la base de données dans NiFi. Cela implique la création de deux controller services : un pour la base de données source et un autre pour l'entrepôt de données de destination.
```sh
Controller Service Type: DBCPConnectionPool
Database Connection URL: jdbc:sqlserver://[source_server]:[port];databaseName=[source_db]
Database Driver Class Name: com.microsoft.sqlserver.jdbc.SQLServerDriver
Database Driver Location(s): [path to sqljdbc4.jar]
Database User: [source_username]
Password: [source_password]
```
2- QueryDatabaseTable:
Ce processeur requette la table spécifiée dans la base de données source. Il utilise la colonne « last_modified » pour récupérer uniquement les enregistrements nouveaux ou mis à jour depuis la dernière exécution, mettant en œuvre une stratégie de chargement incrémentielle. Le paramètre « Maximum-value Columns » lui permet de suivre la dernière valeur « last_modified » traitée, garantissant ainsi que les exécutions suivantes récupèrent uniquement les données les plus récentes.
```sh
Database Connection Pooling Service: source database connection.
Database Type: Microsoft SQL Server
Table Name: Name of the source table (product, facturation, shops, etc.)
Columns to Return: List of columns to fetch (nid, sname, last_modified)
Maximum-value Columns: last_modified
Output Format: Avro
```
