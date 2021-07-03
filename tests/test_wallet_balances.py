import boto3
import botocore
import os


def test_function_returns_success():
    # Create Lambda SDK client to connect to appropriate Lambda endpoint
    lambda_client = boto3.client(
        'lambda',
        region_name=os.environ.get('AWS_SAM_REGION'),
        endpoint_url="http://127.0.0.1:3001",
        use_ssl=False,
        verify=False,
        config=botocore.client.Config(
            signature_version=botocore.UNSIGNED,
            read_timeout=20,
            retries={'max_attempts': 0},
        )
    )

    # Invoke your Lambda function as you normally usually do. The function will run
    # locally if it is configured to do so
    response = lambda_client.invoke(FunctionName="WalletBalancesReporterFn")

    # Verify the response
    assert response.get('FunctionError') is None
    assert response['ResponseMetadata']['HTTPStatusCode'] == 200
    assert response.get('StatusCode') == 200
    assert response.get('Payload') is not None
    assert bool(response['Payload'].read()) is True
