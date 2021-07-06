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
import * as iam from "@aws-cdk/aws-iam";
import * as subscriptions from "@aws-cdk/aws-sns-subscriptions";
import * as cloudfront from '@aws-cdk/aws-cloudfront';

export class CdkNoteFunctionStack extends cdk.Stack {
  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    
    const bucketname = cdk.Fn.importValue(this.node.tryGetContext('s3bucketname_exportname'))
    const bucket = s3.Bucket.fromBucketName(this, 'bucket', bucketname)
    const prefix = this.node.tryGetContext('s3key_articles_prefix')
    const secret_name = this.node.tryGetContext('secretsmanager_secretname')
    const access_token = secretsmanager.Secret.fromSecretNameV2(this, 'Secret', secret_name).secretValue.toString()
    const es_endpoint = this.node.tryGetContext('elasticsearch_endpoint')
    const es_domainarn = this.node.tryGetContext('elasticsearch_domainarn')
    const es_index = this.node.tryGetContext('elasticsearch_code_index')
    const summary_prefix = this.node.tryGetContext('s3key_summary_prefix')
    const distribution_id = cdk.Fn.importValue(this.node.tryGetContext('distributionid_exportname'))
    const distribution_domainname = cdk.Fn.importValue(this.node.tryGetContext('distribution_domainname_exportname'))
    
    // distribution for invalidate
    
    const distribution = cloudfront.Distribution.fromDistributionAttributes(this, 'Distribution', {
      distributionId: distribution_id, 
      domainName: distribution_domainname
    })
    
    // S3 event topic
    
    const s3_topicarn = cdk.Fn.importValue(this.node.tryGetContext('s3bucket_topicarn_exportname'))
    const s3_topic = sns.Topic.fromTopicArn(this, 'S3Topic', s3_topicarn)
    
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
    
    // Role for appsync that query Elasticsearch

    const role = new iam.Role(this, "Role", {
      assumedBy: new iam.ServicePrincipal("lambda.amazonaws.com"),
    })

    const policy_statement = new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
    })

    policy_statement.addActions("es:ESHttpPost");
    policy_statement.addActions("es:ESHttpDelete");
    policy_statement.addActions("es:ESHttpHead");
    policy_statement.addActions("es:ESHttpGet");
    policy_statement.addActions("es:ESHttpPut");

    policy_statement.addResources(
      es_domainarn + "/*"
    );

    const policy = new iam.Policy(this, "Policy", {
      statements: [policy_statement],
    })

    role.attachInlinePolicy(policy)
    
    role.addManagedPolicy(
      iam.ManagedPolicy.fromAwsManagedPolicyName(
        "service-role/AWSLambdaBasicExecutionRole"
      )
    )
    
    // 定期実行
    
    const code_periodic_function = new PythonFunction(this, "DeleteCodePeriodically", {
      entry: "lambda/delete-code-periodically",
      index: "main.py",
      handler: "lambda_handler",
      runtime: lambda.Runtime.PYTHON_3_8,
      timeout: cdk.Duration.seconds(300),
      environment: {
        GITHUB_ACCESS_TOKEN: access_token,
        ES_ENDPOINT: es_endpoint,
        ES_CODE_INDEX: es_index
      },
      role: role
    })
    
    const code_target = new LambdaFunction(code_periodic_function)
    
    const article_periodic_function = new PythonFunction(this, "DeleteArticlePeriodically", {
      entry: "lambda/delete-article-periodically",
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
    
    bucket.grantReadWrite(article_periodic_function)
    
    const article_target = new LambdaFunction(article_periodic_function)

    const article_create_periodic_function = new PythonFunction(this, "CreateArticlePeriodically", {
      entry: "lambda/create-article-periodically",
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
    
    bucket.grantReadWrite(article_create_periodic_function)
    
    const article_create_target = new LambdaFunction(article_create_periodic_function)
    
    const article_index_periodic_function = new PythonFunction(this, "CreateArticleIndexPeriodically", {
      entry: "lambda/update-index-periodically",
      index: "main.py",
      handler: "lambda_handler",
      runtime: lambda.Runtime.PYTHON_3_8,
      timeout: cdk.Duration.seconds(30),
      environment: {
        BUCKET_NAME: bucket.bucketName,
        KEY_PREFIX: prefix,
        GITHUB_ACCESS_TOKEN: access_token
      }
    })
    
    bucket.grantReadWrite(article_index_periodic_function)
    
    const article_index_target = new LambdaFunction(article_index_periodic_function)
    
    const rule = new events.Rule(this, 'Rule', {
     schedule: events.Schedule.rate(cdk.Duration.hours(3)),
     targets: [article_target, code_target, article_create_target, article_index_target],
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
    bucket.grantReadWrite(article_by_webhook_function)
    
    // Webhookで実行
    
    const code_by_webhook_function = new PythonFunction(this, "UpdateCodeByWebhook", {
      entry: "lambda/update-code-by-webhook",
      index: "main.py",
      handler: "lambda_handler",
      runtime: lambda.Runtime.PYTHON_3_8,
      timeout: cdk.Duration.seconds(30),
      environment: {
        GITHUB_ACCESS_TOKEN: access_token,
        ES_ENDPOINT: es_endpoint,
        ES_CODE_INDEX: es_index
      },
      role: role
    })
    
    code_by_webhook_function.addEventSource(new SnsEventSource(topic))
    
    // Webhookで実行
    
    const article_from_note_function = new PythonFunction(this, "UpdateArticleFromNote", {
      entry: "lambda/create-article-from-note",
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
    
    article_from_note_function.addEventSource(new SnsEventSource(topic))
    bucket.grantReadWrite(article_from_note_function)
    
    // S3 bucket event
    
    // Role for Elasticsearch

    const es_role = new iam.Role(this, "EsRole", {
      assumedBy: new iam.ServicePrincipal("lambda.amazonaws.com"),
    })

    const es_policy_statement = new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
    })

    es_policy_statement.addActions("es:ESHttpPost");
    es_policy_statement.addActions("es:ESHttpDelete");
    es_policy_statement.addActions("es:ESHttpHead");
    es_policy_statement.addActions("es:ESHttpGet");
    es_policy_statement.addActions("es:ESHttpPut");

    es_policy_statement.addResources(
      es_domainarn + "/*"
    );

    const es_policy = new iam.Policy(this, "EsPolicy", {
      statements: [es_policy_statement],
    })

    es_role.attachInlinePolicy(es_policy)
    
    es_role.addManagedPolicy(
      iam.ManagedPolicy.fromAwsManagedPolicyName(
        "service-role/AWSLambdaBasicExecutionRole"
      )
    )
    
    // Lambda for Elastic Search Index
    
    const trigger_function = new PythonFunction(this, "UpdateIndexFunc", {
      entry: "lambda/update-index",
      index: "main.py",
      handler: "lambda_handler",
      runtime: lambda.Runtime.PYTHON_3_8,
      environment: {
        BUCKET_NAME: bucket.bucketName,
        KEY_PREFIX: prefix,
        ES_ENDPOINT: es_endpoint,
        ES_INDEX: es_index
      },
      role: es_role,
      timeout: cdk.Duration.seconds(30),
    })
    
    bucket.grantReadWrite(trigger_function)
    
    // Lambda for Generate Toppage
    
    const toppage_function = new PythonFunction(this, "TopPageFunc", {
      entry: "lambda/update-toppage",
      index: "main.py",
      handler: "lambda_handler",
      runtime: lambda.Runtime.PYTHON_3_8,
      environment: {
        BUCKET_NAME: bucket.bucketName,
        KEY_ARTICLES_PREFIX: prefix,
        KEY_SUMMARY_PREFIX: summary_prefix
      },
      timeout: cdk.Duration.seconds(30),
    })
    
    bucket.grantReadWrite(toppage_function)
    
    // Lambda for CloudFront Invalidate
    
    // Role for Distribution create_invalidation

    const cf_role = new iam.Role(this, "CfRole", {
      assumedBy: new iam.ServicePrincipal("lambda.amazonaws.com"),
    })

    const cf_policy_statement = new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
    })

    cf_policy_statement.addActions("cloudfront:CreateInvalidation")

    cf_policy_statement.addResources("arn:aws:cloudfront::" + this.account + ":distribution/" + distribution.distributionId)

    const cf_policy = new iam.Policy(this, "CfPolicy", {
      statements: [cf_policy_statement],
    })

    cf_role.attachInlinePolicy(cf_policy)
    
    cf_role.addManagedPolicy(
      iam.ManagedPolicy.fromAwsManagedPolicyName(
        "service-role/AWSLambdaBasicExecutionRole"
      )
    )
    
    const invalidate_function = new PythonFunction(this, "InvalidateFunc", {
      entry: "lambda/invalidate-cloudfront-by-update",
      index: "main.py",
      handler: "lambda_handler",
      runtime: lambda.Runtime.PYTHON_3_8,
      environment: {
        DISTRIBUTION_ID: distribution.distributionId
      },
      role: cf_role,
      timeout: cdk.Duration.seconds(15),
    })
    
    s3_topic.addSubscription(
      new subscriptions.LambdaSubscription(trigger_function)
    )
    
    s3_topic.addSubscription(
      new subscriptions.LambdaSubscription(toppage_function)
    )
    
    s3_topic.addSubscription(
      new subscriptions.LambdaSubscription(invalidate_function)
    )
    
    // Output
    
    new cdk.CfnOutput(this, 'URL', { 
      value: api.url
    })
    
    new cdk.CfnOutput(this, 'TopicArn', { 
      value: topic.topicArn, 
      exportName: this.node.tryGetContext('webhook_topicarn_exportname')
    })
    
  }
}
