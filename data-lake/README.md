# Data-lake
![Capture d'écran 2024-09-09 104942](https://github.com/user-attachments/assets/4927d4a1-9198-466f-87ff-c18510105bb5)

# Outils utilisés :

- MINIO : un système de stockage d'objets open source compatible avec l'API Amazon S3
- Hive: Gestionnaire de métadonnées
- Trino : Moteur SQL pour interroger avec nos données.

  # Architecture :

  Chaque jour, de nouveaux fichiers CSV contenant les données de six tables différentes provenant de differents sources (transaction, facturation, city, product, shop, recharge) sont stockés dans MinIO, un système de stockage objet.
  Ces fichiers sont organisés dans des répertoires spécifiques pour chaque table, avec les données pour J-1. Hive est utilisé pour définir la structure des tables et gérer les métadonnées,
  créant des schémas et des tables externes qui pointent vers les emplacements correspondants dans MinIO. Trino est de moteur de requête SQL , permettant d'interroger et d'analyser efficacement les données stockées.
