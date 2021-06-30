#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from '@aws-cdk/core';
import { CdkNoteStack } from '../lib/cdk-note-stack';
import { CdkNoteStrageStack } from '../lib/cdk-note-storage-stack';
import { CdkNoteFunctionStack } from '../lib/cdk-note-function-stack';

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