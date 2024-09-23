# Chiffrement et déchiffrement de données d'une table SQL Server


  # - Introduction
## Objectif:

L'objectif de ce projet est de crypter les données d'une table dans une base de données SQL Server, de les visualiser cryptées dans Power BI, mais de pouvoir les décrypter à l'aide d'un script Python sans se connecter où avoir une interaction avec SQL server. Cela permet de sécuriser les données sensibles tout en étant capable de les exploiter.

Autrement dit, on peut télécharger les données chiffrées sous format CSV et exécuter un script Python pour les déchiffrer. Le premier script Python est responsable d'extraire les données RIB de la base de données source et d'effectuer le chiffrement avec la méthode AES. Quant au deuxième script, il est chargé de lire le fichier CSV et de déchiffrer les données RIB vers un autre fichier CSV de sortie.

## Vue sur l’architecture : 
On va utiliser SQL Server pour le stockage et le chiffrement, Power BI pour la visualisation des données chiffrées en varchar puisque de visualiser les données binaires sur power bi, Python pour le déchiffrement hors-ligne c’est-à-dire sans avoir une liaison avec SQL server.

## Les contraintes du projet :
- Chiffrement des RIB dans SQL Server 
- Visualisation des données chiffrées dans Power BI 
- Déchiffrement en Python sans connexion à SQL Server

## Structure des données :

```sh
CREATE TABLE BankAccounts (
    ID INT PRIMARY KEY,
    RIB VARCHAR(200),
    EncryptedRIB VARBINARY(MAX))
```

## Implémentation de la méthode méthode AES :

Dans un premier temps, nous effectuons une extraction des données depuis SQL Server vers Python, où nous chiffrons ensuite les données, puis nous les renvoyons dans une colonne spécifique des données chiffrées dans SQL Server.

## Visualisation des données sur Power BI :
![Capture d'écran 2024-09-23 161632](https://github.com/user-attachments/assets/ef18c258-6363-4493-a87f-85d9e1314d9d)

## Vérification du déchiffrement des données sur fichier csv

![Capture d'écran 2024-09-23 151902](https://github.com/user-attachments/assets/b9a225ce-c49b-4ae5-8f94-f88a62391d23)

