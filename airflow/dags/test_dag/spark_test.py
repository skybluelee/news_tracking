from datetime import datetime
import pendulum
from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator

DAG(
    dag_id="spark_submit_operator",
    schedule = '30 * * * *',
    start_date=pendulum.datetime(2023, 12, 30, 9, 00, tz="Asia/Seoul"),
    catchup=False,
    tags=["test"],
)

# Spark 작업 실행
spark_task = SparkSubmitOperator(
    task_id='spark_task',
    application="/usr/local/spark/app/script.py",  # Spark 코드가 저장된 경로
    conn_id='spark_default',  # Airflow에서 설정한 Spark 연결 ID
    dag=DAG,
)

spark_task
