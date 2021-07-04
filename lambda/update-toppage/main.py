import boto3
import os
import re
from datetime import date, datetime
import json

'''
このプログラムがやること

S3のコンテンツが更新されると呼び出される

S3のバケットに置かれたmdファイルはHugoのFront Matterがついたmarkdownとなっている
そこからタイトルやタグを取り出して
まだ決めていないが何らかのルールに沿ってそれを必要なところに並べてトップページを作る。
そのルールはいずれはコンフィグファイルのようなものを参照しておすすめコンテンツを左コラムに配置するとか、
カテゴリで分けて表示するとか、最初のタグで分けて表示するとかしたいと思っている。
しかしそんなコンフィグファイルはまだ作っていないので、とりあえず今のところはコンテンツの更新日順に降順で並べるという程度にしておく。

'''

BUCKET_NAME = os.environ.get('BUCKET_NAME')
KEY_ARTICLES_PREFIX = os.environ.get('KEY_ARTICLES_PREFIX')
KEY_SUMMARY_PREFIX = os.environ.get('KEY_SUMMARY_PREFIX')

TITLES_KEY = KEY_SUMMARY_PREFIX + 'titles.json'

s3 = boto3.client('s3')

def serialize(anyobj):
    if isinstance(anyobj, (datetime, date)):
        return anyobj.isoformat()
    raise TypeError ('not date')


def lambda_handler(event, context):
    print(event)
    
    # 今のS3の内容を得る
    
    contents = []
    
    list_response = s3.list_objects_v2(
        Bucket=BUCKET_NAME,
        Prefix=KEY_ARTICLES_PREFIX
    )
    
    for content in list_response['Contents']:
        
        key = content['Key']
        
        print(key)
        
        if not key.endswith('.json'):
            continue
        
        get_response = s3.get_object(
            Bucket=BUCKET_NAME,
            Key=key,
        )
        
        try:
            content = json.loads(get_response['Body'].read().decode('utf-8'))
            content['content'] = content['content'][:100]
            contents.append(content)
        except:
            continue
    
    put_response = s3.put_object(
        Bucket=BUCKET_NAME,
        Key=TITLES_KEY,
        Body=json.dumps(contents, ensure_ascii=False, default=serialize)
    )
    
    print(put_response)
    
