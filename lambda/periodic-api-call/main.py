import os
import boto3
import requests
from requests_aws4auth import AWS4Auth

session = requests.Session()
credentials = boto3.session.Session().get_credentials()

print(credentials.access_key)
print(credentials.secret_key)
print(credentials.token)
print(boto3.session.Session().region_name)

session.auth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    boto3.session.Session().region_name,
    'appsync',
    session_token=credentials.token
)

API_URL = os.environ.get('API_URL')

query_code = """
    query MyQuery {
      searchPrograms(word: "Cognito") {
        id
      }
    }
"""

query_article = """
    query MyQuery {
      searchArticles(input: {word: "Cognito", fuzziness: 0}) {
        id
      }
    }
"""

def lambda_handler(event, context):
    print(event)
    
    response = session.request(
        url=API_URL,
        method='POST',
        json={'query': query_code}
    )
    print(response.text)
    
    response = session.request(
        url=API_URL,
        method='POST',
        json={'query': query_article}
    )
    print(response.text)