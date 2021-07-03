import boto3
import os
import re
from datetime import date
import json
from github import Github
import urllib.parse
import requests
from requests_aws4auth import AWS4Auth
from elasticsearch import Elasticsearch, RequestsHttpConnection

'''
このプログラムがやること

定期的に呼び出されてElasticsearchに登録されているが
Githubにはすでにない情報の登録を削除する

'''

GITHUB_ACCESS_TOKEN = os.environ.get('GITHUB_ACCESS_TOKEN')

g = Github(GITHUB_ACCESS_TOKEN)

GITHUB_PATH = "lib"
GITHUB_BRANCH = "master"
GITHUB_OWNER = "suzukiken"
GITHUB_URL_PREFIX = "https://github.com/"
GITHUB_URL_MIDDLE = "/blob/master/"

ENDPOINT = os.environ.get("ES_ENDPOINT")
INDEX = os.environ.get("ES_CODE_INDEX")
TYPE = "doc"

region = "ap-northeast-1" 
service = "es"
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

es = Elasticsearch(
    hosts=[{"host": ENDPOINT, "port": 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
)

def lambda_handler(event, context):
    print(event)
    
    # 今のgithubの内容を得る
    
    github_contents = []
    
    for repo in g.get_user().get_repos():
        if not repo.full_name.startswith(GITHUB_OWNER + '/'):
            continue
        if repo.private:
            continue
        try:
            contents = repo.get_contents(GITHUB_PATH)
        except:
            pass
        else:
            print('contents: {}'.format(contents))
            while contents:
                file_content = contents.pop(0)
                if file_content.type == "dir":
                    contents.extend(repo.get_contents(file_content.path))
                else:
                    print('file_content: {}'.format(file_content))
                    try:
                        data = file_content.decoded_content.decode("utf-8")
                    except:
                        continue
                    else:
                        print('url: {}'.format(GITHUB_URL_PREFIX + repo.full_name + GITHUB_URL_MIDDLE + file_content.path))
                        url = GITHUB_URL_PREFIX + repo.full_name + GITHUB_URL_MIDDLE + file_content.path
                        result = es.delete(
                            index=INDEX, 
                            id=url,
                            doc_type=TYPE
                        )
                        print('elasticsearch result: {}'.format(result))
