from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.hooks.base import BaseHook
from datetime import datetime, timedelta
import pandas as pd
import sqlalchemy
import logging
import pytz
import numpy as np

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 7, 20),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'trx_facturation_dw_checksum_2',
    default_args=default_args,
    schedule_interval='0 1 * * *', 
    catchup=False,
)

def format_datetime(dt):
    if isinstance(dt, str):
        dt = pd.to_datetime(dt)
    if isinstance(dt, pd.Timestamp):
        dt = dt.to_pydatetime()
    return dt.strftime('%Y-%m-%d %H:%M:%S')

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

def initial_load(source_conn_id, source_table, target_conn_id, target_table, columns_to_check, **kwargs):
    source_engine = get_engine(source_conn_id)
    target_engine = get_engine(target_conn_id)

    columns_str = ', '.join(columns_to_check)
    query = f"""
    SELECT *, CHECKSUM({columns_str}) AS ChecksumColonne 
    FROM {source_table}
    """
    df = pd.read_sql(query, source_engine)
    
    now = datetime.now(pytz.UTC)
    df['valid_from'] = now
    df['valid_to'] = datetime(2099, 12, 31, 23, 59, 59, tzinfo=pytz.UTC)
    df['flag'] = 1

    datetime_columns = ['dinsertion', 'last_updated', 'valid_from', 'valid_to']
    for col in datetime_columns:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: format_datetime(x) if pd.notnull(x) else None)

    df.head(0).to_sql(target_table, target_engine, if_exists='replace', index=False)
    
    chunksize = 1000  # adjust this value based on your data size and memory constraints
    for chunk in [df[i:i + chunksize] for i in range(0, df.shape[0], chunksize)]:
        chunk.to_sql(target_table, target_engine, if_exists='append', index=False, method='multi')

    logging.info(f"Initial load complete for table {source_table} to {target_table}")

def get_last_max_id(target_conn_id, target_table, primary_key, **kwargs):
    target_engine = get_engine(target_conn_id)
    query = f"SELECT COALESCE(MAX({primary_key}), 0) FROM {target_table}"
    result = target_engine.execute(query).fetchone()
    max_id = result[0]
    kwargs['ti'].xcom_push(key=f'{target_table}_max_id', value=max_id)
    logging.info(f"Last max ID for table {target_table}: {max_id}")

def extract_new_data(source_conn_id, source_table, target_conn_id, target_table, primary_key, columns_to_check, **kwargs):
    ti = kwargs['ti']
    max_id = ti.xcom_pull(key=f'{target_table}_max_id')
    source_engine = get_engine(source_conn_id)
    columns_str = ', '.join(columns_to_check)
    query = f"""
    SELECT *, CHECKSUM({columns_str}) AS ChecksumColonne 
    FROM {source_table} 
    WHERE {primary_key} > {max_id}
    """
    df = pd.read_sql(query, source_engine)
    logging.info(f"Extracted {df.shape[0]} new rows from {source_table}")
    return df.to_json(date_format='iso')

def load_new_data(df_json, target_conn_id, target_table, **kwargs):
    df = pd.read_json(df_json)
    if df.empty:
        logging.info(f"No new data to load into {target_table}")
        return
    
    now = datetime.now(pytz.UTC)
    df['valid_from'] = now
    df['valid_to'] = datetime(2099, 12, 31, 23, 59, 59, tzinfo=pytz.UTC)
    df['flag'] = 1

    datetime_columns = ['dinsertion', 'last_updated', 'valid_from', 'valid_to']
    for col in datetime_columns:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: format_datetime(x) if pd.notnull(x) else None)

    target_engine = get_engine(target_conn_id)
    df.to_sql(target_table, target_engine, if_exists='append', index=False, method='multi')
    logging.info(f"Loaded {df.shape[0]} new records into {target_table}")

def scd_update_with_checksum(source_conn_id, source_table, target_conn_id, target_table, primary_key, columns_to_check, **kwargs):
    source_engine = get_engine(source_conn_id)
    target_engine = get_engine(target_conn_id)

    columns_str = ', '.join(columns_to_check)

    source_query = f"""
    SELECT 
        {primary_key}, 
        {columns_str},
        CHECKSUM({columns_str}) AS NouveauChecksum
    FROM {source_table}
    """
    
    target_query = f"""
    SELECT 
        {primary_key}, 
        ChecksumColonne,
        flag
    FROM {target_table}
    WHERE flag = 1
    """
    
    source_df = pd.read_sql(source_query, source_engine)
    target_df = pd.read_sql(target_query, target_engine)
    
    comparison_df = pd.merge(source_df, target_df, on=primary_key, how='inner')
    
    comparison_df['StatutModification'] = np.where(
        comparison_df['NouveauChecksum'] == comparison_df['ChecksumColonne'],
        'Non modifié',
        'Modifié'
    )
    
    modified_records = comparison_df[comparison_df['StatutModification'] == 'Modifié']

    if not modified_records.empty:
        now = datetime.now(pytz.UTC)
        
        # Update old records
        update_stmt = f"""
        UPDATE {target_table}
        SET valid_to = ?, flag = 0
        WHERE {primary_key} = ? AND flag = 1
        """
        target_engine.execute(update_stmt, 
                              [(now, row[primary_key]) for _, row in modified_records.iterrows()])

        # Prepare new versions
        new_versions = modified_records.copy()
        new_versions['valid_from'] = now
        new_versions['valid_to'] = datetime(2099, 12, 31, 23, 59, 59, tzinfo=pytz.UTC)
        new_versions['flag'] = 1
        new_versions['ChecksumColonne'] = new_versions['NouveauChecksum']

        datetime_columns = ['dinsertion', 'last_updated', 'valid_from', 'valid_to']
        for col in datetime_columns:
            if col in new_versions.columns:
                new_versions[col] = new_versions[col].apply(lambda x: format_datetime(x) if pd.notnull(x) else None)

        columns_to_insert = [col for col in new_versions.columns if col not in ['StatutModification', 'NouveauChecksum']]
        new_versions[columns_to_insert].to_sql(target_table, target_engine, if_exists='append', index=False, method='multi')

        logging.info(f"Updated {len(modified_records)} records in {target_table}")
    else:
        logging.info(f"No updates needed for {target_table}")

for table, columns in {
    'trx': ['nid', 'dinsertion', 'nproductid', 'namount', 'noperationfee', 'nshopid'],
    'facturation': ['nid', 'nshopid', 'dinsertion', 'sbillerid', 'namount']
}.items():
    source_conn_id = 'checka'
    target_conn_id = 'checkb'
    source_table = table
    target_table = f'dest_{table}'
    primary_key = 'nid'
    columns_to_check = columns[1:]  # Exclude 'nid' from checksum calculation
    
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
            'target_table': target_table,
            'columns_to_check': columns_to_check
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
            'primary_key': primary_key,
            'columns_to_check': columns_to_check
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
        python_callable=scd_update_with_checksum,
        op_kwargs={
            'source_conn_id': source_conn_id, 
            'source_table': source_table, 
            'target_conn_id': target_conn_id, 
            'target_table': target_table,
            'primary_key': primary_key,
            'columns_to_check': columns_to_check
        },
        dag=dag,
    )

    check_empty_task >> branch
    branch >> initial_load_task
    branch >> [get_max_id_task, scd_update_task]
    get_max_id_task >> extract_new_data_task >> load_new_data_task
