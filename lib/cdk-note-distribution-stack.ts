import * as cdk from '@aws-cdk/core';
import * as s3 from '@aws-cdk/aws-s3';
import * as acm from "@aws-cdk/aws-certificatemanager";
import * as cloudfront from '@aws-cdk/aws-cloudfront';
import * as origins from '@aws-cdk/aws-cloudfront-origins';
import * as route53 from '@aws-cdk/aws-route53';
import * as targets from "@aws-cdk/aws-route53-targets/lib";

export class CdkNoteDistributionStack extends cdk.Stack {
  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    
    const domain = this.node.tryGetContext('domain')
    const subdomain = this.node.tryGetContext('subdomain')
    const acmarn = cdk.Fn.importValue(this.node.tryGetContext('useast1_acmarn_exportname'))
    const bucketname = cdk.Fn.importValue(this.node.tryGetContext('s3bucketname_exportname'))
    const bucket = s3.Bucket.fromBucketName(this, 'Bucket', bucketname)
    const certificate = acm.Certificate.fromCertificateArn(this, 'Certificate', acmarn)
    
    const cache_policy = new cloudfront.CachePolicy(this, 'CachePolicy', {
      headerBehavior: cloudfront.CacheHeaderBehavior.allowList(
        'Access-Control-Request-Headers', 'Access-Control-Request-Method', 'Origin'
      ),
    })
    
    const distribution = new cloudfront.Distribution(this, 'Distribution', {
      defaultBehavior: { 
        origin: new origins.S3Origin(bucket),
        allowedMethods: cloudfront.AllowedMethods.ALLOW_ALL,
        cachePolicy: cache_policy
      },
      domainNames: [cdk.Fn.join(".", [subdomain, domain])],
      certificate: certificate,
    })
    
    const zone = route53.HostedZone.fromLookup(this, "HostedZone", {
      domainName: domain,
    })
    
    const record = new route53.ARecord(this, "ARecord", {
      recordName: subdomain,
      target: route53.RecordTarget.fromAlias(
        new targets.CloudFrontTarget(distribution)
      ),
      zone: zone,
    })
    
    new cdk.CfnOutput(this, 'DistributionId', { 
      exportName: this.node.tryGetContext('distributionid_exportname'), 
      value: distribution.distributionId
    })
    
    new cdk.CfnOutput(this, 'DistributionDomainname', { 
      exportName: this.node.tryGetContext('distribution_domainname_exportname'), 
      value: distribution.domainName
    })
    
  }
}
