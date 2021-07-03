import * as cdk from '@aws-cdk/core';
import * as s3 from '@aws-cdk/aws-s3';
import * as lambda from "@aws-cdk/aws-lambda";
import { PythonFunction } from '@aws-cdk/aws-lambda-python';
import * as events from '@aws-cdk/aws-events';
import { LambdaFunction } from '@aws-cdk/aws-events-targets';
import * as secretsmanager from '@aws-cdk/aws-secretsmanager';
import { LambdaIntegration, RestApi } from '@aws-cdk/aws-apigateway';
import * as sns from '@aws-cdk/aws-sns';
import { SnsEventSource } from '@aws-cdk/aws-lambda-event-sources';

export class CdkNoteFunctionStack extends cdk.Stack {
  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    
    const bucketname = cdk.Fn.importValue(this.node.tryGetContext('s3bucketname_exportname'))
    const bucket = s3.Bucket.fromBucketName(this, 'bucket', bucketname)
    const prefix = this.node.tryGetContext('s3key_articles_prefix')
    const secret_name = this.node.tryGetContext('secretsmanager_secretname')
    const access_token = secretsmanager.Secret.fromSecretNameV2(this, 'Secret', secret_name).secretValue.toString()
    const es_endpoint = this.node.tryGetContext('elasticsearch_endpoint')
    const es_index = this.node.tryGetContext('elasticsearch_index')
    
    // Webhook
    
    const topic = new sns.Topic(this, 'Topic')
    
    const webhook_function = new PythonFunction(this, "WebhookFunction", {
      entry: "lambda/called-by-webhook",
      index: "main.py",
      handler: "lambda_handler",
      runtime: lambda.Runtime.PYTHON_3_8,
      timeout: cdk.Duration.seconds(10),
      environment: {
        SNS_TOPICARN: topic.topicArn
      }
    })
    
    topic.grantPublish(webhook_function)
    
    const webhook_integration = new LambdaIntegration(webhook_function)
    const api = new RestApi(this, 'RestApi')
    api.root.addMethod('ANY', webhook_integration)
    
    // 定期実行
    
    const periodic_function = new PythonFunction(this, "UpdateArticle", {
      entry: "lambda/update-article-periodically",
      index: "main.py",
      handler: "lambda_handler",
      runtime: lambda.Runtime.PYTHON_3_8,
      timeout: cdk.Duration.seconds(300),
      environment: {
        BUCKET_NAME: bucket.bucketName,
        KEY_PREFIX: prefix,
        GITHUB_ACCESS_TOKEN: access_token
      }
    })
    
    bucket.grantReadWrite(periodic_function)
    
    const target = new LambdaFunction(periodic_function)

    const rule = new events.Rule(this, 'Rule', {
     schedule: events.Schedule.rate(cdk.Duration.hours(3)),
     targets: [target],
    })
    
    // Webhookで実行
    
    const article_by_webhook_function = new PythonFunction(this, "UpdateArticleByWebhook", {
      entry: "lambda/update-article-by-webhook",
      index: "main.py",
      handler: "lambda_handler",
      runtime: lambda.Runtime.PYTHON_3_8,
      timeout: cdk.Duration.seconds(10),
      environment: {
        BUCKET_NAME: bucket.bucketName,
        KEY_PREFIX: prefix,
        GITHUB_ACCESS_TOKEN: access_token
      }
    })
    
    article_by_webhook_function.addEventSource(new SnsEventSource(topic))
    
    // Webhookで実行
    
    const code_by_webhook_function = new PythonFunction(this, "UpdateCodeByWebhook", {
      entry: "lambda/update-code-by-webhook",
      index: "main.py",
      handler: "lambda_handler",
      runtime: lambda.Runtime.PYTHON_3_8,
      timeout: cdk.Duration.seconds(30),
      environment: {
        GITHUB_ACCESS_TOKEN: access_token,
        ENDPOINT: es_endpoint,
        INDEX: es_index
      }
    })
    
    code_by_webhook_function.addEventSource(new SnsEventSource(topic))
    
    new cdk.CfnOutput(this, 'URL', { 
      value: api.url
    })
    
    new cdk.CfnOutput(this, 'TopicArn', { 
      value: topic.topicArn, 
      exportName: this.node.tryGetContext('webhook_topicarn_exportname')
    })
    
  }
}
