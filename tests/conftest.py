import json

import boto3
import pytest
import requests_mock
from click.testing import CliRunner
from moto import mock_aws

from ccslips.alma import AlmaClient


# Env fixtures
@pytest.fixture(autouse=True)
def _test_environment(monkeypatch):
    monkeypatch.setenv("ALMA_API_URL", "https://example.com")
    monkeypatch.setenv("ALMA_API_READ_KEY", "just-for-testing")
    monkeypatch.setenv("ALMA_API_TIMEOUT", "10")
    monkeypatch.setenv("SES_SEND_FROM_EMAIL", "from@example.com")
    monkeypatch.setenv(
        "SES_RECIPIENT_EMAIL", "recipient1@example.com recipient2@example.com"
    )
    monkeypatch.setenv("SENTRY_DSN", "None")
    monkeypatch.setenv("WORKSPACE", "test")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")


# CLI fixture
@pytest.fixture
def runner():
    return CliRunner()


# Record fixtures
@pytest.fixture(name="fund_records", scope="session")
def fund_records_fixture():
    with open("tests/fixtures/fund_records.json", encoding="utf-8") as funds_file:
        return json.load(funds_file)


@pytest.fixture(name="po_line_records", scope="session")
def po_line_records_fixture():
    with open("tests/fixtures/po_line_records.json", encoding="utf-8") as po_lines_file:
        return json.load(po_lines_file)


# API fixtures
@pytest.fixture
def alma_client():
    return AlmaClient()


@pytest.fixture(autouse=True)
def mocked_alma(fund_records, po_line_records):
    with requests_mock.Mocker() as mocker:
        # Generic paged endpoints
        mocker.get(
            "https://example.com/paged?limit=10&offset=0",
            complete_qs=True,
            json={
                "fake_records": [{"record_number": i} for i in range(10)],
                "total_record_count": 15,
            },
        )
        mocker.get(
            "https://example.com/paged?limit=10&offset=10",
            complete_qs=True,
            json={
                "fake_records": [{"record_number": i} for i in range(10, 15)],
                "total_record_count": 15,
            },
        )

        # Fund endpoints
        mocker.get(
            "https://example.com/acq/funds?q=fund_code~FUND-abc",
            json={"fund": [fund_records["abc"]], "total_record_count": 1},
        )
        mocker.get(
            "https://example.com/acq/funds?q=fund_code~FUND-def",
            json={"fund": [fund_records["def"]], "total_record_count": 1},
        )
        mocker.get(
            "https://example.com/acq/funds?q=fund_code~FUND-no-external-id",
            json={"fund": [fund_records["no-external-id"]], "total_record_count": 1},
        )
        mocker.get(
            "https://example.com/acq/funds?q=fund_code~FUND-nothing-here",
            json={"total_record_count": 0},
        )

        # PO Line endpoints
        mocker.get(
            "https://example.com/acq/po-lines?status=ACTIVE",
            json={
                "po_line": [po_line_records["other_acq_method"]],
                "total_record_count": 1,
            },
        )
        mocker.get(
            (
                "https://example.com/acq/po-lines?status=ACTIVE&"
                "acquisition_method=PURCHASE_NOLETTER"
            ),
            json={
                "po_line": [
                    po_line_records["all_fields"],
                    po_line_records["missing_fields"],
                    po_line_records["wrong_date"],
                ],
                "total_record_count": 3,
            },
        )
        mocker.get(
            "https://example.com/acq/po-lines/POL-all-fields",
            json=po_line_records["all_fields"],
        )
        mocker.get(
            "https://example.com/acq/po-lines/POL-missing-fields",
            json=po_line_records["missing_fields"],
        )
        mocker.get(
            "https://example.com/acq/po-lines/POL-other-acq-method",
            json=po_line_records["other_acq_method"],
        )
        mocker.get(
            "https://example.com/acq/po-lines/POL-wrong-date",
            json=po_line_records["wrong_date"],
        )

        yield mocker


# AWS fixtures
@pytest.fixture(autouse=True)
def mocked_ses():
    with mock_aws():
        ses = boto3.client("ses", region_name="us-east-1")
        ses.verify_email_identity(EmailAddress="from@example.com")
        yield ses
