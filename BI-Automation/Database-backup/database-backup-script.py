import os
from datetime import datetime
import pymssql
from minio import Minio
from minio.error import S3Error

# SQL Server configuration
SQL_SERVER = "[servername]"
SQL_USERNAME = "[user]"
SQL_PASSWORD = "[pswd]"
DATABASES = ["tooday", "telecom2"]

# MinIO configuration
MINIO_ENDPOINT = "localhost:9000"
MINIO_ACCESS_KEY = "[access-key]"
MINIO_SECRET_KEY = "[secret-key]"
MINIO_BUCKET_1 = "data-lake-st1"
MINIO_BUCKET_2 = "data-lake-st2"

# Backup configuration
BACKUP_DIR = r"[localpath]"
FULL_BACKUP_DAY = 6  # dimanche (0 est lundi, 6 c'est dimanche)
DIFF_BACKUP_HOURS = [0, 6, 12, 18]  # heures for differential backups

if not os.path.exists(BACKUP_DIR):
    try:
        os.makedirs(BACKUP_DIR)
        print(f"Created backup directory: {BACKUP_DIR}")
    except Exception as e:
        print(f"Failed to create backup directory: {e}")
        raise

def connect_to_sql_server():
    try:
        conn = pymssql.connect(SQL_SERVER, SQL_USERNAME, SQL_PASSWORD, autocommit=True)
        print(f"Successfully connected to SQL Server: {SQL_SERVER}")
        return conn
    except Exception as e:
        print(f"Failed to connect to SQL Server: {e}")
        raise

def connect_to_minio():
    try:
        minio_client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False
        )
        print(f"Successfully connected to MinIO: {MINIO_ENDPOINT}")
        return minio_client
    except Exception as e:
        print(f"Failed to connect to MinIO: {e}")
        raise

def perform_backup(db_name, backup_type):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"{db_name}_{backup_type}_{timestamp}.bak")
    
    conn = connect_to_sql_server()
    cursor = conn.cursor()
    
    if backup_type == "FULL":
        backup_sql = f"BACKUP DATABASE [{db_name}] TO DISK = '{backup_file}' WITH INIT"
    elif backup_type == "DIFF":
        backup_sql = f"BACKUP DATABASE [{db_name}] TO DISK = '{backup_file}' WITH DIFFERENTIAL"
    
    try:
        cursor.execute(backup_sql)
        print(f"Successfully created {backup_type} backup for {db_name}: {backup_file}")
    except Exception as e:
        print(f"Failed to create {backup_type} backup for {db_name}: {e}")
        raise
    finally:
        cursor.close()
        conn.close()
    
    return backup_file

def upload_to_minio(file_path, bucket):
    minio_client = connect_to_minio()
    file_name = os.path.basename(file_path)
    
    try:
        minio_client.fput_object(bucket, file_name, file_path)
        print(f"Successfully uploaded '{file_name}' to MinIO bucket '{bucket}'")
    except S3Error as e:
        print(f"Error uploading '{file_name}' to MinIO bucket '{bucket}': {e}")
        raise

def should_run_backup():
    now = datetime.now()
    if now.weekday() == FULL_BACKUP_DAY and now.hour == 0:  
        return "FULL"
    elif now.hour in DIFF_BACKUP_HOURS:
        return "DIFF"
    return None

def main():
    print("Starting backup process")
    backup_type = should_run_backup()
    
    if not backup_type:
        print("No backup scheduled for this time. Exiting.")
        return

    try:
        for db in DATABASES:
            print(f"Processing db: {db}")
            
            backup_file = perform_backup(db, backup_type)
            
            upload_to_minio(backup_file, MINIO_BUCKET_1)
            upload_to_minio(backup_file, MINIO_BUCKET_2)
        
        print("Backup process completed successfully")
    except Exception as e:
        print(f"Backup process à echoué: {e}")

if __name__ == "__main__":
    main()