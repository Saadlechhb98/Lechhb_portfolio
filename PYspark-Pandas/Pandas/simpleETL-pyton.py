import pandas as pd
import pyodbc
from sqlalchemy import create_engine
import os
from datetime import datetime

# Connexion à la base de données source
connect_to_source = pyodbc.connect("Driver={ODBC Driver 17 for SQL Server};"
                                   "Server=localhost;"
                                   "PORT=1433;"
                                   "Database=[database];"
                                   "UID=[username];"
                                   "PWD=[password];")

# Connexion à la base de données destination
connect_to_destination = pyodbc.connect("Driver={ODBC Driver 17 for SQL Server};"
                                        "Server=localhost;"
                                        "port=1433;"
                                        "Database=[database];"
                                        "UID=[username];"
                                        "PWD=[password];")
# Création des engines pour la source et la destination
source_engine = create_engine("mssql+pyodbc://UID:PWD@localhost:1433/telecom2?driver=ODBC+Driver+17+for+SQL+Server")

desti_engine = create_engine("mssql+pyodbc://UID:PWD@localhost:1433/telecom?driver=ODBC+Driver+17+for+SQL+Server")
def extract_load():
    try:
        query = """select t.name as tablename from sys.tables"""
        src_tables = pd.read_sql_query(query, connect_to_source)['tablename']
        
        for table_name in src_tables:
            df=pd.read_sql_query(f"select * from {table_name}",connect_to_source)
            transform_data(df, table_name)
            load(df, table_name)
            
def transform_data(df, table_name):
    # application de transaformation basée sur nom de la table
    if table_name == 'department':
        df=pd.read_sql_query(f"select * from {table_name}",connect_to_source)
        df_dep=df.copy()
        df_dep.rename(column={"salary":"salaire"},inplace=True)
        df_dep=df_dep(["DepartmentName"]).str.title()
        df_dep["salary"]=df_dep["salary"].astype(float)
    elif table_name == 'worklocation':
        df_worklocation=df.copy()
        df_worklocation.loc[df_worklocation['LocationName'] == "Washington DC", 'LocationName'] = 'DC'
    elif table_name == 'employee':
        df_employee=df.copy()
        # Transformation
        df_employee['First_Name'] = df_employee['Employee_Name'].str.split().str[0]
        df_employee['Last_Name'] = df_employee['Employee_Name'].str.split().str[-1]
        df_employee['Age'] = df_employee['Age'].astype(float)
        df_employee['Salary'] = df_employee['Salary'].astype(float)
    #  Dropping Duplicates:
        deduplicated_df = df.drop_duplicates(subset=['EmployeeId'])
    #  Binning:
        bins = [0, 20, 30, 40, 50, float('inf')]
        labels = ['<20', '20-30', '30-40', '40-50', '50+']
        df_employee['Age_Group'] = pd.cut(df_employee['Age'], bins=bins, labels=labels)
    elif table_name == 'customer':
        df_customer=df.copy()
        # 1. calcul age a partir de l'année de naissance
        df_customer['Ages'] = pd.Timestamp.now().year - pd.to_datetime(df['DateOfBirth']).dt.year

#  convertir Date of Birth - Datetime
        df_customer['annéenaissance'] = pd.to_datetime(df['DateOfBirth']).dt.year

#  Mask Social Security Numbers---------------------------------------------------
        df_customer['Masked_SSN'] = df_customer['SocialSecurityNumber'].apply(lambda s: f"***-**-{str(s)[-4:]}")
   
    elif table_name == 'order':
        df_order=df.copy()
        
        df_order['OrderStatus'] = df_order['OrderStatus'].astype('category')

        #  Handle Missing Values dans la table OrderType
        df_order['OrderType'] = df_order['OrderType'].fillna('Standard')

        # 4. Creation nouvelle column pour Priority Orders----------------------------------------
        df_order['IsPriorityOrder'] = df_order['OrderType'].apply(lambda x: 1 if 'Priority' in x else 0)
    
    elif table_name='planinclusions':
        df_planinclusion=df.copy()


        #  Extraction information Numeric 
        df_planinclusion['Data_MB'] = df_planinclusion['Data'].str.replace('MB', '').astype(int)
        df_planinclusion['Talktime_Minutes'] = df_planinclusion['Talktime'].str.extract('(\d+)').astype(float)
        df_planinclusion['TextMessages_Count'] = df_planinclusion['TextMessages'].astype(int)

        #  convertir Text Information - Standard Units
        df_planinclusion['Talktime_Minutes'] = df_planinclusion.apply(lambda row: row['Talktime_Minutes'] * 60 if 'Hours' in row['Talktime'] else row['Talktime_Minutes'], axis=1)
        df_planinclusion['Talktime_Minutes'] = df_planinclusion['Talktime_Minutes'].apply(lambda row: row * 60 if 'Hours' in row['Talktime'] else row['Talktime_Minutes'], axis=1)

        #  combiner Data et Units into dans une seule Column
        df_planinclusion['Data_with_Unit'] = df['Data_MB'].astype(str) + ' MB'
        df_planinclusion['Talktime_with_Unit'] = df_planinclusion['Talktime_Minutes'].astype(str) + ' Minutes'

    elif table_name='plans':
        df_plans=df.copy

        df_plans['PlansType'] = df_plans['PlansType'].astype('category')

        df_plans['PlanName_Numeric'] = df_plans['PlanName'].str.extract('(\d+)').astype(float)

        #  Split PlanName 
        df_plans[['PlanName_Action', 'PlanName_Description']] = df_plans['PlanName'].str.split(n=1, expand=True)

    elif table_name='phonenumber':
        df_phonenumber=df.copy

        df_phonenumber['Masked_PhoneNumber'] = df_phonenumber['PhoneNumber'].apply(lambda x: str(x)[:-4] + '****')

        df_phonenumber['AreaCode'] = df_phonenumber['PhoneNumber'].astype(str).str[:3]

        df_phonenumber['NumberLength'] = df_phonenumber['PhoneNumber'].astype(str).apply(len)

        df_phonenumber['IsDuplicate'] = df_phonenumber.duplicated(subset=['PhoneNumber'])
    
    elif table_name='salary':
        df_salary=df.copy()
        df_salary['Bonus'] = df_salary['Salary'] * 0.1

        # convertir Salary en  Salary annuelle
        df_salary['AnnualSalary'] = df_salary['Salary'] * 12

        # Categorize Salary en range
        salary_bins = [0, 3000, 6000, 9000, float('inf')]
        salary_labels = ['Low', 'Medium', 'High', 'Very High']
        df_salary['SalaryRange'] = pd.cut(df_salary['Salary'], bins=salary_bins, labels=salary_labels)

        # Normalizer Salary 
        df_salary['NormalizedSalary'] = (df_salary['Salary'] - df_salary['Salary'].min()) / (df_salary['Salary'].max() - df_salary['Salary'].min())

    elif table_name='simdata':
        df.simdata=df.copy
        # Extraction d'information de SimNumber (Example: extraction  6 premier nombre comme country code)
        df['CountryCode'] = df['SimNumber'].astype(str).str[:6]

        #  Convertire SimType - Categorical
        df['SimType'] = df['SimType'].astype('category')

    return df

def load(df, table_name):
    try:
        row_imported = 0
        desti_engine = create_engine("mssql+pyodbc://", creator=lambda: connect_to_destination)
        print(f'importing rows {row_imported} to {row_imported + len(df)}... for table {tbl}')
        df.to_sql(tbl, desti_engine, if_exists='replace', index=False, chunksize=100000)
        row_imported += len(df)
        print("data imported successful")

    except Exception as e:
        print("data load error", e)

try:
    extract_load()

except Exception as e:
    print("error while extracting data", e)