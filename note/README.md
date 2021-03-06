+++
title = "Note"
category = "CDK"
tags = ["CDK", "Lambda", "S3", "SNS", "Route 53", "ALB", "AppSync", "Elasticsearch", "Amplify"]
date = "2021-07-04"
update = "2021-07-04"
+++

今まで記事をmarkdownで書いて、Hugoを使ってサイトにしていたのですが、いくつか理由があって自作のサイトにすることにしました。
そのサイトを構成するシステムが[このリポジトリ](https://github.com/suzukiken/cdk-note)の内容です。

### 自作にしたわけ

1. 記事のソースをGithubに変更するため

今までの仕組みでは記事を書かなくなってきた。でも相変わらずGithubのリポジトリはよく作る。
そもそも今までの記事の内容は大抵はGithubのリポジトリの内容を説明したものだ。
だから今後はGithubのREADME.mdにそのリポのことを書いていくことにして、サイトではそれをコンテンツとして集約したシステムにしたいと考えた。

2. 既存のテーマだといまいち

HugoでもJekyllでも、ともかくどのテーマも美しいと思うけれども、たいてどこかは、ちょっとやりたいことと違うなあと思う部分がある。
もちろん自分で一から作っても当然そういうところはあるけれど、
既存のテーマをカスタマイズするためにHugoの仕組みを理解してHTMLやCSSで云々するより、
比較的興味もあるしReactとMaterial-UIで一から作る方が自由にできるし面白みもある。

3. Elasticsearchを使いたい

これも興味があるということが大きいが、記事の検索機能をつけたい。それからGithubに保管したコードの検索もしたい。
そもそも自分は自分で書いたコードを検索して利用することが非常に多い。
だから頻繁にGithubで自分のコードを検索しているのだけど、Githubのコード検索がいまいち使いにくいと思っていて、自分なりに検索できる仕組みをElasticsearchで作ろうと思った。

### と言っても

と言っても徐々に作っていくという段階なので、今はまだ開発中です。

### リポジトリの構成はこのようになっている

* [S3バケットとオブジェクト作成などのイベント処理](../lib/cdk-note-storage-stack.ts)
* [CloudFrontを経由したS3バケットの配信](../lib/cdk-note-distribution-stack.ts)
* [定期実行やGithubのpush時のイベントで動くLambda関数](../lib/cdk-note-function-stack.ts)
* [CloudFrontで配信するS3とDNSの設定](../lib/cdk-note-distribution-stack.ts)
* [AppSyncのGraphQLAPIの設定](../lib/cdk-note-api-public-stack.ts)
* [別リポジトリに置いたAmplify+Reactで構成するウェブUIのデプロイ設定](../lib/cdk-note-ui-deploy-public-stack.ts)

### メモ

#### Githubの通知方法

GithubではPushなどの変更があった場合の通知方法として、webhookがあり、それの設定をするのが最も簡単だと思うので、それを利用した。
webhookの登録（通知先）はApi Gatewayで作った1つのURLにしておいて、その先で一旦Lambdaを経由してSNSに通知して、それを複数のLambda関数がサブスクライブするようにしている。

でもこれは実は無駄かもしれない。Api Gatewayから直接SNSにメッセージを投げ込むこともできるかもしれない。

それからwebhookは設定が楽なのでそれを使っているけれど、Github ActionsでEventBridgeに通知するという手間のかかる方法もあるようです。ただAWSのクレデンシャルの登録など、結構手間がかかりそうなのでやめておきました。

#### CloudFront経由でアクセスする際のCORSの設定

やらなくてもいいことなのだけれど、S3のデータにアクセスする時に、S3に設定したCORSのヘッダなどをCloudFront経由でも提供されるようにするために、[AWSの記事](https://aws.amazon.com/premiumsupport/knowledge-center/no-access-control-allow-origin-error/)を参考にして、CloudFrontの[cache behaviorを設定した](https://github.com/suzukiken/cdk-note/blob/5119baa2e7b6886fa750b6f70b88a562c25be104/lib/cdk-note-distribution-stack.ts#L20-L24)。

#### SPAをCloudFrontで配信する

今回のUIはReactとReact Routerを使っているため、ルートオブジェクトとエラー時のオブジェクトを[index.htmlに設定している](https://github.com/suzukiken/cdk-note/blob/a9bef05ca8208329ec0543667b527818a6dbb200/lib/cdk-note-distribution-stack.ts#L34-L42)。ただ[こちらのリポジトリ](https://github.com/suzukiken/utilui)で作ったサイトの方では、同じようにReactとReact RouterとCloudFrontを使っているけれど、特にそういう設定をしていないのに、問題なくウェブが閲覧できているので、そこが不思議なところ。そのために何かをしたのかもしれないんだけど忘れてしまっている。