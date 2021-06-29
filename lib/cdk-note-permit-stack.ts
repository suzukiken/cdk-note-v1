import * as cdk from '@aws-cdk/core';
import * as iam from '@aws-cdk/aws-iam';
import * as s3 from '@aws-cdk/aws-s3';

export class CdkNotePermitStack extends cdk.Stack {
  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    
    const auth_iamrolearn = cdk.Fn.importValue(this.node.tryGetContext('cognito_idpool_auth_iamrolearn_exportname'))
    const auth_iamrole = iam.Role.fromRoleArn(this, 'auth_iamrole', auth_iamrolearn)
    
    const bucketname = cdk.Fn.importValue(this.node.tryGetContext('s3bucketname_exportname'))
    const bucket = s3.Bucket.fromBucketName(this, 'Bucket', bucketname)
    
    auth_iamrole.attachInlinePolicy(new iam.Policy(this, 'policy', {
      statements: [
        new iam.PolicyStatement({
          effect: iam.Effect.ALLOW,
          actions: [
            "s3:PutObject",
            "s3:GetObject",
            "s3:ListBucket",
            "s3:DeleteObject"
          ],
          resources: [
            bucket.bucketArn,
            bucket.bucketArn + "/*"
          ]
        })
      ]
    }))
    
  }
}
