from freezegun import freeze_time

from cc_slips.cli import main


@freeze_time("2023-01-02")
def test_cli_only_required_options(caplog, runner):
    result = runner.invoke(
        main, ["-s", "source@example.com", "-r", "recipient@example.com"]
    )
    assert result.exit_code == 0
    assert "Logger 'root' configured with level=INFO" in caplog.text
    assert "Starting credit card slips process" in caplog.text
    assert "Total time to complete process" in caplog.text


def test_cli_all_options(caplog, runner):
    result = runner.invoke(
        main,
        [
            "--source-email",
            "source@example.com",
            "--recipient-email",
            "recipient1@example.com",
            "--recipient-email",
            "recipient2@example.com",
            "--date",
            "2023-01-02",
            "--log-level",
            "debug",
        ],
    )
    assert result.exit_code == 0
    assert "Logger 'root' configured with level=DEBUG" in caplog.text
    assert (
        "Command called with options: {'source_email': 'source@example.com', "
        "'recipient_email': ('recipient1@example.com', 'recipient2@example.com'), "
        "'date': '2023-01-02', 'log_level': 'debug'}" in caplog.text
    )
    assert "Total time to complete process" in caplog.text
