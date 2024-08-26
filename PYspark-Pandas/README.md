![Capture d'écran 2024-08-26 163112](https://github.com/user-attachments/assets/9d2768be-d35f-4c93-8719-1baf14cc20c9)

# PySpark | ETL
PySpark est une API Python pour Apache Spark. Apache Spark est un moteur d'analyse pour le traitement de données à grande échelle. C'est un moteur de traitement de données distribué, ce qui signifie qu'il s'exécute sur un cluster. Un cluster est composé de trois nœuds (ou ordinateurs) ou plus. Spark est écrit en Scala, mais il fournit des API pour d'autres langages courants tels que Java, Python et R - PySpark est l'API Python. Il prend également en charge d'autres outils et langages, notamment Spark SQL pour SQL, l'API pandas sur Spark pour les charges de travail pandas et Structured Streaming pour le calcul incrémentiel et le traitement de flux.

# ER Diagrame:
![Capture d'écran 2024-08-26 164011](https://github.com/user-attachments/assets/1a973dd4-871c-4ade-b78e-63d5ee26a064)

# Présentation du projet
Le modèle relationnel présenté comprend plusieurs tables interconnectées pour représenter différentes entités et leurs relations dans le contexte d'un système de gestion de téléphonie mobile, en effet il s'agit du meme modèle utilisés dans le project SQL-Telecom-Database. La table "department" contient les informations sur les départements de l'entreprise, tandis que la table "worklocation" représente les lieux de travail des employés. Les employés sont stockés dans la table "employee" avec leurs informations personnelles et leur département associé. La table "employeeworklocation" est une table de liaison entre les employés et leurs lieux de travail.

Les vendeurs sont représentés dans la table "salesperson", liée à la table "employee". Les clients sont stockés dans la table "customer" avec leurs informations personnelles et leur vendeur associé. Les commandes passées par les clients sont enregistrées dans la table "orders". Les détails des forfaits téléphoniques sont stockés dans les tables "planinclusions" et "plans", tandis que les informations de facturation sont enregistrées dans la table "billinginformation".

Les numéros de téléphone associés aux comptes clients sont stockés dans la table "phonenumber", liée à la table "billinginformation". Les détails des appels téléphoniques sont enregistrés dans la table "callrecords", associée à la table "phonenumber". Les informations de salaire des employés sont stockées dans la table "salary", liée à la table "department". Les informations sur les cartes SIM des clients sont stockées dans la table "simdata", liée aux tables "customer", "phonenumber" et "plans". Enfin, la table "tracking" permet de suivre l'état des commandes, en lien avec la table "orders".
