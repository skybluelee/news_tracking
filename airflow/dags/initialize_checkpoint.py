import pendulum
import logging
from airflow.models.dag import DAG
from airflow.operators.python import PythonOperator

with DAG(
    dag_id="initialize_checkpoint",
    schedule = '0 23 * * *',
    start_date=pendulum.datetime(2024, 1, 8, 23, 00, tz="Asia/Seoul"),
    catchup=False,
    tags=["news"],
):
    def initialize_checkpoint():
        logging.info("get checkpoint")
        with open('/opt/airflow/dags/checkpoint.txt', 'w') as file:
            file.write('')
        logging.info("checkpoint initalize")

    initialize_checkpoint = PythonOperator(task_id="initialize_checkpoint", python_callable=initialize_checkpoint)

    initialize_checkpoint