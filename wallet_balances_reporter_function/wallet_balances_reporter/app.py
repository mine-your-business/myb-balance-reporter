import os
import asyncio


from .configuration import Configuration
from .balance_reporter import BalanceReporter


def lambda_handler(event, context):
    """Lambda function reacting to EventBridge events

    Parameters
    ----------
    event: dict, required
        Event Bridge Scheduled Events Format

        Event doc: https://docs.aws.amazon.com/eventbridge/latest/userguide/event-types.html#schedule-event-type

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    """

    dry_run = os.environ.get('RUN_MODE') == 'test'
    print(f'Running in {"dry run" if dry_run else "production"} mode')

    config = Configuration()
    event_loop = asyncio.get_event_loop()
    balance_reporter = BalanceReporter(
        config,
        event_loop,
        dry_run
    )
    event_loop.run_until_complete(balance_reporter.process_reports_async())
    event_loop.close()
    # We got here successfully!
    return True
