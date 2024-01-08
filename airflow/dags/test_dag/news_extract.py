import pendulum
from airflow.models.dag import DAG
from airflow.operators.python import PythonOperator
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from datetime import datetime
from pytz import timezone
import logging
from functions import crawling

options = Options()
options.add_argument('--headless')
options.add_argument('window-size=1200x600')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

with DAG(
    dag_id="news_extraction",
    schedule=None,
    start_date=pendulum.datetime(2023, 12, 29, 21, 10, tz="Asia/Seoul"),
    catchup=False,
    tags=["example"],
):
    def link_extract():
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


    run_this = PythonOperator(task_id="link_extract", python_callable=link_extract, provide_context=True)

    run_this 