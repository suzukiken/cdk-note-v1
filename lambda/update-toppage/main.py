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

tiexp = 'title = "(.+?)"'
tgexp = 'tags = \[(.+?)\]'
dtexp = 'date = "(.+?)"'
upexp = 'update = "(.+?)"'
ctexp = 'category = "(.+?)"'
coexp = '\n[+]{3}\n(.*)'


def serialize(anyobj):
    if isinstance(anyobj, (datetime, date)):
        return anyobj.isoformat()
    raise TypeError ('not date')


def lambda_handler(event, context):
    print(event)
    
    # 今のS3の内容を得る
    
    contents = {}
    
    list_response = s3.list_objects_v2(
        Bucket=BUCKET_NAME,
        Prefix=KEY_ARTICLES_PREFIX
    )
    
    for content in list_response['Contents']:
        
        key = content['Key']
        
        if not key.endswith('.md'):
            continue
        
        get_response = s3.get_object(
            Bucket=BUCKET_NAME,
            Key=key,
        )
        
        filename = key.replace(KEY_ARTICLES_PREFIX, '')

        try:
            text = get_response['Body'].read().decode('utf-8')

            mat = re.search(tiexp, text)
            if mat:
                title = mat.group(1)
                
            mat = re.search(tgexp, text)
            if mat:
                found = mat.group(1)
                tags = [stg.replace('"', '').strip() for stg in found.split(",")]
                
            mat = re.search(dtexp, text)
            if mat:
                found = mat.group(1)
                dte = date.fromisoformat(found)
            
            mat = re.search(upexp, text)
            if mat:
                upd = mat.group(1)
                
            mat = re.search(ctexp, text)
            if mat:
                category = mat.group(1)
            
            mat = re.search(coexp, text, flags=re.DOTALL)
            if mat:
                fco = mat.group(1)
            
            contents[article_name] = {
                'filename': filename,
                'title': title,
                'category': category,
                'tags': tags,
                'date': dte,
                'update': upd,
                'content': fco,
            }
            
        except:
            continue
    
    titles = []
    
    for k in contents:
        titles.append({
            'filename': contents[k]['filename'],
            'title': contents[k]['title'],
            'category': contents[k]['category'],
            'tags': contents[k]['tags'],
            'date': contents[k]['date'],
            'update': contents[k]['update']
        })
        
    put_response = s3.put_object(
        Bucket=BUCKET_NAME,
        Key=TITLES_KEY,
        Body=json.dumps(titles, ensure_ascii=False, default=serialize)
    )
    
    print(put_response)
    
