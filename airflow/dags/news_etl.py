import pendulum
from airflow.models.dag import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from datetime import datetime
import pandas as pd
from pytz import timezone
import logging
from functions import crawling
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
import boto3
from requests_aws4auth import AWS4Auth
from opensearchpy import OpenSearch, RequestsHttpConnection

options = Options()
options.add_argument('--headless')
options.add_argument('window-size=1200x600')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

with DAG(
    dag_id="news_etl",
    schedule = '30 * * * *',
    start_date=pendulum.datetime(2024, 1, 8, 17, 00, tz="Asia/Seoul"),
    catchup=False,
    tags=["news"],
):
    def extract_news():
        logging.info("get date")
        korea_tz = timezone('Asia/Seoul')
        korea_time = datetime.now(korea_tz)
        date = korea_time.strftime('%Y%m%d')
        
        logging.info("get checkpoint")
        with open('/opt/airflow/dags/checkpoint.txt', 'r') as file:
            checkpoint = file.read()

        logging.info("selenium start")
        remote_webdriver = 'remote_chromedriver'
        with webdriver.Remote(f'{remote_webdriver}:4444/wd/hub', options=options) as driver:
            if checkpoint:
                link_list = crawling.get_link_normal(driver, date)
            else:
                link_list = crawling.get_link_init(driver, date)
            logging.info("link extract completion")

            print(link_list[:5])

            logging.info("article extract start")
            crawling.get_article(driver, link_list)
            logging.info("article extract completion")

    extract_news = PythonOperator(task_id="extract_news", python_callable=extract_news)

    spark_task = SparkSubmitOperator(
        task_id='spark_task',
        application="/usr/local/spark/app/get_similarity.py",  # Spark 코드가 저장된 경로
        conn_id='spark_default',  # Airflow에서 설정한 Spark 연결 ID
        dag=DAG,
    )

    def get_representative_value():
        logging.info("start") 
        crawling.get_representative_value()

    get_representative_value = PythonOperator(task_id="get_representative_value", python_callable=get_representative_value)

    def s3_upload():
        korea_tz = timezone('Asia/Seoul')
        korea_time = datetime.now(korea_tz)
        date = korea_time.strftime('_%Y_%m_%d_%H_%M')
  
        bucket_name = "news-data"
        key = 'news_2_representative_data' + str(date) + '.csv'
        local_file_path = "/opt/airflow/dags/news_2_representative_data.csv"
        hook = S3Hook(aws_conn_id='aws_conn')
        hook.load_file(
            bucket_name=bucket_name,
            key=key,
            filename=local_file_path,
            replace=True
        )

    s3_upload = PythonOperator(task_id="s3_upload", python_callable=s3_upload)

    def check_track():
        region = 'ap-northeast-1'
        service = 'es'
        awsauth = AWS4Auth("access_key", "secret_key", region, service)

        host = "search-news-tracking-twuc6chnabn6eplckxlyenti44.ap-northeast-1.es.amazonaws.com"

        search = OpenSearch(
            hosts = [{'host': host, 'port': 443}],
            http_auth = awsauth,
            use_ssl = True,
            verify_certs = True,
            http_compress = True,
            connection_class = RequestsHttpConnection
        )

        crawling.track_update(search)

    check_track = PythonOperator(task_id="check_track", python_callable=check_track)

    extract_news >> spark_task >> get_representative_value >> s3_upload >> check_track