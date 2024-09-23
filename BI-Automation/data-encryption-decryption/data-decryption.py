import csv
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import base64
from datetime import date

def decrypt_rib(encrypted_rib, key):
    if len(key) != 32:
        raise ValueError(f"La clé doit faire exactement 32 octets. Longueur actuelle : {len(key)} octets")
    
    encrypted_data = base64.b64decode(encrypted_rib)
    iv = encrypted_data[:16]
    ct = encrypted_data[16:]
    
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(ct) + decryptor.finalize()
    
    unpadder = padding.PKCS7(128).unpadder()
    data = unpadder.update(padded_data) + unpadder.finalize()
    
    return data.decode('utf-8')

# Chemin du fichier CSV d'entrée
input_file = r'C:\Users\ELITEBOOK\Downloads\datadatadata.csv'

# Générer le nom du fichier de sortie avec la date d'aujourd'hui
today = date.today().strftime("%Y%m%d")
output_file = rf'C:\Users\ELITEBOOK\Downloads\datadatadata_{today}.csv'

# Clé de chiffrement (exactement 32 octets pour AES-256)
key = b'12345678901234567890123456789012'

try:
    with open(input_file, 'r', newline='', encoding='utf-8-sig') as infile:
        # Lire les 5 premières lignes pour le débogage
        print("Contenu des 5 premières lignes du fichier:")
        for i, line in enumerate(infile):
            if i < 5:
                print(f"Ligne {i+1}: {line.strip()}")
            else:
                break
        infile.seek(0)  # Revenir au début du fichier

        reader = csv.reader(infile)
        headers = next(reader, None)
        
        print(f"En-têtes détectés: {headers}")
        
        if not headers:
            raise ValueError("Le fichier CSV est vide ou n'a pas d'en-tête.")
        
        # Trouver les index des colonnes de manière insensible à la casse
        id_index = next((i for i, h in enumerate(headers) if h.lower() == 'id'), None)
        encrypted_index = next((i for i, h in enumerate(headers) if h.lower() == 'encryptedrib'), None)
        
        print(f"Index de la colonne 'id': {id_index}")
        print(f"Index de la colonne 'encryptedrib': {encrypted_index}")
        
        if id_index is None or encrypted_index is None:
            raise ValueError("Les colonnes 'id' et 'encryptedrib' sont requises dans le fichier CSV.")
        
        with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.writer(outfile)
            writer.writerow(headers + ['DecryptedRIB'])
            
            for row in reader:
                try:
                    id_value = row[id_index]
                    encrypted_rib = row[encrypted_index]
                    decrypted_rib = decrypt_rib(encrypted_rib, key)
                    row.append(decrypted_rib)
                    writer.writerow(row)
                    print(f"ID: {id_value}, RIB déchiffré: {decrypted_rib}")
                except Exception as e:
                    print(f"Erreur lors du déchiffrement du RIB avec ID {id_value}: {str(e)}")
                    row.append('ERREUR DE DÉCHIFFREMENT')
                    writer.writerow(row)

    print(f"Déchiffrement terminé. Résultats sauvegardés dans {output_file}")

except Exception as e:
    print(f"Une erreur s'est produite : {str(e)}")
    import traceback
    print("Traceback complet:")
    print(traceback.format_exc())
