import * as cdk from '@aws-cdk/core';
import * as appsync from "@aws-cdk/aws-appsync";
import * as iam from "@aws-cdk/aws-iam";

export class CdkNoteApiPublicStack extends cdk.Stack {
  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    
    const es_index = this.node.tryGetContext('elasticsearch_index')
    const es_endpoint = this.node.tryGetContext('elasticsearch_endpoint')
    const es_domain_arn = this.node.tryGetContext('elasticsearch_domainarn')
    
    const schema = new appsync.Schema({
      filePath: "graphql/public.schema.graphql",
    })
    
    const api = new appsync.GraphqlApi(this, "API", {
      logConfig: {
        fieldLogLevel: appsync.FieldLogLevel.ALL,
      },
      authorizationConfig: {
        defaultAuthorization: {
          authorizationType: appsync.AuthorizationType.IAM,
        },
      },
      schema: schema,
      name: id + "-api"
    })
    
    // ES

    // Role for appsync that query Elasticsearch

    const appsync_es_role = new iam.Role(this, "Role", {
      assumedBy: new iam.ServicePrincipal("appsync.amazonaws.com"),
      //roleName: "cdkappsync-es-role",
    })

    const appsync_es_policy_statement = new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
    })

    appsync_es_policy_statement.addActions("es:ESHttpPost");
    appsync_es_policy_statement.addActions("es:ESHttpDelete");
    appsync_es_policy_statement.addActions("es:ESHttpHead");
    appsync_es_policy_statement.addActions("es:ESHttpGet");
    appsync_es_policy_statement.addActions("es:ESHttpPut");

    appsync_es_policy_statement.addResources(
      es_domain_arn + "/*"
    )

    const appsync_es_policy = new iam.Policy(this, "Policy", {
      policyName: "cdkappsync-es-policy",
      statements: [appsync_es_policy_statement],
    })

    appsync_es_role.attachInlinePolicy(appsync_es_policy)

    // Register Elasticsearch as data source and resolvers

    const es_datasource = new appsync.CfnDataSource(this, "DataSource", {
      apiId: api.apiId,
      name: "elasticsearch",
      type: "AMAZON_ELASTICSEARCH",
      elasticsearchConfig: {
        awsRegion: "ap-northeast-1",
        endpoint: 'https://' + es_endpoint, // es_domain.domainEndpoint,
      },
      serviceRoleArn: appsync_es_role.roleArn,
    })

    const es_search_blog_resolver = new appsync.CfnResolver(this, "Resolver", {
      apiId: api.apiId,
      typeName: "Query",
      fieldName: "searchArticles",
      dataSourceName: es_datasource.name,
      requestMappingTemplate: `{
        "version":"2017-02-28",
        "operation":"GET",
        "path":"/${es_index}/_search",
        "params": {
          "body": {
            "query": {
              "multi_match" : {
                "query": "$\{context.args.input.word\}",
                "fuzziness": $\{context.args.input.fuzziness\},
                "operator": "and",
                "fields": [ "title^10", "category^10", "tags^10", "content" ] 
              }
            },
            "sort": {
              "lank": {
                "order": "desc"
              }
            },
            "highlight": {
              "fields": {
                "title": {},
                "tags": {},
                "category": {},
                "content": {}
              }
            }
          }
        }
      }`,
      responseMappingTemplate: `
        #set($items = [])
        #foreach($entry in $context.result.hits.hits)
          #set($item = $entry.get("_source"))
          $util.qr($item.put("id", $entry.get("_id")))
          $util.qr($item.put("highlight", $entry.get("highlight")))
          $util.qr($items.add($item))
        #end
        $util.toJson($items)
      `,
    })
    
    // これが無いとNotFoundのエラーが出る
    es_search_blog_resolver.addDependsOn(es_datasource)
    
    // Output
    
    new cdk.CfnOutput(this, 'AppsyncapiId', { 
      exportName: this.node.tryGetContext('appsync_public_apiid_exportname'), 
      value: api.apiId,
    })
    
    new cdk.CfnOutput(this, 'AppsyncapiUrl', { 
      exportName: this.node.tryGetContext('appsync_public_apiurl_exportname'), 
      value: api.graphqlUrl,
    })
  }
}
