import * as cdk from '@aws-cdk/core';
import * as s3 from '@aws-cdk/aws-s3';
import * as lambda from "@aws-cdk/aws-lambda";
import { PythonFunction } from '@aws-cdk/aws-lambda-python';
import * as events from '@aws-cdk/aws-events';
import { LambdaFunction } from '@aws-cdk/aws-events-targets';
import * as secretsmanager from '@aws-cdk/aws-secretsmanager';

export class CdkNoteFunctionStack extends cdk.Stack {
  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    
    const bucketname = cdk.Fn.importValue(this.node.tryGetContext('s3bucketname_exportname'))
    const bucket = s3.Bucket.fromBucketName(this, 'bucket', bucketname)
    const prefix = this.node.tryGetContext('s3key_articles_prefix')
    const secret_name = this.node.tryGetContext('secretsmanager_secretname')
    const access_token = secretsmanager.Secret.fromSecretNameV2(this, 'Secret', secret_name).secretValue.toString()

    const lambda_function = new PythonFunction(this, "UpdateArticle", {
      entry: "lambda/update-article",
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
    
    bucket.grantReadWrite(lambda_function)
    
    const target = new LambdaFunction(lambda_function)

    const rule = new events.Rule(this, 'Rule', {
     schedule: events.Schedule.rate(cdk.Duration.hours(3)),
     targets: [target],
    })
    
  }
}
