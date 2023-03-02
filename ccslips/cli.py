import logging
import os
from datetime import datetime, timedelta
from time import perf_counter
from typing import Optional

import click

from ccslips.config import configure_logger, configure_sentry
from ccslips.email import Email
from ccslips.polines import generate_credit_card_slips_html, process_po_lines

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "-s",
    "--source-email",
    envvar="SES_SEND_FROM_EMAIL",
    required=True,
    help="The email address sending the credit card slips.",
)
@click.option(
    "-r",
    "--recipient-email",
    envvar="SES_RECIPIENT_EMAIL",
    required=True,
    multiple=True,
    help="The email address(es) receiving the credit card slips. Repeatable, e.g. "
    "`-r recipient1@example.com -r recipient2@example.com`. If setting via ENV "
    "variable, separate multiple email addresses with a space, e.g. "
    "`SES_RECIPIENT_EMAIL=recipient1@example.com recipient2@example.com`",
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
    date = date or (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    credit_card_slips_data = process_po_lines(date)
    email_content = generate_credit_card_slips_html(credit_card_slips_data)
    email = Email()
    env = os.environ["WORKSPACE"]
    subject_prefix = f"{env.upper()} " if env != "prod" else ""
    email.populate(
        from_address=source_email,
        to_addresses=",".join(recipient_email),
        subject=f"{subject_prefix}Credit card slips {date}",
        attachments=[
            {
                "content": email_content,
                "filename": f"{date}_credit_card_slips.htm",
            }
        ],
    )
    response = email.send()
    logger.debug(response)

    elapsed_time = perf_counter() - start_time
    logger.info(
        "Credit card slips processing complete for date %s. Email sent to recipient(s) "
        "%s with SES message ID '%s'. Total time to complete process: %s",
        date,
        recipient_email,
        response["MessageId"],
        str(timedelta(seconds=elapsed_time)),
    )
