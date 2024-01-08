import pendulum
from airflow.models.dag import DAG
from airflow.operators.python import PythonOperator
import boto3
import requests
from requests_aws4auth import AWS4Auth
from opensearchpy import OpenSearch, RequestsHttpConnection
with DAG(
    dag_id="opensearch_test",
    schedule=None,
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False,
    tags=["example"],
):
    def opensearch():
        region = 'ap-northeast-1' # e.g. us-west-1
        service = 'es'
        credentials = boto3.Session().get_credentials()
        awsauth = AWS4Auth("access_key", "secret_key", region, service)

        host = "search-news-tracking-twuc6chnabn6eplckxlyenti44.ap-northeast-1.es.amazonaws.com"

        search = OpenSearch(
            hosts = [{'host': host, 'port': 443}],
            http_auth = awsauth,
            use_ssl = True,
            verify_certs = True,
            http_compress = True, # enables gzip compression for request bodies
            connection_class = RequestsHttpConnection
        )

        docs = search.search(index="test", body={"query": {"match": {"pub": "KBS"}}})
    
        # 결과 출력
        for doc in docs['hits']['hits']:
            print(doc['_source'])
        
    run_this = PythonOperator(task_id="opensearch", python_callable=opensearch)


    run_this