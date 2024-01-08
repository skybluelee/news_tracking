import pendulum
from airflow.models.dag import DAG
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.operators.python import PythonOperator
import os

with DAG(
    dag_id="s3_upload",
    schedule=None,
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False,
    tags=["example"],
):
    def s3_upload():
        bucket_name = "news-data"
        key = 'news_2_representative_data.csv'
        local_file_path = "/opt/airflow/dags/news_2_representative_data.csv"
        hook = S3Hook(aws_conn_id='aws_conn')
        hook.load_file(
            bucket_name=bucket_name,
            key=key,
            filename=local_file_path,
            replace=True
        )

    run_this = PythonOperator(task_id="s3_upload", python_callable=s3_upload)

    run_this
