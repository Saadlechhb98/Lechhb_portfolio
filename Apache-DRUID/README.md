![Capture d'écran 2024-08-27 230216](https://github.com/user-attachments/assets/aec023f7-825f-4baf-9972-60c949cfb3d3)

# Description du projet:
Ce projet vise à mettre en place un pipeline de données efficace et en temps réel. Il extrait des données de SQL server, les traite via Apache NiFi, puis les envoie à Apache Druid pour le stockage et l'analyse. Enfin, les données sont visualisées dans Power BI. Le système est conçu pour être réactif, mettant à jour automatiquement les données dans Druid chaque fois que de nouvelles informations sont ajoutées à la table source dans SQL Server. Cette architecture permet une analyse de données rapide et flexible, idéale pour les tableaux de bord en temps réel et les applications analytiques à grande échelle. Par exemple, pour une société financière ou une équipe de conformité, ce système pourrait être crucial pour surveiller en temps réel les transactions suspectes ou les violations potentielles de la réglementation. Les équipes de conformité pourraient ainsi réagir immédiatement aux alertes générées, visualiser les tendances sur des tableaux de bord Power BI constamment mis à jour.

# Qu'est-ce que Druid ?
Apache Druid est une base de données conçue pour une ingestion rapide des données et des requêtes à faible latence. Il est particulièrement adapté aux applications d'analyse OLAP (Online Analytical Processing) qui nécessitent un accès rapide à de grands volumes de données. Druid excelle dans les scénarios où les données sont constamment mises à jour et où les utilisateurs ont besoin d'effectuer des analyses interactives sur des données à la fois historiques et en temps réel.

# Qu'est-ce qui rend Druid rapide ?
Plusieurs facteurs contribuent à la vitesse de Druid. Premièrement, son architecture de stockage en colonnes permet de lire uniquement les données nécessaires pour répondre à une requête spécifique, réduisant ainsi la quantité de données à traiter. Deuxièmement, Druid utilise des agrégations pré-calculées et des index bitmap pour accélérer les requêtes courantes. Troisièmement, sa capacité à stocker les données en mémoire pour les requêtes fréquentes réduit considérablement les temps d'accès. Enfin, l'architecture distribuée de Druid permet une scalabilité horizontale, ce qui signifie que la performance peut être augmentée simplement en ajoutant plus de nœuds au cluster.
Il faut ajouter également le role que joue la column temporelle (column date), elle permet à Druid de partitionner efficacement les données en segments temporels, facilitant ainsi une sélection rapide des données pertinentes lors des requêtes. Cette organisation temporelle optimise les opérations de filtrage, d'agrégation et de comparaison basées sur le temps, qui sont fréquentes dans les analyses de données. De plus, elle facilite la mise en place de stratégies de rétention et de gestion du cycle de vie des données, contribuant à maintenir des performances élevées en gardant les données les plus pertinentes facilement accessibles. L'indexation temporelle basée sur cette colonne accélère considérablement les requêtes, réduisant la latence pour de nombreuses opérations analytiques courantes. 

# Implementation
Notre approche de réalisation de ce projet d'intégration de données a suivi plusieurs étapes :

1- creation Database Connections: Tout d'abord, nous devons configurer les connexions à la base de données dans NiFi.

```sh
Controller Service Type: DBCPConnectionPool
Database Connection URL: jdbc:sqlserver://[source_server]:[port];databaseName=[source_db]
Database Driver Class Name: com.microsoft.sqlserver.jdbc.SQLServerDriver
Database Driver Location(s): [path to sqljdbc4.jar]
Database User: [sourcedb_username]
Password: [sourcedb_password]
```
2- QueryDatabaseTable:
Ce processeur requette la table spécifiée dans la base de données source
```sh
Database Connection Pooling Service: source database connection.
Database Type: Microsoft SQL Server
Table Name: facturation
Columns to Return: List columns (nid, nshopid, dinsertion, sbillerid, namount, last_updated)
Output Format: Avro
```
3- ConvertRecord :
Convertire les données extraites en format JSON pour etre compatible avec type format accepter par druid. Il prend les données au format avro (sortie  de QueryDatabaseTable) et les convertit en JSON.
```sh 
Record Reader : AvroReader
Record Writer :JsonRecordSetWriter
```
4- UpdateAttribute:
Ajoute des attributs dans le FlowFile, comme le nom de la table Druid cible.
```sh
druid.datasource = FACTURATION1
```
5- JoltTransformJSON 
Transforme la structure du JSON pour correspondre au format attendu par Druid
```sh
jolt specification : [
  {
    "operation": "shift",
    "spec": {
      "*": "&"
    }
  },
  {
    "operation": "default",
    "spec": {
      "dataSource": "${druid.datasource}"
    }
  }
]
```
6- Invoke http:
Envoie une requête HTTP (généralement POST) à l'API Druid pour insérer les données
```sh
Properties:
  HTTP URL: http://172.22.0.6:8888/druid/v2/sql
  HTTP Method: POST
  Content-Type: application/json
  Send Message Body: true
  Request Multipart Form-Data Name:
    {
      "query": "INSERT INTO ${druid.datasource} SELECT * FROM (VALUES(${nid}, ${nshopid}, TIMESTAMP '${dinsertion}', ${sbillerid}, ${namount}))",
      "parameters": [
        { "type": "VARCHAR", "value": "${nid}" },
        { "type": "VARCHAR", "value": "${nshopid}" },
        { "type": "VARCHAR", "value": "${dinsertion}" },
        { "type": "VARCHAR", "value": "${sbillerid}" },
        { "type": "DOUBLE", "value": "${namount}" }
      ] }
```
Avant tous cela on doit cree la table en druid, et inserer manuellemnt une ligne lors de la creation de la table puisque druid ne permet pas une creation de table vide 
```sh
{
  "type": "index_parallel",
  "spec": {
    "dataSchema": {
      "dataSource": "FACTURATION1",
      "timestampSpec": {
        "column": "dinsertion",
        "format": "auto"
      },
      "dimensionsSpec": {
        "dimensions": [
          "nid",
          "nshopid",
          "sbillerid"
        ]
      },
      "metricsSpec": [
        { "type": "doubleSum", "name": "namount", "fieldName": "namount" }
      ]
    },
    "ioConfig": {
      "type": "index_parallel",
      "inputSource": {
        "type": "inline",
        "data": "{\"nid\":\"1\",\"nshopid\":\"SHOP001\",\"dinsertion\":\"2024-08-28T12:00:00Z\",\"sbillerid\":\"BILL001\",\"namount\":100.50}\n"
      },
      "inputFormat": {
        "type": "json"
      }
    },
    "tuningConfig": {
      "type": "index_parallel",
      "partitionsSpec": {
        "type": "dynamic"
      }
    }
  }
}
```

# Résultat:
<img width="353" alt="tabledruid" src="https://github.com/user-attachments/assets/e48d0549-9b60-4464-b13f-a007356f536a">
