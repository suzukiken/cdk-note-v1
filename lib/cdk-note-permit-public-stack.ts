import * as cdk from '@aws-cdk/core';
import * as iam from '@aws-cdk/aws-iam';
import * as appsync from '@aws-cdk/aws-appsync';

export class CdkNotePermitPublicStack extends cdk.Stack {
  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const iamrolearn = cdk.Fn.importValue(this.node.tryGetContext('cognito_idpool_unauth_iamrolearn_exportname'))
    const iamrole = iam.Role.fromRoleArn(this, 'Role', iamrolearn)
    const graphqlapiid = cdk.Fn.importValue(this.node.tryGetContext('appsync_public_apiid_exportname'))
    const api = appsync.GraphqlApi.fromGraphqlApiAttributes(this, 'Api', { graphqlApiId: graphqlapiid })
    
    iamrole.attachInlinePolicy(new iam.Policy(this, 'Policy', {
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
    
  }
}