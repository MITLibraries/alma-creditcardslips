import datetime
import logging
from time import perf_counter

import click

from ccslips.config import Config, configure_logger, configure_sentry
from ccslips.email import Email
from ccslips.polines import generate_credit_card_slips_html, process_po_lines

logger = logging.getLogger(__name__)

CONFIG = Config()


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
        "two (2) days before the date the application is run."
    ),
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Pass to set log level to DEBUG. Defaults to INFO.",
)
@click.pass_context
def main(
    ctx: click.Context,
    source_email: str,
    recipient_email: list[str],
    date: str | None,
    *,
    verbose: bool,
) -> None:
    start_time = perf_counter()
    root_logger = logging.getLogger()
    logger.info(configure_logger(root_logger, verbose=verbose))
    logger.info(configure_sentry())
    CONFIG.check_required_env_vars()

    logger.debug("Command called with options: %s", ctx.params)
    logger.info("Starting credit card slips process")

    # creation date of retrieved PO lines
    created_date = date or (
        datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(days=2)
    ).strftime("%Y-%m-%d")

    credit_card_slips_data = process_po_lines(created_date)

    email_content = generate_credit_card_slips_html(credit_card_slips_data)
    email = Email()
    subject_prefix = f"{CONFIG.WORKSPACE.upper()} " if CONFIG.WORKSPACE != "prod" else ""
    email.populate(
        from_address=source_email,
        to_addresses=",".join(recipient_email),
        subject=f"{subject_prefix}Credit card slips {created_date}",
        attachments=[
            {
                "content": email_content,
                "filename": f"{created_date}_credit_card_slips.htm",
            }
        ],
    )
    response = email.send()
    logger.debug(response)

    elapsed_time = perf_counter() - start_time
    logger.info(
        f"Credit card slips processing complete for date {created_date}. "
        f"Email sent to recipient(s) {recipient_email} "
        f"with SES message ID {response["MessageId"]}. "
        f"Total time to complete process: {datetime.timedelta(seconds=elapsed_time)}"
    )
