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
そのリポジトリの中にあるnote/README.mdをS3のバケットにコピーする。
（すでに同じ内容がある場合は上書きしない。
上書きすると別のLambdaに通知されてElasticSearchのインデックス更新が無駄に行われてしまうため。）

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
    
    s3_contents = {}
    
    list_response = s3.list_objects_v2(
        Bucket=BUCKET_NAME,
        Prefix=KEY_PREFIX
    )
    
    for content in list_response['Contents']:
        
        filename = content['Key']
        
        if not filename.endswith('.md'):
            continue
        
        get_response = s3.get_object(
            Bucket=BUCKET_NAME,
            Key=filename,
        )
        
        key = filename.replace(KEY_PREFIX, '').replace('.md', '')

        try:
            text = get_response['Body'].read().decode('utf-8')
            s3_contents[key] = text
        except:
            continue
    
    print(s3_contents)
        
    # 今のgithubの内容を得る
    
    github_contents = {}
    
    for repo in g.get_user().get_repos():
        if repo.full_name.startswith(GITHUB_OWNER + '/') and not repo.private:
            try:
                file = repo.get_contents(GITHUB_PATH)
            except:
                continue
            else:
                data = file.decoded_content.decode("utf-8")
                github_contents[repo.name] = data
                # TODO: URLのリンクが相対だった場合にはそれを置き換える
    
    print(github_contents)

    # 内容を比較して差異を抽出する
    
    # TODO: github側でリポジトリの削除などで、S3にはデータがあるがgithubにはすでにデータがないという場合の対応
    
    diff = {}
    
    for key in github_contents:
        if key in s3_contents:
            if s3_contents[key] == github_contents[key]:
                continue
        diff[key] = github_contents[key]
        
    print(diff)
    
    # 差異をS3に反映する
    
    for key in diff:
        put_response = s3.put_object(
            Bucket=BUCKET_NAME,
            Key=KEY_PREFIX + key + '.md',
            Body=diff[key]
        )
        
        print(put_response)
    

