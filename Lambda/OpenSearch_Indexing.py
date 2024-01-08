import boto3
import requests
import json
import csv
from requests_aws4auth import AWS4Auth

region = 'ap-northeast-1' # e.g. us-west-1
service = 'es'
credentials = boto3.Session().get_credentials()
#awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
awsauth = AWS4Auth("access_key", "secret_key", region, service)

# OpenSearch 클러스터 엔드포인트
OPENSEARCH_ENDPOINT = "https://search-news-tracking-twuc6chnabn6eplckxlyenti44.ap-northeast-1.es.amazonaws.com"

def lambda_handler(event, context):
    # 이벤트 레코드에서 버킷 이름과 객체 키 추출
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    object_key = event['Records'][0]['s3']['object']['key']
    #bucket_name = "news-data"
    #object_key = "test8.csv"
    # S3 객체 읽기
    s3_client = boto3.client('s3')
    response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
    csv_content = response['Body'].read().decode('utf-8')
    
    # CSV 데이터 파싱
    rows = csv_content.splitlines()
    csv_reader = csv.DictReader(rows)
    
    # OpenSearch로 데이터 전송
    headers = {'Content-Type': 'application/json'}
    url = f"{OPENSEARCH_ENDPOINT}/news/_doc"
    print("url: ",url)
    
    for row in csv_reader:
        response = requests.post(url, auth=awsauth, headers=headers, data=json.dumps(row))
        print("response: ", response)
        print("\n\n")
        print(json.dumps(row))
        print("\n\n")
        print(response.text)
        if response.status_code != 201:
            print(f"Failed to index data: {response.text}")
            return {
                'statusCode': 500,
                'body': json.dumps('Failed to index data')
            }
    
    return {
        'statusCode': 200,
        'body': json.dumps('Data indexed successfully')
    }
