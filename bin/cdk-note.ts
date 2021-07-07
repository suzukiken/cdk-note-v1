#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from '@aws-cdk/core';
import { CdkNoteStack } from '../lib/cdk-note-stack';
import { CdkNoteStrageStack } from '../lib/cdk-note-storage-stack';
import { CdkNoteFunctionStack } from '../lib/cdk-note-function-stack';
import { CdkNoteDistributionStack } from '../lib/cdk-note-distribution-stack';
import { CdkNoteApiPublicStack } from '../lib/cdk-note-api-public-stack';
import { CdkNotePermitStack } from '../lib/cdk-note-permit-stack';
import { CdkNoteUiDeployStack } from '../lib/cdk-note-ui-deploy-stack';


const app = new cdk.App();
new CdkNoteStack(app, 'CdkNoteStack', {
  env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: process.env.CDK_DEFAULT_REGION },
});

new CdkNoteStrageStack(app, 'CdkNoteStrageStack', {
  env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: process.env.CDK_DEFAULT_REGION },
});

new CdkNoteFunctionStack(app, 'CdkNoteFunctionStack', {
  env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: process.env.CDK_DEFAULT_REGION },
});

new CdkNoteDistributionStack(app, 'CdkNoteDistributionStack', {
  env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: process.env.CDK_DEFAULT_REGION },
});

new CdkNoteApiPublicStack(app, 'CdkNoteApiPublicStack', {
  env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: process.env.CDK_DEFAULT_REGION },
});

new CdkNotePermitStack(app, 'CdkNotePermitStack', {
  env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: process.env.CDK_DEFAULT_REGION },
});

new CdkNoteUiDeployStack(app, 'CdkNoteUiDeployStack', {
  env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: process.env.CDK_DEFAULT_REGION },
});