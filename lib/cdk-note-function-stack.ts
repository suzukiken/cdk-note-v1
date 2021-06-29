import * as cdk from '@aws-cdk/core';
import * as s3 from '@aws-cdk/aws-s3';
import * as lambda from "@aws-cdk/aws-lambda";
import { PythonFunction } from '@aws-cdk/aws-lambda-python';
import * as events from '@aws-cdk/aws-events';
import { LambdaFunction } from '@aws-cdk/aws-events-targets';

export class CdkNoteFunctionStack extends cdk.Stack {
  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    
    const bucketname = cdk.Fn.importValue(this.node.tryGetContext('s3bucketname_exportname'))
    const bucket = s3.Bucket.fromBucketName(this, 'bucket', bucketname)

    const lambda_function = new PythonFunction(this, "UpdateArticle", {
      entry: "lambda/update-article",
      index: "main.py",
      handler: "lambda_handler",
      runtime: lambda.Runtime.PYTHON_3_8,
      environment: {
        BUCKET_NAME: bucket.bucketName
      }
    })
    
    const target = new LambdaFunction(lambda_function)

    const rule = new events.Rule(this, 'Rule', {
     schedule: events.Schedule.rate(cdk.Duration.minutes(100)),
     targets: [target],
    })
    
  }
}
