import * as cdk from '@aws-cdk/core';
import * as s3 from "@aws-cdk/aws-s3";
import * as lambda from "@aws-cdk/aws-lambda";
import { PythonFunction } from '@aws-cdk/aws-lambda-python';
import { S3EventSource } from '@aws-cdk/aws-lambda-event-sources';
import * as iam from "@aws-cdk/aws-iam";

export class CdkNoteStrageStack extends cdk.Stack {
  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    
    const PREFIX = this.node.tryGetContext('s3key_articles_prefix')
    const ES_ENDPOINT = this.node.tryGetContext('elasticsearch_endpoint')
    const ES_INDEX = this.node.tryGetContext('elasticsearch_index')
    const ES_DOMAIN_ARN = this.node.tryGetContext('elasticsearch_domainarn')
    
    // bucket
    
    const bucket = new s3.Bucket(this, 'Bucket', {
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      versioned: true,
      cors: [
        {
          allowedMethods: [
            s3.HttpMethods.HEAD,
            s3.HttpMethods.GET,
            s3.HttpMethods.PUT,
            s3.HttpMethods.POST,
            s3.HttpMethods.DELETE,
          ],
          allowedOrigins: ["*"],
          allowedHeaders: ["*"],
          exposedHeaders: [
            "x-amz-server-side-encryption",
            "x-amz-request-id",
            "x-amz-id-2",
            "ETag",
          ],
          maxAge: 3000,
        },
      ],
    })
    
    const s3_eventsource = new S3EventSource(bucket, {
      events: [ 
        s3.EventType.OBJECT_CREATED,
        s3.EventType.OBJECT_REMOVED
      ],
      filters: [{ 
        prefix: PREFIX,
        suffix: '.md'
      }]
    })
    
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
      ES_DOMAIN_ARN + "/*"
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
    
    // Lambda for Elastic Search Index
    
    const trigger_function = new PythonFunction(this, "UpdateIndexFunc", {
      entry: "lambda/update-index",
      index: "main.py",
      handler: "lambda_handler",
      runtime: lambda.Runtime.PYTHON_3_8,
      environment: {
        BUCKET_NAME: bucket.bucketName,
        KEY_PREFIX: PREFIX,
        ES_ENDPOINT: ES_ENDPOINT,
        ES_INDEX: ES_INDEX
      },
      role: role
    })
    
    trigger_function.addEventSource(s3_eventsource)
    bucket.grantReadWrite(trigger_function)
    
    
    // Lambda for Generate Toppage
    /*
    const toppage_function = new PythonFunction(this, "TopPageFunc", {
      entry: "lambda/update-toppage",
      index: "main.py",
      handler: "lambda_handler",
      runtime: lambda.Runtime.PYTHON_3_8,
      environment: {
        BUCKET_NAME: bucket.bucketName
      }
    })
    
    toppage_function.addEventSource(s3_eventsource)
    bucket.grantReadWrite(toppage_function)
    */
    new cdk.CfnOutput(this, 'BucketName', { 
      exportName: this.node.tryGetContext('s3bucketname_exportname'), 
      value: bucket.bucketName,
    })
  }
}


