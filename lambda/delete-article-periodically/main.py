import boto3
import os
import re
from datetime import date
import json
from github import Github

'''
このプログラムがやること

定期的に呼び出され
自分のGithubの公開されたリポジトリを総浚いして
そのリポジトリの中にあるnote/README.mdとS3のバケットを比較して
GithubにないものはS3からも削除する
'''

BUCKET_NAME = os.environ.get('BUCKET_NAME')
KEY_PREFIX = os.environ.get('KEY_PREFIX')
GITHUB_ACCESS_TOKEN = os.environ.get('GITHUB_ACCESS_TOKEN')

s3 = boto3.client('s3')
g = Github(GITHUB_ACCESS_TOKEN)

GITHUB_PATH = "note/README.md"
GITHUB_BRANCH = "master"
GITHUB_OWNER = "suzukiken"

def lambda_handler(event, context):
    print(event)
    
    # 今のS3の内容を得る
    
    s3_contents = []
    
    list_response = s3.list_objects_v2(
        Bucket=BUCKET_NAME,
        Prefix=KEY_PREFIX
    )
    
    for content in list_response['Contents']:
        if not content['Key'].endswith('.json'):
            continue
        filename = content['Key'].replace(KEY_PREFIX, '')
        if filename:
            s3_contents.append(filename)

    print(s3_contents)
        
    # 今のgithubの内容を得る
    
    github_contents = []
    
    for repo in g.get_user().get_repos():
        if repo.full_name.startswith(GITHUB_OWNER + '/') and not repo.private:
            github_contents.append(repo.name + '.json')
    
    print(github_contents)

    # 内容を比較して差異を抽出する
    
    # TODO: github側でリポジトリの削除などで、S3にはデータがあるがgithubにはすでにデータがないという場合の対応
    
    diff = []
    
    for key in s3_contents:
        if not key in github_contents:
            diff.append(key)
        
    print(diff)
    
    # 差異をS3に反映する
    
    for key in diff:
        response = s3.delete_object(
            Bucket=BUCKET_NAME,
            Key=KEY_PREFIX + key
        )
        
        print(response)
    