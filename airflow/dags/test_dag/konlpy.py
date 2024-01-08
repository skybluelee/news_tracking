import pendulum
from airflow.models.dag import DAG
from airflow.operators.python import PythonOperator
import logging
from functions import crawling
import pandas as pd

with DAG(
    dag_id="konlpy",
    schedule=None,
    start_date=pendulum.datetime(2023, 12, 29, 21, 10, tz="Asia/Seoul"),
    catchup=False,
    tags=["example"],
):
    def konlpy():
        logging.info("start") 
        df = pd.read_csv('/opt/airflow/dags/news_1_raw_data.csv')
        crawling.konlpy(df)

    run_this = PythonOperator(task_id="konlpy", python_callable=konlpy)

    run_this