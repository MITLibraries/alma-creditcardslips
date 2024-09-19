import logging

from freezegun import freeze_time

from ccslips.cli import main


@freeze_time("2023-01-04")
def test_cli_options_from_env(caplog, runner):
    result = runner.invoke(main)
    assert result.exit_code == 0
    assert "Logger 'root' configured with level=INFO" in caplog.text
    assert "Starting credit card slips process" in caplog.text
    assert (
        "Credit card slips processing complete for date 2023-01-02. Email sent to "
        "recipient(s) ('recipient1@example.com', 'recipient2@example.com')" in caplog.text
    )


def test_cli_all_options_passed(caplog, runner):
    caplog.set_level(logging.DEBUG)
    result = runner.invoke(
        main,
        [
            "--source-email",
            "from@example.com",
            "--recipient-email",
            "recipient1@example.com",
            "--recipient-email",
            "recipient2@example.com",
            "--date",
            "2023-01-02",
            "--verbose",
        ],
    )
    assert result.exit_code == 0
    assert "Logger 'root' configured with level=DEBUG" in caplog.text
    assert (
        "Command called with options: {'source_email': 'from@example.com', "
        "'recipient_email': ('recipient1@example.com', 'recipient2@example.com'), "
        "'date': '2023-01-02', 'verbose': True}" in caplog.text
    )
    assert (
        "Credit card slips processing complete for date 2023-01-02. Email sent to "
        "recipient(s) ('recipient1@example.com', 'recipient2@example.com')" in caplog.text
    )
