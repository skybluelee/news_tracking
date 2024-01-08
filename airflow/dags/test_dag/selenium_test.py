import pendulum
from airflow.models.dag import DAG
from airflow.operators.python import PythonOperator
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import logging

options = Options()
options.add_argument('--headless')
options.add_argument('window-size=1200x600')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

with DAG(
    dag_id="selenium",
    schedule=None,
    start_date=pendulum.datetime(2023, 12, 29, 21, 10, tz="Asia/Seoul"),
    catchup=False,
    tags=["example"],
):
    def s3_upload():
        logging.info("start")
        remote_webdriver = 'remote_chromedriver'
        with webdriver.Remote(f'{remote_webdriver}:4444/wd/hub', options=options) as driver:
            logging.info("webdriver")
            url = "https://www.google.com/"
            driver.get(url)
            title = driver.title
            logging.info("print")
            print(title)

    run_this = PythonOperator(task_id="s3_upload", python_callable=s3_upload)

    run_this