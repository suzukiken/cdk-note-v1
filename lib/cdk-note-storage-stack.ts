import * as cdk from '@aws-cdk/core';
import * as s3 from "@aws-cdk/aws-s3";
import * as s3n from '@aws-cdk/aws-s3-notifications';
import * as sns from '@aws-cdk/aws-sns';

export class CdkNoteStrageStack extends cdk.Stack {
  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    
    const PREFIX = this.node.tryGetContext('s3key_articles_prefix')

    // bucket
    
    const bucket = new s3.Bucket(this, 'Bucket', {
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      versioned: false,
      publicReadAccess: true,
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
    
    // Bucket Event Notification
    
    const topic = new sns.Topic(this, 'Topic')

    bucket.addEventNotification(
      s3.EventType.OBJECT_REMOVED,
      new s3n.SnsDestination(topic),
      { 
        prefix: PREFIX, 
        suffix: '.json' 
      }
    )
    
    bucket.addEventNotification(
      s3.EventType.OBJECT_CREATED,
      new s3n.SnsDestination(topic),
      { 
        prefix: PREFIX, 
        suffix: '.json' 
      }
    )
    
    new cdk.CfnOutput(this, 'BucketName', { 
      exportName: this.node.tryGetContext('s3bucketname_exportname'), 
      value: bucket.bucketName,
    })
    
    new cdk.CfnOutput(this, 'TopicArn', { 
      exportName: this.node.tryGetContext('s3bucket_topicarn_exportname'), 
      value: topic.topicArn,
    })
  }
}


