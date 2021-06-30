from requests_aws4auth import AWS4Auth
import boto3
from elasticsearch import Elasticsearch, RequestsHttpConnection
import uuid
from datetime import datetime, timezone, timedelta
import time
import random
import os

region = "ap-northeast-1" 
service = "es"
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

ENDPOINT = os.environ.get("ES_ENDPOINT")
INDEX = os.environ.get("ES_INDEX")
TYPE = "doc"

region = "ap-northeast-1"
service = "es"
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key,
                   credentials.secret_key,
                   region,
                   service,
                   session_token=credentials.token)

es = Elasticsearch(
    hosts=[{"host": ENDPOINT, "port": 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
)

body = {
    "index":{
        "analysis":{
            "tokenizer" : {
                "kuromoji" : {
                    "type" : "kuromoji_tokenizer"
                }
            },
            "analyzer" : {
                "analyzer" : {
                    "type" : "custom",
                    "tokenizer" : "kuromoji"
                }
            }
        }
    },
    "mappings": {
        "doc": {
            "properties": {
                "filename": {
                    "type": "string"
                },
                "category": {
                    "type": "string"
                },
                "title": {
                    "type": "string",
                    "analyzer": "kuromoji"
                },
                "content": {
                    "type": "string",
                    "analyzer": "kuromoji"
                },
                "tags": {
                    "type": "string"
                },
                "date": {
                    "type": "date",
                    "format": "strict_date_optional_time||epoch_millis",
                    "fields": {
                        "raw": {
                            "type": "string",
                            "index": "not_analyzed"
                        },
                        "ana": {
                            "type": "string",
                            "index": "analyzed"
                        }
                    }
                },
                "update": {
                    "type": "date",
                    "format": "strict_date_optional_time||epoch_millis",
                    "fields": {
                        "raw": {
                            "type": "string",
                            "index": "not_analyzed"
                        },
                        "ana": {
                            "type": "string",
                            "index": "analyzed"
                        }
                    }
                },
                "lank": {
                    "type": "long"
                }
            }
        }
    }
}

res = es.indices.create(index=INDEX, body=body)

print(res)
