import boto3
from requests_aws4auth import AWS4Auth
from opensearchpy import OpenSearch, RequestsHttpConnection

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

response = search.delete_by_query(
    index='news',
    body={
        'query': {
            'match': {
                'title': 'representative_title'
            }
        }
    }
)

# response = search.update_by_query(
#     index='news',
#     body={
#         "script": {
#             "source": """
#                 if (ctx._source.containsKey('track')) {
#                     if (ctx._source.track == null) {
#                         ctx._source.track = params.track_value;
#                     }
#                 } else {
#                     ctx._source['track'] = params.track_value;
#                 }
#             """,
#             "lang": "painless",
#             "params": {
#                 "track_value": track_value
#             }
#         },
#         "query": {
#             "bool": {
#                 "must": [
#                     {"match": {"representative_title": representative_title}}
#                 ]
#             }
#         }
#     }   
# )

# POST /test/_doc
# {
#   "movieCode": 1,
#   "movieName": "기생충",
#   "movieEnName": "Parasite2",
#   "prdtYear": "2019",
#   "repNationName": "Korea",
#   "regGenreName": "Drama"
# }

# PUT /test
# {
#   "_index": "movie",
#   "_id": "1",
#   "_version": 1,
#   "result": "created",
#   "_shards": {
#     "total": 2,
#     "successful": 2,
#     "failed": 0
#   },
#   "_seq_no": 0,
#   "_primary_term": 1
# }

# DELETE movie

# GET /news/_count

# GET _search
# {
#   "size": 2000,
#   "query": {
#     "match_all": {}
#   }
# }

# GET _search
# {
#   "size": 2000,
#   "query": {
#     "match_all": {}
#   },
#   "sort": [
#     {
#       "input_time": {
#         "order": "asc"
#       }
#     }
#   ]
# }


# GET _search
# {
#   "size": 100,
#   "query": {
#     "range": {
#         "input_time": {
#             "gte": "2024-01-09 08:00:00",
#             "lte": "2024-01-09 12:00:00"
#         }
#     }
#   }
# }

# PUT /news/_mapping
# {
#   "properties": {
#     "representative_title": {
#       "type": "text",
#       "fielddata": true
#     }
#   }
# }

# GET _search
# {
#   "query": {
#     "exists": {
#       "field": "track"
#     }
#   }
# }

# GET /news/_mapping

# PUT /test/_doc
# {
#   "properties": {
#     "new_input_time": {
#       "type": "date",
#       "format": "yyyy-MM-dd HH:mm:ss"
#     }
#   }
# }

# PUT /news
# {
#   "mappings": {
#     "properties": {
#       "input_time": {
#         "type": "date",
#         "format": "yyyy-MM-dd HH:mm:ss"
#       },
#       "link": {
#         "type": "text"
#       },
#       "reporter": {
#         "type": "text"
#       },
#       "representative_title": {
#         "type": "text"
#       },
#       "title": {
#         "type": "text"
#       },
#       "pub": {
#         "type": "text"
#       },
#       "article": {
#         "type": "text"
#       }
#     }
#   }
# }

# POST /news/_delete_by_query
# {
#   "query": {
#     "match_all": {}
#   }
# }
