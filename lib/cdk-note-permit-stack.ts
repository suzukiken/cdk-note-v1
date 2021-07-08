import * as cdk from '@aws-cdk/core';
import * as iam from '@aws-cdk/aws-iam';
import * as appsync from '@aws-cdk/aws-appsync';

export class CdkNotePermitStack extends cdk.Stack {
  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const unauth_iamrolearn = cdk.Fn.importValue(this.node.tryGetContext('cognito_idpool_unauth_iamrolearn_exportname'))
    const unauth_iamrole = iam.Role.fromRoleArn(this, 'Role', unauth_iamrolearn)
    const graphqlapiid = cdk.Fn.importValue(this.node.tryGetContext('appsync_public_apiid_exportname'))
    const api = appsync.GraphqlApi.fromGraphqlApiAttributes(this, 'Api', { graphqlApiId: graphqlapiid })
    
    const api_policy = new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        "appsync:GraphQL"
      ],
      resources: [ api.arn + "/*" ]
    })
    
    unauth_iamrole.attachInlinePolicy(new iam.Policy(this, 'Policy', {
      statements: [
        api_policy
      ]
    }))
    
  }
}