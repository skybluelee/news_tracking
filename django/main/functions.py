import boto3
from requests_aws4auth import AWS4Auth
from opensearchpy import OpenSearch, RequestsHttpConnection

# AWS IAM 사용자 인증
region = 'ap-northeast-1'
service = 'es'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth("AKIATNOQWNZFQBFA3PXJ", "OYgh1XYU/GjLVSALFFJ3qTqeZ6HoTh4dMfBvIFHn", region, service)

host = "search-news-tracking-twuc6chnabn6eplckxlyenti44.ap-northeast-1.es.amazonaws.com"

search = OpenSearch(
    hosts = [{'host': host, 'port': 443}],
    http_auth = awsauth,
    use_ssl = True,
    verify_certs = True,
    http_compress = True,
    connection_class = RequestsHttpConnection
)

# 현재 추적 중인 뉴스 검색
def get_track_news():
    response = search.search(index='news', body={
        "size": 0,
        "aggs": {
            "tracks": {
                "terms": {
                    "field": "track",
                    "size": 10000
                },
                "aggs": {
                    "latest_doc": {
                        "top_hits": {
                            "size": 1,
                            "sort": [{"input_time": {"order": "desc"}}],
                            "_source": ["title"]
                        }
                    }
                }
            }
        }
    })

    # 집계 결과 가공
    buckets = response['aggregations']['tracks']['buckets']
    title_list = [{'title': bucket['latest_doc']['hits']['hits'][0]['_source']['title'], 'count': bucket['doc_count'], 'track': bucket['key']} for bucket in buckets]

    # article_list 초기화
    article_list = []
    title_set = set()

    response = search.search(index='news', body={
        "sort": [{"input_time": {"order": "desc"}}],  # 최신순으로 정렬
        "query": {
            "exists": {
                "field": "track"  # track 필드가 존재하는 데이터만 검색
            }
        }
    })

    # article_list 초기화
    article_list = []

    for title_dict in title_list:
        # 검색 결과에서 각 문서를 최신순으로 순회
        for hit in response['hits']['hits']:
            title = hit['_source'].get('title', '')
            article = hit['_source'].get('article', '')
            input_time = hit['_source'].get('input_time', '')
            pub = hit['_source'].get('pub', '')
            reporter = hit['_source'].get('reporter', '')
            link = hit['_source'].get('link', '')
            track = hit['_source'].get('track', '')

            if title_dict['track'] == track:
                data = {
                    'representative_title': title_dict['title'],  # 각 문서의 title을 representative_title로 설정
                    'title': title,
                    'article': f'{article} \n {input_time} \n {pub} \n {reporter}',
                    'link': link
                }

                if title not in title_set:
                    title_set.add(title)
                    article_list.append(data)

    return title_list, article_list

# 설정할 track 번호를 지정하는 함수
def get_track_value():
    response = search.search(index='news', body={
                                                "size": 0,
                                                "aggs": {
                                                    "unique_tracks": {
                                                        "terms": {
                                                            "field": "track",
                                                            "size": 10000
                                                        }
                                                    }
                                                }
                                            })

    # 검색 결과에서 고유한 track 값 추출
    unique_track_values = [bucket['key'] for bucket in response['aggregations']['unique_tracks']['buckets']]

    cnt = 0
    # track 필드가 없는 경우
    if not unique_track_values:
        track_value = 0
    else:
        for num in unique_track_values:
            if cnt == num: # 기존에 있는 값
                cnt += 1
            else:
                track_value = cnt
                return track_value
        track_value = cnt + 1
    return track_value

# 추적 상태에 따라 track에 값을 추가하거나 제거하는 업데이트 함수
def update_track_value(title, track_value):
    response = search.search(index='news', body={
        "query": {
            "bool": {
                "must": [
                    {"match": {"title": title}}
                ]
            }
        },
        "_source": ["representative_title", "track"]
    })

    for hit in response['hits']['hits']:
        representative_title = hit['_source']['representative_title']
        current_track_value = hit['_source'].get('track')

        if current_track_value is not None:
            # track 필드가 이미 존재하면 값을 null로 설정
            response = search.search(index='news', body={
                "query": {
                    "bool": {
                        "must": [
                            {"match": {"track": current_track_value}} 
                        ]
                    }
                },
                "_source": ["representative_title"]
            })
            for hit in response['hits']['hits']:
                representative_title = hit['_source']['representative_title']
                
                # track 값을 null로 설정하는 업데이트 쿼리 실행
                search.update_by_query(index='news', body={
                    "script": {
                        "source": "ctx._source.track = null;",
                        "lang": "painless"
                    },
                    "query": {
                        "bool": {
                            "must": [
                                {"match": {"representative_title": representative_title}}
                            ]
                        }
                    }
                })
        else:
            # track 필드가 존재하면서 null인 경우 또는 track 필드가 존재하지 않는 경우 representative_title에 대한 track 값을 추가
            track_value = "your_track_value_here"  # 업데이트할 값 설정
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

# 시간과 검색 단어를 모두 사용하여 뉴스 검색
def get_news_w_time_w_search(request):
    startDate = request.POST['startDate']
    startTime = request.POST['startTime']
    startSelect = request.POST['startSelect']
    endDate = request.POST['endDate']
    endTime = request.POST['endTime']
    endSelect = request.POST['endSelect']
    searchSelect = request.POST['searchSelect']
    searchContent = request.POST['searchContent']
    start, end = change_date(startDate, startTime, startSelect, endDate, endTime, endSelect)
    if searchSelect == 'title':
        query = {
            "size": 1000,
            "query": {
                "bool": {
                "must": [
                    {
                    "query_string": {
                        "fields": ["title"],
                        "query": f"*{searchContent}*"
                    }
                    },
                    {
                    "range": {
                        "input_time": {
                        "gte": start,
                        "lte": end,
                        "format": "yyyy-MM-dd HH:mm:ss"
                        }
                    }
                    }
                ]
                }
            }
            }
    elif searchSelect == 'all':
        query = {
            "size": 1000,
            "query": {
                "bool": {
                "must": [
                    {
                    "query_string": {
                        "fields": ["article"],
                        "query": f"*{searchContent}*"
                    }
                    },
                    {
                    "range": {
                        "input_time": {
                        "gte": start,
                        "lte": end,
                        "format": "yyyy-MM-dd HH:mm:ss"
                        }
                    }
                    }
                ]
                }
            }
            }

    response  = search.search(index="news", body=query)
    hits = response['hits']['hits']
    representative_title_count = {}
    
    title_list = []
    article_list = []
    for hit in hits:
        source = hit['_source']
        representative_title = source.get('representative_title')
        title = source.get('title')
        article = source.get('article', '')
        link = source.get('link', '')
        input_time = source.get('input_time', '')
        pub = source.get('pub', '')
        reporter = source.get('reporter', '')

        # title_list 업데이트
        if representative_title in representative_title_count:
            representative_title_count[representative_title] += 1
        else:
            representative_title_count[representative_title] = 1

        # article_list 업데이트
        article_list.append({
            'representative_title': representative_title,
            'title': title,
            'article': f'{article} \n {input_time} \n {pub} \n {reporter}',
            'link': link
        })
    # title_list 생성
    title_list = [{'title': title, 'count': count} for title, count in representative_title_count.items()]

    # article_list의 범위를 지정하기 위한 리스트
    repre_idx = []

    # article_list의 순서를 title_list의 순서와 일치시키기 위해 재정렬
    sorted_article_list = []
    for title_info in title_list:
        title = title_info['title']
        for article_info in article_list:
            if article_info['representative_title'] == title:
                sorted_article_list.append(article_info)
        repre_idx.append(len(sorted_article_list))

    return title_list, sorted_article_list, repre_idx

# 시간에 대해서만 뉴스를 검색하는 함수
def get_news_w_time_wo_search(request):
    startDate = request.POST['startDate']
    startTime = request.POST['startTime']
    startSelect = request.POST['startSelect']
    endDate = request.POST['endDate']
    endTime = request.POST['endTime']
    endSelect = request.POST['endSelect']
    start, end = change_date(startDate, startTime, startSelect, endDate, endTime, endSelect)

    query = {
        "size": 2000,
        "query": {
            "range": {
                "input_time": {
                    "gte": start,
                    "lte": end,
                    "format": "yyyy-MM-dd HH:mm:ss"
                }
            }
        }
    }
    
    response  = search.search(index="news", body=query)
    hits = response['hits']['hits']
    representative_title_count = {}
    title_set = set()

    title_list = []
    article_list = []
    for hit in hits:
        source = hit['_source']
        representative_title = source.get('representative_title')
        title = source.get('title')
        article = source.get('article', '')
        link = source.get('link', '')
        input_time = source.get('input_time', '')
        pub = source.get('pub', '')
        reporter = source.get('reporter', '')

        data = {
            'representative_title': representative_title,
            'title': title,
            'article': f'{article} \n {input_time} \n {pub} \n {reporter}',
            'link': link
        }

        if title not in title_set:
            title_set.add(title)
            article_list.append(data)

            if representative_title in representative_title_count:
                representative_title_count[representative_title] += 1
            else:
                representative_title_count[representative_title] = 1        

    title_list = [{'title': title, 'count': count} for title, count in representative_title_count.items()]
    title_list = sorted(title_list, key=lambda x: x['count'], reverse=True)
    repre_idx = []

    sorted_article_list = []
    for title_info in title_list:
        title = title_info['title']
        for article_info in article_list:
            if article_info['representative_title'] == title:
                sorted_article_list.append(article_info)
        repre_idx.append(len(sorted_article_list))

    return title_list, sorted_article_list, repre_idx

# 검색 단어만을 사용하여 뉴스를 검색하는 함수
def get_news_wo_time_w_search(request):
    searchSelect = request.POST['searchSelect']
    searchContent = request.POST['searchContent']
    
    if searchSelect == 'title':
        query = {
            "size": 1000,
            "query": {
                "bool": {
                    "must": [
                        {
                            "query_string": {
                                "fields": ["title"],
                                "query": f"*{searchContent}*"
                            }
                        },
                    ]
                }
            }
        }
    elif searchSelect == 'all':
        query = {
            "size": 1000,
            "query": {
                "bool": {
                    "must": [
                        {
                            "query_string": {
                                "fields": ["article"],
                                "query": f"*{searchContent}*"
                            }
                        },
                    ]
                }
            }
        }    

    response  = search.search(index="news", body=query)

    hits = response['hits']['hits']
    representative_title_count = {}

    title_list = []
    article_list = []
    for hit in hits:
        source = hit['_source']
        representative_title = source.get('representative_title')
        title = source.get('title')
        article = source.get('article', '')
        link = source.get('link', '')
        input_time = source.get('input_time', '')
        pub = source.get('pub', '')
        reporter = source.get('reporter', '')

        if representative_title in representative_title_count:
            representative_title_count[representative_title] += 1
        else:
            representative_title_count[representative_title] = 1

        article_list.append({
            'representative_title': representative_title,
            'title': title,
            'article': f'{article} \n {input_time} \n {pub} \n {reporter}',
            'link': link
        })

    title_list = [{'title': title, 'count': count} for title, count in representative_title_count.items()]
    repre_idx = []

    sorted_article_list = []
    for title_info in title_list:
        title = title_info['title']
        for article_info in article_list:
            if article_info['representative_title'] == title:
                sorted_article_list.append(article_info)
        repre_idx.append(len(sorted_article_list))

    return title_list, sorted_article_list, repre_idx

# 시간을 쿼리에서 사용할 수 있도록 변형하는 함수
def change_date(startDate, startTime, startSelect, endDate, endTime, endSelect):
    if not startTime: # 시간이 정해지지 않으면
        start = startDate + ' 00:' + startSelect + ':00'
    else:
        start = startDate + ' ' + startTime + ':' + startSelect + ':00'
    if not endTime: # 시간이 정해지지 않으면
        end = endDate + ' 00:' + endSelect + ':00'
    else:
        end = endDate + ' ' + endTime + ':' + endSelect + ':00'

    return start, end