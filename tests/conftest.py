import json
import os

import pytest
import requests_mock
from click.testing import CliRunner

from ccslips.alma import AlmaClient


# Env fixture
@pytest.fixture(autouse=True)
def test_env():
    os.environ = {
        "ALMA_API_URL": "https://example.com",
        "ALMA_API_READ_KEY": "just-for-testing",
        "ALMA_API_TIMEOUT": "10",
        "SENTRY_DSN": "None",
        "WORKSPACE": "test",
    }
    yield


# CLI fixture
@pytest.fixture()
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
@pytest.fixture()
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
                    po_line_records["wrong_date"],
                ],
                "total_record_count": 2,
            },
        )
        mocker.get(
            "https://example.com/acq/po-lines/POL-all-fields",
            json=po_line_records["all_fields"],
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
