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
    'start_date': datetime(2024, 7, 17),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'trx_facturation_dw_dle3',
    default_args=default_args,
    schedule_interval='0 1 * * *', 
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
    return is_empty

def branch_task(ti, table, **kwargs):
    target_table = f'dest_{table}'
    is_empty = ti.xcom_pull(key=f'{target_table}_is_empty')
    logging.info(f"Branch decision for {target_table}, is_empty: {is_empty}")
    if is_empty:
        return f'initial_load_{table}'
    else:
        return [f'get_last_max_id_{table}', f'scd_update_{table}']

def initial_load(source_conn_id, source_table, target_conn_id, target_table, **kwargs):
    source_engine = get_engine(source_conn_id)
    query = f"SELECT * FROM {source_table}"
    df = pd.read_sql(query, source_engine)
    
    df['valid_from'] = datetime.now()
    df['valid_to'] = datetime(9999, 12, 31)
    df['flag'] = 1

    target_engine = get_engine(target_conn_id)
    df.to_sql(target_table, target_engine, if_exists='replace', index=False)
    logging.info(f"Initial load complete for table {source_table} to {target_table}")

def get_last_max_id(target_conn_id, target_table, primary_key, **kwargs):
    target_engine = get_engine(target_conn_id)
    query = f"SELECT COALESCE(MAX({primary_key}), 0) FROM {target_table}"
    result = target_engine.execute(query).fetchone()
    max_id = result[0]
    kwargs['ti'].xcom_push(key=f'{target_table}_max_id', value=max_id)
    logging.info(f"Last max ID for table {target_table}: {max_id}")

def extract_new_data(source_conn_id, source_table, target_conn_id, target_table, primary_key, **kwargs):
    ti = kwargs['ti']
    max_id = ti.xcom_pull(key=f'{target_table}_max_id')
    source_engine = get_engine(source_conn_id)
    query = f"SELECT * FROM {source_table} WHERE {primary_key} > {max_id}"
    df = pd.read_sql(query, source_engine)
    logging.info(f"Extracted {df.shape[0]} new rows from {source_table}")
    return df.to_json()

def load_new_data(df_json, target_conn_id, target_table, **kwargs):
    df = pd.read_json(df_json)
    if df.empty:
        logging.info(f"No new data to load into {target_table}")
        return
    
    df['valid_from'] = datetime.now()
    df['valid_to'] = datetime(9999, 12, 31)
    df['flag'] = 1

    target_engine = get_engine(target_conn_id)
    df.to_sql(target_table, target_engine, if_exists='append', index=False)
    logging.info(f"Loaded {df.shape[0]} new records into {target_table}")

def scd_update(source_conn_id, source_table, target_conn_id, target_table, primary_key, **kwargs):
    source_engine = get_engine(source_conn_id)
    target_engine = get_engine(target_conn_id)

    source_df = pd.read_sql(f"SELECT * FROM {source_table}", source_engine)
    target_df = pd.read_sql(f"SELECT * FROM {target_table} WHERE flag = 1", target_engine)

    logging.info(f"Source columns: {source_df.columns.tolist()}")
    logging.info(f"Target columns: {target_df.columns.tolist()}")

    if primary_key not in source_df.columns or primary_key not in target_df.columns:
        logging.error(f"Primary key {primary_key} not found in one of the dataframes")
        return

    merged = pd.merge(target_df, source_df, on=primary_key, suffixes=('_target', '_source'))
    logging.info(f"Merged columns: {merged.columns.tolist()}")

    columns_to_compare = [col for col in source_df.columns if col != primary_key]
    updated_records = merged[merged.apply(lambda row: any(row[f'{col}_target'] != row[f'{col}_source'] for col in columns_to_compare if f'{col}_target' in row.index and f'{col}_source' in row.index), axis=1)]

    logging.info(f"Updated records columns: {updated_records.columns.tolist()}")

    if not updated_records.empty:
        current_time = datetime.now()
        
        old_record_columns = [col for col in target_df.columns if col in updated_records.columns and not col.endswith('_source')]
        logging.info(f"Old record columns: {old_record_columns}")
        old_records = updated_records[old_record_columns].copy()
        old_records['valid_to'] = current_time
        old_records['flag'] = 0

        new_record_columns = [col for col in source_df.columns]
        logging.info(f"New record columns: {new_record_columns}")
        new_versions = updated_records[[f"{col}_source" if f"{col}_source" in updated_records.columns else col for col in new_record_columns]].copy()
        new_versions.columns = new_record_columns  # Rename columns to remove '_source' suffix
        new_versions['valid_from'] = current_time
        new_versions['valid_to'] = datetime(9999, 12, 31)
        new_versions['flag'] = 1

        update_stmt = f"""
        UPDATE {target_table}
        SET valid_to = ?, flag = 0
        WHERE {primary_key} = ? AND flag = 1
        """
        target_engine.execute(update_stmt, 
                              [(row['valid_to'], row[primary_key]) for _, row in old_records.iterrows()])

        new_versions.to_sql(target_table, target_engine, if_exists='append', index=False)

        logging.info(f"Updated {len(updated_records)} records in {target_table}")
    else:
        logging.info(f"No updates needed for {target_table}")

for table in ['trx', 'facturation']:
    source_conn_id = 'scda'
    target_conn_id = 'scdb'
    source_table = table
    target_table = f'dest_{table}'
    primary_key = 'nid'
    
    check_empty_task = PythonOperator(
        task_id=f'check_if_target_is_empty_{table}',
        python_callable=check_if_target_is_empty,
        op_kwargs={'target_conn_id': target_conn_id, 'target_table': target_table},
        dag=dag,
    )

    branch = BranchPythonOperator(
        task_id=f'branch_task_{table}',
        python_callable=branch_task,
        op_kwargs={'table': table},
        dag=dag,
    )

    initial_load_task = PythonOperator(
        task_id=f'initial_load_{table}',
        python_callable=initial_load,
        op_kwargs={
            'source_conn_id': source_conn_id, 
            'source_table': source_table, 
            'target_conn_id': target_conn_id, 
            'target_table': target_table
        },
        dag=dag,
    )

    get_max_id_task = PythonOperator(
        task_id=f'get_last_max_id_{table}',
        python_callable=get_last_max_id,
        op_kwargs={'target_conn_id': target_conn_id, 'target_table': target_table, 'primary_key': primary_key},
        dag=dag,
    )

    extract_new_data_task = PythonOperator(
        task_id=f'extract_new_data_{table}',
        python_callable=extract_new_data,
        op_kwargs={
            'source_conn_id': source_conn_id, 
            'source_table': source_table, 
            'target_conn_id': target_conn_id, 
            'target_table': target_table,
            'primary_key': primary_key
        },
        dag=dag,
    )

    load_new_data_task = PythonOperator(
        task_id=f'load_new_data_{table}',
        python_callable=load_new_data,
        op_kwargs={
            'df_json': "{{ ti.xcom_pull(task_ids='extract_new_data_" + table + "') }}",
            'target_conn_id': target_conn_id,
            'target_table': target_table
        },
        dag=dag,
    )

    scd_update_task = PythonOperator(
        task_id=f'scd_update_{table}',
        python_callable=scd_update,
        op_kwargs={
            'source_conn_id': source_conn_id, 
            'source_table': source_table, 
            'target_conn_id': target_conn_id, 
            'target_table': target_table,
            'primary_key': primary_key
        },
        dag=dag,
    )

    check_empty_task >> branch
    branch >> initial_load_task
    branch >> [get_max_id_task, scd_update_task]
    get_max_id_task >> extract_new_data_task >> load_new_data_task