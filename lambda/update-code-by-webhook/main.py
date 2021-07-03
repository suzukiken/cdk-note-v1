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

Githubのpushをwebhook経由のSNSメッセージとして受ける

Githubからそのリポジトリのコードを得てそれをElasticsearchに投入する
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
    
    for record in event['Records']:
        if record['EventSource'] != 'aws:sns':
            continue
        
        message = json.loads(record['Sns']['Message'])
        repository = message['repository']
        full_name = repository['full_name']
        repo = g.get_repo(full_name)
        
        # githubの内容を得る
        
        if repo.private:
            return
        
        try:
            contents = repo.get_contents(GITHUB_PATH)
            '''
            while contents:
                file_content = contents.pop(0)
                if file_content.type == "dir":
                    contents.extend(repo.get_contents(file_content.path))
                else:
                    print(file_content)
                    try:
                        data = file_content.decoded_content.decode("utf-8")
                    except:
                        continue
                    else:
                        res = es.index(
                            index=INDEX, 
                            id=file_content.path, 
                            body={
                                'url': GITHUB_URL_PREFIX + repo.full_name + GITHUB_URL_MIDDLE + file_content.path,
                                'code': data
                            }, 
                            doc_type=TYPE
                        )
                        print(res)
            '''
        except:
            pass
        else:
            print('--------------------')
            print(contents)

    
'''
{
   "Records":[
      {
         "EventSource":"aws:sns",
         "EventVersion":"1.0",
         "EventSubscriptionArn":"arn:aws:sns:ap-northeast-1:656169322665:CdkNoteFunctionStack-TopicBFC7AF6E-B4HS0KLQH79J:ad2c9bd8-7974-4a81-89a6-26fd31d0db4a",
         "Sns":{
            "Type":"Notification",
            "MessageId":"b060f10f-0d7c-5194-a203-a856a18323ce",
            "TopicArn":"arn:aws:sns:ap-northeast-1:656169322665:CdkNoteFunctionStack-TopicBFC7AF6E-B4HS0KLQH79J",
            "Subject":"None",
            "Message":"{\"ref\":\"refs/heads/main\",\"before\":\"434a4d45f46604bb5bd89db161ac700685849abe\",\"after\":\"b7b3e1838fa090fed17b01f30403a3cd1be1317c\",\"repository\":{\"id\":382050327,\"node_id\":\"MDEwOlJlcG9zaXRvcnkzODIwNTAzMjc=\",\"name\":\"event-action\",\"full_name\":\"suzukiken/event-action\",\"private\":false,\"owner\":{\"name\":\"suzukiken\",\"email\":\"suzukiken@gmail.com\",\"login\":\"suzukiken\",\"id\":557268,\"node_id\":\"MDQ6VXNlcjU1NzI2OA==\",\"avatar_url\":\"https://avatars.githubusercontent.com/u/557268?v=4\",\"gravatar_id\":\"\",\"url\":\"https://api.github.com/users/suzukiken\",\"html_url\":\"https://github.com/suzukiken\",\"followers_url\":\"https://api.github.com/users/suzukiken/followers\",\"following_url\":\"https://api.github.com/users/suzukiken/following{/other_user}\",\"gists_url\":\"https://api.github.com/users/suzukiken/gists{/gist_id}\",\"starred_url\":\"https://api.github.com/users/suzukiken/starred{/owner}{/repo}\",\"subscriptions_url\":\"https://api.github.com/users/suzukiken/subscriptions\",\"organizations_url\":\"https://api.github.com/users/suzukiken/orgs\",\"repos_url\":\"https://api.github.com/users/suzukiken/repos\",\"events_url\":\"https://api.github.com/users/suzukiken/events{/privacy}\",\"received_events_url\":\"https://api.github.com/users/suzukiken/received_events\",\"type\":\"User\",\"site_admin\":false},\"html_url\":\"https://github.com/suzukiken/event-action\",\"description\":null,\"fork\":false,\"url\":\"https://github.com/suzukiken/event-action\",\"forks_url\":\"https://api.github.com/repos/suzukiken/event-action/forks\",\"keys_url\":\"https://api.github.com/repos/suzukiken/event-action/keys{/key_id}\",\"collaborators_url\":\"https://api.github.com/repos/suzukiken/event-action/collaborators{/collaborator}\",\"teams_url\":\"https://api.github.com/repos/suzukiken/event-action/teams\",\"hooks_url\":\"https://api.github.com/repos/suzukiken/event-action/hooks\",\"issue_events_url\":\"https://api.github.com/repos/suzukiken/event-action/issues/events{/number}\",\"events_url\":\"https://api.github.com/repos/suzukiken/event-action/events\",\"assignees_url\":\"https://api.github.com/repos/suzukiken/event-action/assignees{/user}\",\"branches_url\":\"https://api.github.com/repos/suzukiken/event-action/branches{/branch}\",\"tags_url\":\"https://api.github.com/repos/suzukiken/event-action/tags\",\"blobs_url\":\"https://api.github.com/repos/suzukiken/event-action/git/blobs{/sha}\",\"git_tags_url\":\"https://api.github.com/repos/suzukiken/event-action/git/tags{/sha}\",\"git_refs_url\":\"https://api.github.com/repos/suzukiken/event-action/git/refs{/sha}\",\"trees_url\":\"https://api.github.com/repos/suzukiken/event-action/git/trees{/sha}\",\"statuses_url\":\"https://api.github.com/repos/suzukiken/event-action/statuses/{sha}\",\"languages_url\":\"https://api.github.com/repos/suzukiken/event-action/languages\",\"stargazers_url\":\"https://api.github.com/repos/suzukiken/event-action/stargazers\",\"contributors_url\":\"https://api.github.com/repos/suzukiken/event-action/contributors\",\"subscribers_url\":\"https://api.github.com/repos/suzukiken/event-action/subscribers\",\"subscription_url\":\"https://api.github.com/repos/suzukiken/event-action/subscription\",\"commits_url\":\"https://api.github.com/repos/suzukiken/event-action/commits{/sha}\",\"git_commits_url\":\"https://api.github.com/repos/suzukiken/event-action/git/commits{/sha}\",\"comments_url\":\"https://api.github.com/repos/suzukiken/event-action/comments{/number}\",\"issue_comment_url\":\"https://api.github.com/repos/suzukiken/event-action/issues/comments{/number}\",\"contents_url\":\"https://api.github.com/repos/suzukiken/event-action/contents/{ path}\",\"compare_url\":\"https://api.github.com/repos/suzukiken/event-action/compare/{base}...{head}\",\"merges_url\":\"https://api.github.com/repos/suzukiken/event-action/merges\",\"archive_url\":\"https://api.github.com/repos/suzukiken/event-action/{archive_format}{/ref}\",\"downloads_url\":\"https://api.github.com/repos/suzukiken/event-action/downloads\",\"issues_url\":\"https://api.github.com/repos/suzukiken/event-action/issues{/number}\",\"pulls_url\":\"https://api.github.com/repos/suzukiken/event-action/pulls{/number}\",\"milestones_url\":\"https://api.github.com/repos/suzukiken/event-action/milestones{/number}\",\"notifications_url\":\"https://api.github.com/repos/suzukiken/event-action/notifications{?since,all,participating}\",\"labels_url\":\"https://api.github.com/repos/suzukiken/event-action/labels{/name}\",\"releases_url\":\"https://api.github.com/repos/suzukiken/event-action/releases{/id}\",\"deployments_url\":\"https://api.github.com/repos/suzukiken/event-action/deployments\",\"created_at\":1625147751,\"updated_at\":\"2021-07-01T23:38:19Z\",\"pushed_at\":1625183196,\"git_url\":\"git://github.com/suzukiken/event-action.git\",\"ssh_url\":\"git@github.com:suzukiken/event-action.git\",\"clone_url\":\"https://github.com/suzukiken/event-action.git\",\"svn_url\":\"https://github.com/suzukiken/event-action\",\"homepage\":null,\"size\":3,\"stargazers_count\":0,\"watchers_count\":0,\"language\":null,\"has_issues\":true,\"has_projects\":true,\"has_downloads\":true,\"has_wiki\":true,\"has_pages\":false,\"forks_count\":0,\"mirror_url\":null,\"archived\":false,\"disabled\":false,\"open_issues_count\":0,\"license\":null,\"forks\":0,\"open_issues\":0,\"watchers\":0,\"default_branch\":\"main\",\"stargazers\":0,\"master_branch\":\"main\"},\"pusher\":{\"name\":\"suzukiken\",\"email\":\"suzukiken@gmail.com\"},\"sender\":{\"login\":\"suzukiken\",\"id\":557268,\"node_id\":\"MDQ6VXNlcjU1NzI2OA==\",\"avatar_url\":\"https://avatars.githubusercontent.com/u/557268?v=4\",\"gravatar_id\":\"\",\"url\":\"https://api.github.com/users/suzukiken\",\"html_url\":\"https://github.com/suzukiken\",\"followers_url\":\"https://api.github.com/users/suzukiken/followers\",\"following_url\":\"https://api.github.com/users/suzukiken/following{/other_user}\",\"gists_url\":\"https://api.github.com/users/suzukiken/gists{/gist_id}\",\"starred_url\":\"https://api.github.com/users/suzukiken/starred{/owner}{/repo}\",\"subscriptions_url\":\"https://api.github.com/users/suzukiken/subscriptions\",\"organizations_url\":\"https://api.github.com/users/suzukiken/orgs\",\"repos_url\":\"https://api.github.com/users/suzukiken/repos\",\"events_url\":\"https://api.github.com/users/suzukiken/events{/privacy}\",\"received_events_url\":\"https://api.github.com/users/suzukiken/received_events\",\"type\":\"User\",\"site_admin\":false},\"created\":false,\"deleted\":false,\"forced\":false,\"base_ref\":null,\"compare\":\"https://github.com/suzukiken/event-action/compare/434a4d45f466...b7b3e1838fa0\",\"commits\":[{\"id\":\"b7b3e1838fa090fed17b01f30403a3cd1be1317c\",\"tree_id\":\"e7946af12b38ba3644bacc7007b7e0b78fb5c9b7\",\"distinct\":true,\"message\":\"Update README.md\",\"timestamp\":\"2021-07-02T08:46:36 09:00\",\"url\":\"https://github.com/suzukiken/event-action/commit/b7b3e1838fa090fed17b01f30403a3cd1be1317c\",\"author\":{\"name\":\"suzukiken\",\"email\":\"suzukiken@gmail.com\",\"username\":\"suzukiken\"},\"committer\":{\"name\":\"GitHub\",\"email\":\"noreply@github.com\",\"username\":\"web-flow\"},\"added\":[],\"removed\":[],\"modified\":[\"note/README.md\"]}],\"head_commit\":{\"id\":\"b7b3e1838fa090fed17b01f30403a3cd1be1317c\",\"tree_id\":\"e7946af12b38ba3644bacc7007b7e0b78fb5c9b7\",\"distinct\":true,\"message\":\"Update README.md\",\"timestamp\":\"2021-07-02T08:46:36 09:00\",\"url\":\"https://github.com/suzukiken/event-action/commit/b7b3e1838fa090fed17b01f30403a3cd1be1317c\",\"author\":{\"name\":\"suzukiken\",\"email\":\"suzukiken@gmail.com\",\"username\":\"suzukiken\"},\"committer\":{\"name\":\"GitHub\",\"email\":\"noreply@github.com\",\"username\":\"web-flow\"},\"added\":[],\"removed\":[],\"modified\":[\"note/README.md\"]}}",
            "Timestamp":"2021-07-03T00:09:35.971Z",
            "SignatureVersion":"1",
            "Signature":"K4zidF0SfNOE/x/eO1KTEVHOOh5/xgY7s/kntEnvO02qS5O1OSVCg9NXPFsF6nwZ0IaLam7aejS8OBCrdGJBwMFOsFvPH43f7nEUiE7peAQTAo7YPW6780auQ3Y2noqNj89c2zNCTvLgLo1yyLpKLaK1fT/8hVZYm6X1F7p4hVFUzcQrVGRh00S4UuqqGD5hQGlQjLlt71r8UXsgMncv7L5e2PoXNJ9ajl+p51/QUS16W6uzvqFrpxftAWuk4t2rheT597bEJkrAxP4y06uDMLquUuqiQUIqdQdLiVTOCyZT34eqApUqTs4sFj13mQheoKbLTgK9plqPq2NZFLI6Ng==",
            "SigningCertUrl":"https://sns.ap-northeast-1.amazonaws.com/SimpleNotificationService-010a507c1833636cd94bdb98bd93083a.pem",
            "UnsubscribeUrl":"https://sns.ap-northeast-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:ap-northeast-1:656169322665:CdkNoteFunctionStack-TopicBFC7AF6E-B4HS0KLQH79J:ad2c9bd8-7974-4a81-89a6-26fd31d0db4a",
            "MessageAttributes":{
               
            }
         }
      }
   ]
}
'''