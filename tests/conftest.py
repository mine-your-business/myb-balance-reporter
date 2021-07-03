import os
import pytest

ENV_VARS = {}
with open('samconfig.toml') as file:
    for line in file:
        if line.startswith('region'):
            ENV_VARS['AWS_SAM_REGION'] = line.split('=')[1].strip().strip('\"')


@pytest.fixture(scope="session", autouse=True)
def tests_setup_and_teardown():
    # Will be executed before the first test
    original_environ = dict(os.environ)
    os.environ.update(ENV_VARS)

    yield
    # Will be executed after the last test
    os.environ.clear()
    os.environ.update(original_environ)
