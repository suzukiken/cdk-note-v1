import boto3
import os
import re
from datetime import date
import json
from github import Github
import urllib.parse

'''
このプログラムがやること

Githubのpushをwebhookとして受ける

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
    
    print(urllib.parse.unquote(event['body']))
    
    payload = json.loads(urllib.parse.parse_qs(urllib.parse.unquote(event['body']))['payload'][0])
    print(payload)
    
    repo_full_name = payload['repository']['full_name']
    print(repo_full_name)
    
    repo = g.get_repo(repo_full_name)
    
    # suzukiken/event-action

    # 今のS3の内容を得る
    try:
        get_response = s3.get_object(
            Bucket=BUCKET_NAME,
            Key=KEY_PREFIX + repo.name + '.md',
        )
        s3_contents = get_response['Body'].read().decode('utf-8')
    except:
        s3_contents = ''
    
    print(s3_contents)
        
    # 今のgithubの内容を得る
    
    file = repo.get_contents(GITHUB_PATH)
    github_contents = file.decoded_content.decode("utf-8")

    print(github_contents)
    
    # 差異をS3に反映する
    
    if not s3_contents == github_contents:
        put_response = s3.put_object(
            Bucket=BUCKET_NAME,
            Key=KEY_PREFIX + repo.name + '.md',
            Body=github_contents
        )
        
        print(put_response)
    
'''
{
   "ref":"refs/heads/main",
   "before":"434a4d45f46604bb5bd89db161ac700685849abe",
   "after":"b7b3e1838fa090fed17b01f30403a3cd1be1317c",
   "repository":{
      "id":382050327,
      "node_id":"MDEwOlJlcG9zaXRvcnkzODIwNTAzMjc=",
      "name":"event-action",
      "full_name":"suzukiken/event-action",
      "private":false,
      "owner":{
         "name":"suzukiken",
         "email":"suzukiken@gmail.com",
         "login":"suzukiken",
         "id":557268,
         "node_id":"MDQ6VXNlcjU1NzI2OA==",
         "avatar_url":"https://avatars.githubusercontent.com/u/557268?v=4",
         "gravatar_id":"",
         "url":"https://api.github.com/users/suzukiken",
         "html_url":"https://github.com/suzukiken",
         "followers_url":"https://api.github.com/users/suzukiken/followers",
         "following_url":"https://api.github.com/users/suzukiken/following{/other_user}",
         "gists_url":"https://api.github.com/users/suzukiken/gists{/gist_id}",
         "starred_url":"https://api.github.com/users/suzukiken/starred{/owner}{/repo}",
         "subscriptions_url":"https://api.github.com/users/suzukiken/subscriptions",
         "organizations_url":"https://api.github.com/users/suzukiken/orgs",
         "repos_url":"https://api.github.com/users/suzukiken/repos",
         "events_url":"https://api.github.com/users/suzukiken/events{/privacy}",
         "received_events_url":"https://api.github.com/users/suzukiken/received_events",
         "type":"User",
         "site_admin":false
      },
      "html_url":"https://github.com/suzukiken/event-action",
      "description":"None",
      "fork":false,
      "url":"https://github.com/suzukiken/event-action",
      "forks_url":"https://api.github.com/repos/suzukiken/event-action/forks",
      "keys_url":"https://api.github.com/repos/suzukiken/event-action/keys{/key_id}",
      "collaborators_url":"https://api.github.com/repos/suzukiken/event-action/collaborators{/collaborator}",
      "teams_url":"https://api.github.com/repos/suzukiken/event-action/teams",
      "hooks_url":"https://api.github.com/repos/suzukiken/event-action/hooks",
      "issue_events_url":"https://api.github.com/repos/suzukiken/event-action/issues/events{/number}",
      "events_url":"https://api.github.com/repos/suzukiken/event-action/events",
      "assignees_url":"https://api.github.com/repos/suzukiken/event-action/assignees{/user}",
      "branches_url":"https://api.github.com/repos/suzukiken/event-action/branches{/branch}",
      "tags_url":"https://api.github.com/repos/suzukiken/event-action/tags",
      "blobs_url":"https://api.github.com/repos/suzukiken/event-action/git/blobs{/sha}",
      "git_tags_url":"https://api.github.com/repos/suzukiken/event-action/git/tags{/sha}",
      "git_refs_url":"https://api.github.com/repos/suzukiken/event-action/git/refs{/sha}",
      "trees_url":"https://api.github.com/repos/suzukiken/event-action/git/trees{/sha}",
      "statuses_url":"https://api.github.com/repos/suzukiken/event-action/statuses/{sha}",
      "languages_url":"https://api.github.com/repos/suzukiken/event-action/languages",
      "stargazers_url":"https://api.github.com/repos/suzukiken/event-action/stargazers",
      "contributors_url":"https://api.github.com/repos/suzukiken/event-action/contributors",
      "subscribers_url":"https://api.github.com/repos/suzukiken/event-action/subscribers",
      "subscription_url":"https://api.github.com/repos/suzukiken/event-action/subscription",
      "commits_url":"https://api.github.com/repos/suzukiken/event-action/commits{/sha}",
      "git_commits_url":"https://api.github.com/repos/suzukiken/event-action/git/commits{/sha}",
      "comments_url":"https://api.github.com/repos/suzukiken/event-action/comments{/number}",
      "issue_comment_url":"https://api.github.com/repos/suzukiken/event-action/issues/comments{/number}",
      "contents_url":"https://api.github.com/repos/suzukiken/event-action/contents/{ path}",
      "compare_url":"https://api.github.com/repos/suzukiken/event-action/compare/{base}...{head}",
      "merges_url":"https://api.github.com/repos/suzukiken/event-action/merges",
      "archive_url":"https://api.github.com/repos/suzukiken/event-action/{archive_format}{/ref}",
      "downloads_url":"https://api.github.com/repos/suzukiken/event-action/downloads",
      "issues_url":"https://api.github.com/repos/suzukiken/event-action/issues{/number}",
      "pulls_url":"https://api.github.com/repos/suzukiken/event-action/pulls{/number}",
      "milestones_url":"https://api.github.com/repos/suzukiken/event-action/milestones{/number}",
      "notifications_url":"https://api.github.com/repos/suzukiken/event-action/notifications{?since,all,participating}",
      "labels_url":"https://api.github.com/repos/suzukiken/event-action/labels{/name}",
      "releases_url":"https://api.github.com/repos/suzukiken/event-action/releases{/id}",
      "deployments_url":"https://api.github.com/repos/suzukiken/event-action/deployments",
      "created_at":1625147751,
      "updated_at":"2021-07-01T23:38:19Z",
      "pushed_at":1625183196,
      "git_url":"git://github.com/suzukiken/event-action.git",
      "ssh_url":"git@github.com:suzukiken/event-action.git",
      "clone_url":"https://github.com/suzukiken/event-action.git",
      "svn_url":"https://github.com/suzukiken/event-action",
      "homepage":"None",
      "size":3,
      "stargazers_count":0,
      "watchers_count":0,
      "language":"None",
      "has_issues":true,
      "has_projects":true,
      "has_downloads":true,
      "has_wiki":true,
      "has_pages":false,
      "forks_count":0,
      "mirror_url":"None",
      "archived":false,
      "disabled":false,
      "open_issues_count":0,
      "license":"None",
      "forks":0,
      "open_issues":0,
      "watchers":0,
      "default_branch":"main",
      "stargazers":0,
      "master_branch":"main"
   },
   "pusher":{
      "name":"suzukiken",
      "email":"suzukiken@gmail.com"
   },
   "sender":{
      "login":"suzukiken",
      "id":557268,
      "node_id":"MDQ6VXNlcjU1NzI2OA==",
      "avatar_url":"https://avatars.githubusercontent.com/u/557268?v=4",
      "gravatar_id":"",
      "url":"https://api.github.com/users/suzukiken",
      "html_url":"https://github.com/suzukiken",
      "followers_url":"https://api.github.com/users/suzukiken/followers",
      "following_url":"https://api.github.com/users/suzukiken/following{/other_user}",
      "gists_url":"https://api.github.com/users/suzukiken/gists{/gist_id}",
      "starred_url":"https://api.github.com/users/suzukiken/starred{/owner}{/repo}",
      "subscriptions_url":"https://api.github.com/users/suzukiken/subscriptions",
      "organizations_url":"https://api.github.com/users/suzukiken/orgs",
      "repos_url":"https://api.github.com/users/suzukiken/repos",
      "events_url":"https://api.github.com/users/suzukiken/events{/privacy}",
      "received_events_url":"https://api.github.com/users/suzukiken/received_events",
      "type":"User",
      "site_admin":false
   },
   "created":false,
   "deleted":false,
   "forced":false,
   "base_ref":"None",
   "compare":"https://github.com/suzukiken/event-action/compare/434a4d45f466...b7b3e1838fa0",
   "commits":[
      {
         "id":"b7b3e1838fa090fed17b01f30403a3cd1be1317c",
         "tree_id":"e7946af12b38ba3644bacc7007b7e0b78fb5c9b7",
         "distinct":true,
         "message":"Update README.md",
         "timestamp":"2021-07-02T08:46:36 09:00",
         "url":"https://github.com/suzukiken/event-action/commit/b7b3e1838fa090fed17b01f30403a3cd1be1317c",
         "author":{
            "name":"suzukiken",
            "email":"suzukiken@gmail.com",
            "username":"suzukiken"
         },
         "committer":{
            "name":"GitHub",
            "email":"noreply@github.com",
            "username":"web-flow"
         },
         "added":[
            
         ],
         "removed":[
            
         ],
         "modified":[
            "note/README.md"
         ]
      }
   ],
   "head_commit":{
      "id":"b7b3e1838fa090fed17b01f30403a3cd1be1317c",
      "tree_id":"e7946af12b38ba3644bacc7007b7e0b78fb5c9b7",
      "distinct":true,
      "message":"Update README.md",
      "timestamp":"2021-07-02T08:46:36 09:00",
      "url":"https://github.com/suzukiken/event-action/commit/b7b3e1838fa090fed17b01f30403a3cd1be1317c",
      "author":{
         "name":"suzukiken",
         "email":"suzukiken@gmail.com",
         "username":"suzukiken"
      },
      "committer":{
         "name":"GitHub",
         "email":"noreply@github.com",
         "username":"web-flow"
      },
      "added":[
         
      ],
      "removed":[
         
      ],
      "modified":[
         "note/README.md"
      ]
   }
}
'''