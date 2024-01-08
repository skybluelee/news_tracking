import pandas as pd
import pendulum
import boto3
from requests_aws4auth import AWS4Auth
from opensearchpy import OpenSearch, RequestsHttpConnection

from functions import crawling

from airflow.models.dag import DAG
from airflow.operators.python import PythonOperator

with DAG(
    dag_id="opensearch_check",
    schedule=None,
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False,
    tags=["example"],
):
    def opensearch():
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
        def add_track_field_to_documents(search, representative_title, track):
            track_value = track  # 업데이트할 값 설정
            search.update_by_query(index='news', body={
                "script": {
                    "source": """
                        if (ctx._source.containsKey('track')) {
                            if (ctx._source.track == null) {
                                ctx._source.track = params.track_value;
                            }
                        } else {
                            ctx._source['track'] = params.track_value;
                        }
                    """,
                    "lang": "painless",
                    "params": {
                        "track_value": track_value
                    }
                },
                "query": {
                    "bool": {
                        "must": [
                            {"match": {"representative_title": representative_title}}
                        ]
                    }
                }
            })

        if 'track.keyword' in search.indices.get(index='news')['news']['mappings']['properties']:
            response = search.search(
                index='news',
                body={
                    "size": 0,
                    "aggs": {
                        "tracks": {
                            "terms": {
                                "field": "track.keyword",
                                "size": 10000  # 유니크한 track 값이 많을 경우에는 적절한 크기로 설정
                            },
                            "aggs": {
                                "articles": {
                                    "terms": {
                                        "field": "article.keyword",
                                        "size": 10000  # 유니크한 article 값이 많을 경우에는 적절한 크기로 설정
                                    }
                                }
                            }
                        }
                    }
                }
            )
            # 집계 결과에서 'tracks' 집계의 버킷을 추출
            tracks_buckets = response['aggregations']['tracks']['buckets']

            # 가장 최신의 대표값이 있는 csv 파일 로드
            df = pd.read_csv("/opt/airflow/dags/news_latest_representative.csv")
            latest_article = df['article'].tolist()
            print('최근의 대표 기사만 df로 만듦')

            # 각 버킷에서 'articles' 집계의 버킷을 추출하고 article 값을 출력
            for bucket in tracks_buckets:
                track_value = bucket['key']
                article_buckets = bucket['articles']['buckets']
                articles = [article_bucket['key'] for article_bucket in article_buckets]

                articles_fianl = latest_article + articles
                print("articles_fianl", articles_fianl)
                matrix = crawling.konlpy(articles_fianl)
                for i in range(len(latest_article)):
                    for num in matrix[i][len(latest_article):]:
                        if num > 70:
                            title = df.loc[i, 'title']
                            add_track_field_to_documents(search, 'news', title, track_value)
                            break
        else:
            print("추적할 뉴스 없음.")
        
    run_this = PythonOperator(task_id="opensearch", python_callable=opensearch)

    run_this
