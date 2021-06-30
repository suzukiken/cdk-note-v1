import * as cdk from '@aws-cdk/core';
import * as s3 from "@aws-cdk/aws-s3";
import * as lambda from "@aws-cdk/aws-lambda";
import { PythonFunction } from '@aws-cdk/aws-lambda-python';
import { S3EventSource } from '@aws-cdk/aws-lambda-event-sources';

export class CdkNoteStrageStack extends cdk.Stack {
  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    
    const prefix = this.node.tryGetContext('s3key_articles_prefix')
    
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
        prefix: prefix,
        suffix: '.md'
      }]
    })
    
    // Lambda for Elastic Search Index
    
    const trigger_function = new PythonFunction(this, "UpdateIndexFunc", {
      entry: "lambda/update-index",
      index: "main.py",
      handler: "lambda_handler",
      runtime: lambda.Runtime.PYTHON_3_8,
      environment: {
        BUCKET_NAME: bucket.bucketName
      }
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


