import * as cdk from '@aws-cdk/core';
import * as iam from '@aws-cdk/aws-iam';
import * as appsync from '@aws-cdk/aws-appsync';
import * as s3 from '@aws-cdk/aws-s3';

export class CdkNotePermitStack extends cdk.Stack {
  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const unauth_iamrolearn = cdk.Fn.importValue(this.node.tryGetContext('cognito_idpool_unauth_iamrolearn_exportname'))
    const unauth_iamrole = iam.Role.fromRoleArn(this, 'Role', unauth_iamrolearn)
    const graphqlapiid = cdk.Fn.importValue(this.node.tryGetContext('appsync_public_apiid_exportname'))
    const api = appsync.GraphqlApi.fromGraphqlApiAttributes(this, 'Api', { graphqlApiId: graphqlapiid })
    const auth_iamrolearn = cdk.Fn.importValue(this.node.tryGetContext('cognito_idpool_auth_iamrolearn_exportname'))
    const auth_iamrole = iam.Role.fromRoleArn(this, 'AuthRole', auth_iamrolearn)
    const bucketname = cdk.Fn.importValue(this.node.tryGetContext('s3bucketname_exportname'))
    const bucket = s3.Bucket.fromBucketName(this, 'Bucket', bucketname)
    
    unauth_iamrole.attachInlinePolicy(new iam.Policy(this, 'Policy', {
      statements: [
        new iam.PolicyStatement({
          effect: iam.Effect.ALLOW,
          actions: [
            "appsync:GraphQL"
          ],
          resources: [ api.arn + "/*" ]
        })
      ]
    }))
    
    auth_iamrole.attachInlinePolicy(new iam.Policy(this, 'AuthPolicy', {
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