import logging
from datetime import datetime, timedelta
from time import perf_counter
from typing import Optional

import click

from cc_slips.config import configure_logger, configure_sentry

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "-s",
    "--source-email",
    required=True,
    help="The email address sending the credit card slips.",
)
@click.option(
    "-r",
    "--recipient-email",
    required=True,
    multiple=True,
    help="The email address receiving the credit card slips. Repeatable",
)
@click.option(
    "-d",
    "--date",
    help=(
        "Optional date of exports to process, in 'YYYY-MM-DD' format. Defaults to "
        "yesterday's date if not provided."
    ),
)
@click.option(
    "-l",
    "--log-level",
    envvar="LOG_LEVEL",
    help="Case-insensitive Python log level to use, e.g. debug or warning. Defaults to "
    "INFO if not provided or found in ENV.",
)
@click.pass_context
def main(
    ctx: click.Context,
    source_email: str,
    recipient_email: list[str],
    date: Optional[str],
    log_level: Optional[str],
) -> None:
    start_time = perf_counter()
    log_level = log_level or "INFO"
    root_logger = logging.getLogger()
    logger.info(configure_logger(root_logger, log_level))
    logger.info(configure_sentry())
    logger.debug("Command called with options: %s", ctx.params)

    logger.info("Starting credit card slips process")

    # Do things here!
    date = date or (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    click.echo(
        f"\nFunctionality to be added here will process the credit card invoices from "
        f"date {date} and send the resulting email from {source_email} to "
        f"{recipient_email}\n"
    )

    elapsed_time = perf_counter() - start_time
    logger.info(
        "Finished! Total time to complete process: %s",
        str(timedelta(seconds=elapsed_time)),
    )
