# myb-balance-reporter
 A serverless AWS-hosted solution for fetching crypto account balances and reporting it to New Relic

This project contains source code and supporting files for a serverless application that you can deploy with the [AWS SAM CLI](#aws-sam-cli). 

The [`template.yaml`](template.yaml) is a template that defines the application's AWS resources and configurations for those resources. Pay special attention to this file for configuring the project.

## Prerequisites

### AWS SAM CLI 

The Serverless Application Model Command Line Interface (SAM CLI) is an extension of the AWS CLI that adds functionality for building and testing Lambda applications. It uses Docker to run the functions in an Amazon Linux environment that matches Lambda.

To use the SAM CLI, you need the following tools.

* SAM CLI - [Install the SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
* [Python 3 installed](https://www.python.org/downloads/)
* Docker - [Install Docker community edition](https://hub.docker.com/search/?type=edition&offering=community)

### Coinbase Pro

This project interacts with the Coinbase Pro API. In order to do so, you need an account with them and API key.

Instructions on how to create an API key can be found [here](https://help.coinbase.com/en/pro/other-topics/api/how-do-i-create-an-api-key-for-coinbase-pro).

For documentation on the API as well as the permission requirements for each endpoint, you can visit [here](https://docs.pro.coinbase.com/).

Note that Coinbase Pro is not the same as Coinbase. They have separate APIs and for the purposes of this project, Coinbase Pro is what you want to interface with.

### Celsius Network

Celsius Network offers a number of different "partner" integrations. The one this library leverages is the "Omnibus Integration Partner" partnership which is documented [here][omnibus-integration-partner].

Instructions on how to acquire a partner token are described in that document and it links to a guide on [generating an API key][celsius-api-key].

Postman Docs for their API can be found [here][omnibus-postman-docs].

### New Relic

This project reports the BTC balance to New Relic. New Relic offers a free tier with 1-months worth of "live" data storage. Anything reported more than a month ago will be deleted so consider other options for permanent storage. To sign up for a free account and get credentials for New Relic, go [here](https://newrelic.com/).

Once you have an account, follow the instructions [here](https://docs.newrelic.com/docs/apis/get-started/intro-apis/new-relic-api-keys#insights-insert-key) to create an Insights Insert key. The guide should eventually take you to a site starting with `https://insights.newrelic.com/` which will have your account ID in the URL like so: `https://insights.newrelic.com/accounts/<account_id>/manage/api_keys`. You will need that in addition to the insert API key.

## Running Locally

### Use the SAM CLI to build and test locally

Build the application with the `sam build --use-container` command.

```sh
sam build --use-container
```

For rebuilding small changes, it should be a lot faster to use the following command:

```sh
sam build --use-container --parallel --skip-pull-image
```

The SAM CLI installs dependencies defined in `requirements.txt` files for each function, creates a deployment package, and saves it in the `.aws-sam/build` folder.

Before invoking a function, make sure you have any necessary secrets in an `env.json` file as that will be necessary to [override any environment variables](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-using-invoke.html#serverless-sam-cli-using-invoke-environment-file) referencing AWS Systems Manager strings. The SAM CLI does not currently support dynamic resolution of those references running locally. An [`example_env.json`](example_env.json) is provided for you to show what it could look like for this project.

Test a single function by invoking it directly.

Run functions locally and invoke them with the `sam local invoke` command. Note the use of `--env-vars` to pull values from the file mentioned above.

```sh
sam local invoke --env-vars env.json WalletBalancesReporterFn
```

### Running Tests

Note that currently only local testing is supported.

Before running tests for the lambda functions, we need to host them locally. This can be done with the following command which starts by ensuring the code is built and then starts the lambda environment:

```sh
sam build --use-container --parallel --skip-pull-image
sam local start-lambda --env-vars env.json
```

Once that has been done, you can run the tests using:

```
pytest --verbose
```

Or a specific test using:
```
pytest --verbose tests/test_specific_function.py
```

## Remote Deployment

### Deploy the Application to AWS

Note that the functions will not run successfully until you have [set up secrets](#set-up-secrets) but _this is ok_. They will begin working once you've set those secrets up and it is important to try out this step first.

To build and deploy this project for the first time, run the following in your shell:

```sh
sam build --use-container
sam deploy --guided
```

The first `sam` command will build the source of the application. The second `sam` command will trigger a series of prompts to customize the deployment configuration:

* **Stack Name**: The name of the stack to deploy to CloudFormation. This should be unique to your account and region, and a good starting point would be something matching the project name.
* **AWS Region**: The AWS region you want to deploy the app to.
* **Confirm changes before deploy**: If set to yes, any change sets will be shown to you before execution for manual review. If set to no, the AWS SAM CLI will automatically deploy application changes.
* **Allow SAM CLI IAM role creation**: Many AWS SAM templates, including this example, create AWS IAM roles required for the AWS Lambda function(s) included to access AWS services. By default, these are scoped down to minimum required permissions. To deploy an AWS CloudFormation stack which creates or modified IAM roles, the `CAPABILITY_IAM` value for `capabilities` must be provided. If permission isn't provided through this prompt, to deploy this example you must explicitly pass `--capabilities CAPABILITY_IAM` to the `sam deploy` command.
* **Save arguments to samconfig.toml**: If set to yes, your choices will be saved to a configuration file inside the project, so that in the future you can just re-run `sam deploy` without parameters to deploy changes to the application.

### Set up Secrets

In order to give AWS access to the same secret values that you previously entered into your [`env.json`](env.json) file if you [used the SAM CLI to build and test locally](#use-the-sam-cli-to-build-and-test-locally), you will need to store those values in AWS.

This project utilizes a combination of in-[template](template.yaml) environment variable configuration settings, as well as referenced plaintext strings using [AWS Systems Manager](https://aws.amazon.com/systems-manager/)

To create secrets using the AWS CLI, follow the instructions [here](https://docs.aws.amazon.com/systems-manager/latest/userguide/param-create-cli.html). You will need to populate secrets based on the referenced names in the [`template.yaml`](template.yaml) and make sure to use the same region as specified in the [`samconfig.toml`](samconfig.toml) that you should have generated when you [deployed the application to AWS](#deploy-the-application-to-AWS).

The general syntax of the command to add a secret is:

```sh
aws ssm put-parameter \
    --name "/example/hierarchy/secret" \
    --type "String" \
    --value "ami-12345abcdeEXAMPLE"
```

You can also list all parameters stored directly in a path with:

```sh
aws ssm get-parameters-by-path --path /example/hierarchy
```

These secret paths should match the paths found in the [`template.yaml`](template.yaml) file as values for certain environment variables. An example is 

```yaml
NEWRELIC_INSIGHTS_INSERT_API_KEY: '{{resolve:ssm:/newrelic/insights/insert_api_key:1}}'
```

In this case, you would want to run the following command to store the secret with `ssm`:

```sh
aws ssm put-parameter \
    --name "/newrelic/insights/insert_api_key" \
    --type "String" \
    --value "NR-ABCDF123456"
```

### Fetch, tail, and filter Lambda function logs

To simplify troubleshooting, SAM CLI has a command called `sam logs`. `sam logs` lets you fetch logs generated by the deployed Lambda function from the command line. In addition to printing the logs on the terminal, this command has several nifty features to help you quickly find the bug.

`NOTE`: This command works for all AWS Lambda functions; not just the ones you deploy using SAM.

```sh
sam logs -n ExampleFunction --stack-name myb-balance-reporter --tail
```

You can find more information and examples about filtering Lambda function logs in the [SAM CLI Documentation](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-logging.html).

### Cleanup

To delete this application after it has been deployed successfully, use the AWS CLI. Assuming you used the project name for the stack name, you can run the following:

```sh
aws cloudformation delete-stack --stack-name myb-balance-reporter
```

## Monitoring and Observability

Time to actually look at the data you're collecting!

### New Relic Events
The following events are reported by this project to New Relic

* WalletBalanceSnapshot - A snapshot of the current wallet balance and its USD equivalent among other details

### New Relic Dashboarding

Once you've successfully reported data to New Relic, you may want to create a [dashboard](http://one.newrelic.com/launcher/dashboards.launcher) in order to view it. The site should guide you through how to do this.

An example query leveraging the reported [events](#events) would be as follows:

```
FROM WalletBalanceSnapshot SELECT max(usd_equivalent) TIMESERIES 30 minutes SINCE 3 day ago COMPARE WITH 7 days ago
```


[celsius-api-key]: https://developers.celsius.network/createAPIKey.html
[omnibus-integration-partner]: https://developers.celsius.network/integration-partner.html
[omnibus-postman-docs]: https://documenter.getpostman.com/view/4207695/Rzn6v2mZ#83677182-2cc9-4198-b574-77ad0862237b
