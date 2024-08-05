# ETL - APACHE-NIFI
Ce projet vise à développer une solution robuste d'intégration et warehousing de données à l'aide d'Apache NiFi, un outil d'intégration de données puissant et évolutif. L'objectif principal est de créer un système efficace et automatisé permettant d'extraire des données de plusieurs tables sources dans une base de données SQL Server, de transformer ces données si nécessaire et de les charger dans les tables de destination correspondantes dans un environnement d'entrepôt de données, outre cela chaque modification de données dans la source sera capture et executer dans la destination. Ce processus, communément appelé ETL (Extract, Transform, Load), est essentiel pour les entreprises qui cherchent à consolider et à analyser efficacement leurs données.

Le projet aborde plusieurs défis clés en matière d'intégration de données, notamment le chargement incrémentiel des données, la transformation des données et le maintien de la cohérence des données entre différents systèmes.

Les données sources proviennent de diverses tables opérationnelles, chacune représentant différents aspects de l'entreprise, tels que les informations sur les produits, les détails de shop, les transactions financières et les recharges des clients, il s'agit du meme modèle utilisés dans le project Airflow.

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
3- UpdateRecord:
UpdateRecord nous permet de modifier le contenu des enregistrements. Dans notre exemple avec la table product, nous mettons en majuscule la première lettre de attribue 'sname'. Pour la table 'trx', nous l'utilisons pour remplacer les valeurs NULL de attribue 'nOperationFee' par 0. Ce processeur est crucial pour le nettoyage des données.
```sh
Record Reader: AvroReader
Record Writer: AvroRecordSetWriter
Replacement Value Strategy: Record Path Value
/sname: ${field.value:substring(0,1):toUpper()}${field.value:substring(1):toLower()}
```
4-LookupRecord:
LookupRecord effectue une recherche dans la table de destination pour chaque enregistrement entrant, en utilisant la clé primaire < nid >. Il oriente ensuite l'enregistrement vers « matched » (s'il existe dans la destination) ou « unmatched » (s'il est nouveau). Cela nous permet de faire la différence entre les enregistrements qui doivent être insérés et ceux qui doivent modifiés.
```sh
Record Reader: AvroReader
Record Writer: AvroRecordSetWriter
Lookup Service: DBLookupService (configured to connect to the destination table)
Result RecordPath: /matched
Routing Strategy: Route to 'matched' or 'unmatched'
User-Defined Properties: key: /nid
```
5- UpdateAttribute (pour les nouveau record - unmatched)

6- UpdateAttribute (pour les données modifiées - matched)

7- PutDatabaseRecord (pour INSERT):
Ce processeur prend les enregistrements qui ne correspondent pas dans LookupRecord (nouveaux enregistrements) et les insère dans la table de destination. Le mappage de champs garantit que chaque champ de la source est correctement placé dans la colonne correspondante de la table de destination.
```sh
Record Reader: AvroReader
Statement Type: INSERT
Database Connection Pooling Service: Points to the destination database connection
Table Name: Name of the destination table (product_dw)
Field Mapping: Maps fields from the source to the destination (nid:/nid,sname:/sname,last_modified:/last_modified,dw_insert_date:/dw_insert_date,dw_update_date:/dw_update_date)
```

8- PutDatabaseRecord (for UPDATE)
Ce processeur prend les enregistrements correspondant à LookupRecord (enregistrements existants) et les met à jour dans la table de destination. Le mappage de champs spécifie les champs à mettre à jour et le paramètre « Mettre à jour les clés » indiquant ainsi le champ à utiliser pour identifier l'enregistrement à mettre à jour.
```sh
Record Reader: AvroReader
Statement Type: UPDATE
Database Connection Pooling Service: Points to the destination database connection
Table Name: Name of the destination table (product_dw)
Field Mapping: Maps fields to be updated (sname:/sname,last_modified:/last_modified,dw_update_date:/dw_update_date)
Update Keys: nid
```
Ces processeurs, lorsqu'ils sont connectés dans le bon ordre, forment un pipeline ETL complet. Ils extraient les données de la source, les transforment si nécessaire, déterminent si chaque enregistrement est nouveau ou existant, puis insèrent ou mettent à jour les enregistrements dans l'entrepôt de données de destination. Cette configuration garantit un chargement efficace et incrémentiel des données tout en préservant l'intégrité des données et en suivant les modifications au fil du temps.

# Zoom sur application du processus sur chaque table
- tables [facturation,shop,city,recharge,product,trx] - destination ( echantillon ):

![Capture d'écran 2024-08-05 105650](https://github.com/user-attachments/assets/9437190e-108f-45f4-bd83-daa090b06821)

![Capture d'écran 2024-08-05 110243](https://github.com/user-attachments/assets/448f4d68-6230-4f86-be48-c7a59b4aeb30)

![Capture d'écran 2024-08-05 110312](https://github.com/user-attachments/assets/b5b8a3c8-280a-4c0e-b0b3-cfb5886f08c7)

![Capture d'écran 2024-08-05 110326](https://github.com/user-attachments/assets/1d645b27-efad-4f98-bce2-94194f68782e)

![Capture d'écran 2024-08-05 110352](https://github.com/user-attachments/assets/51a4228c-8324-4db3-96a3-37b25a765449)

![Capture d'écran 2024-08-05 110435](https://github.com/user-attachments/assets/f1bd0cd8-7c8f-49ca-aaf6-ff09ec1d271b)

On constate que les données ont été efficacement transférées de la base de données transactionnelle vers le data warehouse, plus précisément dans les tables de destination correspondantes. Ce processus d'ETL (Extract, Transform, Load) ne se limite pas à un transfert ponctuel, mais fonctionne de manière continue et en temps réel. Ainsi, chaque nouvelle donnée insérée dans la base transactionnelle est automatiquement capturée et transmise vers le data warehouse. De même, toute modification apportée aux données existantes dans la base transactionnelle est immédiatement reflétée dans le data warehouse. Cette synchronisation en temps réel assure que le data warehouse maintient constamment une image à jour et fidèle des données opérationnelles, permettant ainsi des analyses et des prises de décision basées sur les informations les plus récentes.

