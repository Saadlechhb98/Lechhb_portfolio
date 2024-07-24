from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.hooks.base import BaseHook
from datetime import datetime, timedelta
import pandas as pd
import sqlalchemy
import logging

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 6, 26),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'incremental_data_load_sql_server_z4',
    default_args=default_args,
    schedule_interval='0 13 * * *',
    catchup=False,
)

def get_engine(conn_id):
    conn = BaseHook.get_connection(conn_id)
    driver = 'ODBC+Driver+17+for+SQL+Server'
    conn_str = f"mssql+pyodbc://{conn.login}:{conn.password}@{conn.host}:{conn.port}/{conn.schema}?driver={driver}"
    return sqlalchemy.create_engine(conn_str)

def check_if_target_is_empty(target_conn_id, target_table, **kwargs):
    target_engine = get_engine(target_conn_id)
    query = f"SELECT COUNT(1) FROM {target_table}"
    result = target_engine.execute(query).fetchone()
    is_empty = result[0] == 0
    kwargs['ti'].xcom_push(key=f'{target_table}_is_empty', value=is_empty)
    logging.info(f"Checked if target table {target_table} is empty: {is_empty}")

def branch_task(ti, target_table, **kwargs):
    is_empty = ti.xcom_pull(key=f'{target_table}_is_empty')
    logging.info(f"Branch decision for {target_table}, is_empty: {is_empty}")
    if is_empty:
        return f'initial_load_{target_table}'
    else:
        return f'get_last_max_id_{target_table}'

def get_last_max_id(target_conn_id, target_table, primary_key, **kwargs):
    target_engine = get_engine(target_conn_id)
    query = f"SELECT ISNULL(MAX({primary_key}), 0) FROM {target_table}"
    result = target_engine.execute(query).fetchone()
    max_id = result[0]
    kwargs['ti'].xcom_push(key=f'{target_table}_max_id', value=max_id)
    logging.info(f"Last max ID for table {target_table}: {max_id}")

def initial_load(source_conn_id, source_table, target_conn_id, target_table, **kwargs):
    source_engine = get_engine(source_conn_id)
    query = f"SELECT * FROM {source_table}"
    df = pd.read_sql(query, source_engine)
    
    df = transform_dataframe(df, source_table)
    
    target_engine = get_engine(target_conn_id)
    df.to_sql(target_table, target_engine, if_exists='append', index=False)
    logging.info(f"Initial load and transformation complete for table {source_table} to {target_table}")

def extract_incremental_data(source_conn_id, source_table, target_conn_id, target_table, primary_key, **kwargs):
    ti = kwargs['ti']
    max_id = ti.xcom_pull(key=f'{target_table}_max_id')
    source_engine = get_engine(source_conn_id)
    query = f"SELECT * FROM {source_table} WHERE {primary_key} > {max_id}"
    logging.info(f"Executing query: {query}")
    df = pd.read_sql(query, source_engine)
    logging.info(f"Query result shape: {df.shape}")
    if df.empty:
        logging.info(f"No new data extracted from table {source_table} with {primary_key} > {max_id}")
    else:
        logging.info(f"Extracted {df.shape[0]} rows of incremental data from table {source_table} with {primary_key} > {max_id}")
        logging.debug(f"Extracted data: {df.to_dict('records')}")
    
    xcom_value = df.to_dict('records')
    ti.xcom_push(key=f'{source_table}_incremental_data', value=xcom_value)
    logging.info(f"Pushed {len(xcom_value)} records to XCom for {source_table}")
    return xcom_value

def transform_dataframe(df, table_name):
    if table_name == 'trx':
        df['nOperationFee'] = df['nOperationFee'].fillna(0)  # Fill NaN in NOPERATIONFEE with 0
    elif table_name == 'shop':
        df['sname'] = df['sname'].str.upper()  # Convert shop names to uppercase
    elif table_name == 'city':
        df['sname'] = df['sname'].str.capitalize()  # Capitalize city names
    
    logging.info(f"Transformed data for {table_name}: {df.to_dict('records')}")
    return df

def transform_data(source_table, target_table, **kwargs):
    ti = kwargs['ti']
    new_data = ti.xcom_pull(task_ids=f'extract_incremental_data_{target_table}', key=f'{source_table}_incremental_data')
    logging.info(f"Pulled {len(new_data) if new_data else 0} records from XCom for {source_table}")
    
    if not new_data:
        logging.info(f"No new data to transform for {source_table}")
        return

    df = pd.DataFrame(new_data)
    logging.info(f"Data before transformation: {df.to_dict('records')}")
    df = transform_dataframe(df, source_table)
    logging.info(f"Data after transformation: {df.to_dict('records')}")
    
    if df.empty:
        logging.info(f"No data after transformation for table {source_table}")
    else:
        logging.info(f"Transformed {df.shape[0]} rows of data for table {source_table}")
    
    transformed_data = df.to_dict('records')
    ti.xcom_push(key=f'{target_table}_transformed_data', value=transformed_data)
    logging.info(f"Pushed {len(transformed_data)} transformed records to XCom for {target_table}")
    return transformed_data

def load_incremental_data(target_conn_id, target_table, **kwargs):
    ti = kwargs['ti']
    new_data = ti.xcom_pull(key=f'{target_table}_transformed_data')
    logging.info(f"Pulled {len(new_data) if new_data else 0} transformed records from XCom for {target_table}")
    
    if not new_data:
        logging.info(f"No new data to load into {target_table}")
        return
    
    df = pd.DataFrame(new_data)
    logging.info(f"Loading {df.shape[0]} rows of data into {target_table}")
    logging.debug(f"Data to be loaded: {df.to_dict('records')}")
    
    target_engine = get_engine(target_conn_id)
    df.to_sql(target_table, target_engine, if_exists='append', index=False)
    logging.info(f"Incremental load complete for table {target_table}")

servers_tables = {
    'sql11': {'trx': 'nid', 'facturation': 'nid'},
    'sql13': {'shop': 'nid', 'recharge': 'nid'},
    'sql12': {'city': 'nid', 'product': 'nid'}
}

for server, tables in servers_tables.items():
    for table, primary_key in tables.items():
        source_conn_id = f'{server}'  # Use just the server name without _source suffix
        target_conn_id = 'sqlsql11'  # Corrected target connection ID for example
        
        target_table = f'stge_{table}'
        
        check_empty_task = PythonOperator(
            task_id=f'check_if_target_is_empty_{target_table}',
            python_callable=check_if_target_is_empty,
            op_args=[target_conn_id, target_table],
            provide_context=True,
            dag=dag,
        )

        branch = BranchPythonOperator(
            task_id=f'branch_task_{target_table}',
            python_callable=branch_task,
            op_kwargs={'target_table': target_table},
            provide_context=True,
            dag=dag,
        )

        initial_load_task = PythonOperator(
            task_id=f'initial_load_{target_table}',
            python_callable=initial_load,
            op_args=[source_conn_id, table, target_conn_id, target_table],
            provide_context=True,
            dag=dag,
        )

        get_max_id_task = PythonOperator(
            task_id=f'get_last_max_id_{target_table}',
            python_callable=get_last_max_id,
            op_args=[target_conn_id, target_table, primary_key],
            provide_context=True,
            dag=dag,
        )

        extract_task = PythonOperator(
            task_id=f'extract_incremental_data_{target_table}',
            python_callable=extract_incremental_data,
            op_args=[source_conn_id, table, target_conn_id, target_table, primary_key],
            provide_context=True,
            dag=dag,
        )

        transform_task = PythonOperator(
            task_id=f'transform_data_{target_table}',
            python_callable=transform_data,
            op_kwargs={'source_table': table, 'target_table': target_table},
            provide_context=True,
            dag=dag,
        )
        
        load_task = PythonOperator(
            task_id=f'load_incremental_data_{target_table}',
            python_callable=load_incremental_data,
            op_args=[target_conn_id, target_table],
            provide_context=True,
            dag=dag,
        )

        check_empty_task >> branch
        branch >> initial_load_task
        branch >> get_max_id_task
        get_max_id_task >> extract_task >> transform_task >> load_task
