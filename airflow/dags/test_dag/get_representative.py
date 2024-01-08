import pendulum
from airflow.models.dag import DAG
from airflow.operators.python import PythonOperator
import logging
from functions import crawling

with DAG(
    dag_id="get_representative_value",
    schedule=None,
    start_date=pendulum.datetime(2023, 12, 29, 21, 10, tz="Asia/Seoul"),
    catchup=False,
    tags=["example"],
):
    def get_representative_value():
        logging.info("start") 
        crawling.get_representative_value()

    run_this = PythonOperator(task_id="get_representative_value", python_callable=get_representative_value)

    run_this