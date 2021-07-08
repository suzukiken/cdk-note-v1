import * as cdk from '@aws-cdk/core';
import * as s3 from '@aws-cdk/aws-s3';
import * as codebuild from '@aws-cdk/aws-codebuild';
import * as codepipeline from '@aws-cdk/aws-codepipeline';
import * as codepipeline_actions from '@aws-cdk/aws-codepipeline-actions';
import * as lambda from '@aws-cdk/aws-lambda';
import { PythonFunction } from '@aws-cdk/aws-lambda-python';
import * as iam from '@aws-cdk/aws-iam';
import * as secretsmanager from '@aws-cdk/aws-secretsmanager';

export class CdkNoteUiDeployStack extends cdk.Stack {
  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    
    const repository = this.node.tryGetContext('github_repository_name')
    const owner = this.node.tryGetContext('github_owner_name')
    const branch = this.node.tryGetContext('github_branch_name')
    const smname = this.node.tryGetContext('github_connection_codestararn_smsecretname')

    const DISTRIBUTION_ID = cdk.Fn.importValue(this.node.tryGetContext('distributionid_exportname'))
    const BUCKETNAME = cdk.Fn.importValue(this.node.tryGetContext('s3bucketname_exportname'))
    
    const codestararn = secretsmanager.Secret.fromSecretNameV2(this, 'secret', smname).secretValue.toString()
    
    // bucket
    
    const bucket = s3.Bucket.fromBucketName(this, 'bucket', BUCKETNAME)
    
    // code pipeline
    
    const environmentVariables = {
      COGNITO_IDPOOL_ID: { value: cdk.Fn.importValue(this.node.tryGetContext('cognito_idpool_id_exportname')) },
      COGNITO_USERPOOL_ID: { value: cdk.Fn.importValue(this.node.tryGetContext('cognito_userpool_id_exportname')) },
      COGNITO_USERPOOL_WEBCLIENT_ID: { value: cdk.Fn.importValue(this.node.tryGetContext('cognito_userpool_webclient_id_exportname')) },
      APPSYNC_GRAPHQL_URL: { value: cdk.Fn.importValue(this.node.tryGetContext('appsync_public_apiurl_exportname')) }
    }
    
    const pipeline_project = new codebuild.PipelineProject(this, 'pipeline_project', {
      buildSpec: codebuild.BuildSpec.fromSourceFilename('buildspec.yml'), // this line is not necessary. 
      environmentVariables: environmentVariables
    })
    
    const source_output = new codepipeline.Artifact();
    const build_output = new codepipeline.Artifact();
    
    // To use GitHub version 2 source action
    // https://github.com/aws/aws-cdk/issues/11582
    const source_action = new codepipeline_actions.BitBucketSourceAction({
      actionName: id + '-sourceaction',
      owner: owner,
      repo: repository,
      connectionArn: codestararn,
      output: source_output,
      branch: branch,
    })

    const build_action = new codepipeline_actions.CodeBuildAction({
      actionName: id + '-buildaction',
      project: pipeline_project,
      input: source_output,
      outputs: [build_output],
      executeBatchBuild: false,
    })
    
    const deploy_action = new codepipeline_actions.S3DeployAction({
      actionName: id + '-deployaction',
      input: build_output,
      bucket: bucket,
    })

    // Lambda to invalidate CloudFront cache
    
    const invalidate_role = new iam.Role(this, "invalidate_role", {
      assumedBy: new iam.ServicePrincipal("lambda.amazonaws.com"),
    })

    invalidate_role.attachInlinePolicy(new iam.Policy(this, 'cloudfront_policy', {
      statements: [
        new iam.PolicyStatement({
          effect: iam.Effect.ALLOW,
          actions: [
            "cloudfront:CreateInvalidation",
            "cloudfront:GetDistribution"
          ],
          resources: [
            "*"
          ]
        })
      ]
    }));
    
    invalidate_role.addManagedPolicy(
      iam.ManagedPolicy.fromAwsManagedPolicyName(
        "AWSCodePipelineCustomActionAccess",
      )
    )
    
    invalidate_role.addManagedPolicy(
      iam.ManagedPolicy.fromAwsManagedPolicyName(
        "service-role/AWSLambdaBasicExecutionRole"
      )
    )
    
    // Lambda of Dynamo Stream Poller
    
    const invalidate_function = new PythonFunction(this, "invalidate_function", {
      entry: "lambda/invalidate-cloudfront",
      index: "main.py",
      handler: "lambda_handler",
      runtime: lambda.Runtime.PYTHON_3_8,
      role: invalidate_role,
      timeout: cdk.Duration.minutes(5),
      environment: {
        DISTRIBUTION_ID: DISTRIBUTION_ID
      }
    })
    
    const invalidate_action = new codepipeline_actions.LambdaInvokeAction({
      lambda: invalidate_function,
      actionName: id + '-invalidate-action'
    })

    const pipeline = new codepipeline.Pipeline(this, 'pipeline', {
      pipelineName: id + '-pipeline',
      stages: [
        {
          stageName: 'source',
          actions: [source_action],
        },
        {
          stageName: 'build',
          actions: [build_action],
        },
        {
          stageName: 'deploy',
          actions: [deploy_action, invalidate_action],
        }
      ],
    })
    
    new cdk.CfnOutput(this, 'Params', { 
      value: JSON.stringify(environmentVariables)
    })
    
  }
}
