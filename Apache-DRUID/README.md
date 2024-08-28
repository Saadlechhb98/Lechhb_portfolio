![Capture d'écran 2024-08-27 230216](https://github.com/user-attachments/assets/aec023f7-825f-4baf-9972-60c949cfb3d3)

# Description du projet:
Ce projet vise à mettre en place un pipeline de données efficace et en temps réel. Il extrait des données de SQL server, les traite via Apache NiFi, puis les envoie à Apache Druid pour le stockage et l'analyse. Enfin, les données sont visualisées dans Power BI. Le système est conçu pour être réactif, mettant à jour automatiquement les données dans Druid chaque fois que de nouvelles informations sont ajoutées à la table source dans SQL Server. Cette architecture permet une analyse de données rapide et flexible, idéale pour les tableaux de bord en temps réel et les applications analytiques à grande échelle. Par exemple, pour une société financière ou une équipe de conformité, ce système pourrait être crucial pour surveiller en temps réel les transactions suspectes ou les violations potentielles de la réglementation. Les équipes de conformité pourraient ainsi réagir immédiatement aux alertes générées, visualiser les tendances sur des tableaux de bord Power BI constamment mis à jour.

# Qu'est-ce que Druid ?
Apache Druid est une base de données conçue pour une ingestion rapide des données et des requêtes à faible latence. Il est particulièrement adapté aux applications d'analyse OLAP (Online Analytical Processing) qui nécessitent un accès rapide à de grands volumes de données. Druid excelle dans les scénarios où les données sont constamment mises à jour et où les utilisateurs ont besoin d'effectuer des analyses interactives sur des données à la fois historiques et en temps réel.

# Qu'est-ce qui rend Druid rapide ?
Plusieurs facteurs contribuent à la vitesse de Druid. Premièrement, son architecture de stockage en colonnes permet de lire uniquement les données nécessaires pour répondre à une requête spécifique, réduisant ainsi la quantité de données à traiter. Deuxièmement, Druid utilise des agrégations pré-calculées et des index bitmap pour accélérer les requêtes courantes. Troisièmement, sa capacité à stocker les données en mémoire pour les requêtes fréquentes réduit considérablement les temps d'accès. Enfin, l'architecture distribuée de Druid permet une scalabilité horizontale, ce qui signifie que la performance peut être augmentée simplement en ajoutant plus de nœuds au cluster.
Il faut ajouter également le role que joue la column temporelle (column date), elle permet à Druid de partitionner efficacement les données en segments temporels, facilitant ainsi une sélection rapide des données pertinentes lors des requêtes. Cette organisation temporelle optimise les opérations de filtrage, d'agrégation et de comparaison basées sur le temps, qui sont fréquentes dans les analyses de données. De plus, elle facilite la mise en place de stratégies de rétention et de gestion du cycle de vie des données, contribuant à maintenir des performances élevées en gardant les données les plus pertinentes facilement accessibles. L'indexation temporelle basée sur cette colonne accélère considérablement les requêtes, réduisant la latence pour de nombreuses opérations analytiques courantes. 