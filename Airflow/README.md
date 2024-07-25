# ETL-AIRFLOW-SCD 
Utilisation d'un Data Warehouse dans un cadre ETL
Dans un contexte ETL (Extract, Transform, Load), l'utilisation d'un data warehouse est cruciale pour plusieurs raisons :

  1- Séparation des environnements : Un data warehouse permet de travailler sur les données sans impacter les bases de données de production. Cela préserve l'intégrité et les performances des systèmes opérationnels.
  
  2- Optimisation pour l'analyse : Contrairement aux bases de données de production, un data warehouse est conçu pour l'analyse et le reporting, offrant de meilleures performances puisque lorsque les données sont réparties sur différentes instances et serveurs, il est impossible d'appliquer des jointures. En combinant les données en un seul endroit, nous pouvons effectuer des jointures plus facilement et répondre plus efficacement aux besoins analytiques.
  
  3-Intégration de données : Il permet de centraliser des données provenant de diverses sources, facilitant ainsi leur analyse globale.
  
  4-Historisation : Un data warehouse est idéal pour stocker l'historique des données, ce qui est essentiel pour l'analyse des tendances et l'évolution dans le temps. En effet, l'objectif initial est de conserver l'historique afin d'avoir une vue sur les tendances et d'extraire des informations permettant de prendre des décisions importantes.
  

# Notre cas d'étude

Dans notre configuration, nous avons 6 tables réparties sur différentes instances :

  * Machine locale :

    trx,
    
    facturation,
    
    Data Warehouse (contenant des copies de toutes les tables vides)


  * Instance GCP 1 :

    city,
    
    recharge,


  * Instance GCP 2 :

    product,
    
    shop,
<img width="860" alt="Capture d’écran 2024-07-23 152929" src="https://github.com/user-attachments/assets/aca11964-20d1-4e4c-9fe9-cac8e8a72870">


Cette architecture distribuée nécessite un data warehouse centralisé pour faciliter l'analyse et le reporting sur l'ensemble des données.

# Script 1 : Chargement incrémental multi-instances

Ce script Airflow réalise un chargement incrémental de données depuis plusieurs serveurs SQL vers un data warehouse SQL Server centralisé.

- Comment ce mecanisme foctionnera

  Ce script vérifie si la table cible est vide ou remplie. Si elle est vide, il enchaîne vers le chargement initial où il charge la totalité des données vers la table de destination. S'il trouve que la table de       
  destination est remplie, il prend la valeur maximale de la clé primaire, puis extrait les données de la table source où la clé primaire est plus grande que l'ID maximal de la table de destination. Ensuite, après 
  avoir extrait les données, on les charge vers la table de destination.

- Visualtisation des resultats

![Capture d'écran 2024-07-23 153339](https://github.com/user-attachments/assets/39539166-2a06-4b07-a537-45123bb351be)
![Capture d'écran 2024-07-23 153744](https://github.com/user-attachments/assets/6aa8cb96-7ba6-4f18-b57d-46cb37b260f5)

- Etat final d'une table (echantillon)

  ![Capture d'écran 2024-07-25 165207](https://github.com/user-attachments/assets/097ce944-54dd-4458-98bc-5ee855f0f8d4)

  
# Script 2 : Chargement avec Slowly Changing Dimension (SCD) Type 2

Ce script implémente un processus ETL utilisant la technique SCD Type 2 pour capturer l'historique des changements dans les données dimensionnelles.

- Comment ce mecanisme foctionnera

  * Nous chargeons les données actuelles (actives) de la table cible (où flag = 1).
  * Nous fusionnons ces données actuelles avec les nouvelles données provenant de la source, en utilisant 'nid' comme clé. La fusion 'right' garantit que nous conservons tous les nouveaux enregistrements, même s'ils        n'existent pas dans les données actuelles.
  * Nous comparons ensuite chaque colonne des données fusionnées, à l'exclusion de la colonne 'nid'. Si des valeurs de colonne sont différentes entre les données actuelles et les nouvelles données, nous considérons cet     enregistrement comme modifié.
    
- Visualisation des resultats
  ![Capture d'écran 2024-07-23 154246](https://github.com/user-attachments/assets/6f3a4f1d-3887-4655-9be2-00f6729e14cd)

- Etat final d'une table (echantillon)
  ![Capture d'écran 2024-07-23 210514](https://github.com/user-attachments/assets/a0a01e63-fac5-4ebb-a9ee-486eba1264cd)

- Cependant, cette méthode présente des inconvénients. Il y a quelques points à considérer, premièrement, la performance. Cette méthode charge toutes les données actuelles en mémoire, ce qui peut poser problème pour les très grandes tables. Deuxièmement, la précision. Elle compare toutes les colonnes, ce qui n'est pas toujours nécessaire. Certaines colonnes peuvent être autorisées à changer sans créer une nouvelle version.Donc nous devons voir d'autre altenative.

# Script 3 : SCD Type 2 avec suivi par horodatage ( last_updated timestamp)

Ce script combine la technique SCD Type 2 avec un suivi des mises à jour basé sur les horodatages pour optimiser le processus ETL.

- Comment ce mecanisme foctionnera

  * Utilisation d'une colonne 'last_updated' et d'une variable Airflow pour le suivi
  * Extraction et traitement des seuls enregistrements modifiés depuis la dernière exécution
  * Conservation de l'historique avec SCD Type 2

- Visualisation des résultats
  ![Capture d'écran 2024-07-23 154459](https://github.com/user-attachments/assets/c2832a15-c835-4e0e-9c10-ee2e39a9ed6f)

- Etat final d'une table (echantillon)
  ![Capture d'écran 2024-07-23 211552](https://github.com/user-attachments/assets/bbaa0b6e-3d4c-4f76-8ca2-486c292e26d6)
  
- L'utilisation d'un horodatage "last_updated" dans la source et la comparaison uniquement des enregistrements qui ont été mis à jour depuis la dernière exécution de l'ETL .C'est plus efficace que de charger et de comparer toutes les données à chaque fois.
# Script 4 : SCD Type 2 avec détection des modifications par checksum

Ce script utilise la technique SCD Type 2 avec une détection des modifications basée sur le calcul de checksums pour optimiser le processus ETL.

- Comment ce mecanisme foctionnera

  * Calcul de checksums sur des colonnes spécifiques pour chaque table
  * Détection efficace des enregistrements modifiés
  * Traitement par lots pour améliorer les performances

- Visualisation des résultats
  ![Capture d'écran 2024-07-23 154038](https://github.com/user-attachments/assets/7d6507a3-1999-44a5-8816-99d6c4a7c382)

- Etat final d'une table (echantillon)
  ![Capture d'écran 2024-07-23 211616](https://github.com/user-attachments/assets/eeb7af3d-ec8f-4e21-a032-bd4e3820d7d9)

  Avec CHECKSUM, nous n'avons pas besoin de charger que la valeur de hachage pour chaque ligne, plutôt que toutes les colonnes. Cela réduit considérablement la quantité de données à charger en mémoire
