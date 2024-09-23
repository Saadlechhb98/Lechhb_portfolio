import pyodbc
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import os
import base64

def encrypt_rib(rib, key):
    if len(key) != 32:
        raise ValueError(f"La clé doit faire exactement 32 octets. Longueur actuelle : {len(key)} octets")
    
    print(f"Longueur de la clé (en octets): {len(key)}")
    print(f"Clé (en hexadécimal): {key.hex()}")
    
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(rib.encode()) + padder.finalize()
    ct = encryptor.update(padded_data) + encryptor.finalize()
    return base64.b64encode(iv + ct).decode('utf-8')

conn_str = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=ribdatabase;UID=;PWD='
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

key = b'12345678901234567890123456789012'
print(f"Longueur de la clé définie (en octets): {len(key)}")
print(f"Clé définie (en texte): {key.decode('utf-8', errors='replace')}")
print(f"Clé définie (en hexadécimal): {key.hex()}")

if len(key) != 32:
    raise ValueError(f"La clé doit faire exactement 32 octets. Longueur actuelle : {len(key)} octets")

try:
    # Lire les RIB non chiffrés
    cursor.execute("SELECT ID, RIB FROM RIBAccounts WHERE EncryptedRIB IS NULL")
    ribs = cursor.fetchall()

    print(f"Nombre de RIB à chiffrer: {len(ribs)}")

    # Chiffrer et mettre à jour
    for id, rib in ribs:
        print(f"Chiffrement du RIB pour ID {id}: {rib}")
        encrypted_rib = encrypt_rib(rib, key)
        cursor.execute("UPDATE RIBAccounts SET EncryptedRIB = ? WHERE ID = ?", (encrypted_rib, id))
        print(f"RIB chiffré pour ID {id}")

    conn.commit()
    print("Tous les RIB ont été chiffrés avec succès.")

except Exception as e:
    conn.rollback()
    print(f"Une erreur s'est produite lors du chiffrement : {str(e)}")
    print(f"Type d'erreur : {type(e)}")
    import traceback
    print("Traceback complet:")
    print(traceback.format_exc())

finally:
    cursor.close()
    conn.close()
