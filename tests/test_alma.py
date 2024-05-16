from ccslips.alma import AlmaClient


def test_client_initializes_with_expected_values():
    client = AlmaClient()
    assert client.base_url == "https://example.com"
    assert client.headers == {
        "Authorization": "apikey just-for-testing",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    assert client.timeout == 10  # noqa: PLR2004


def test_get_paged(alma_client):
    records = alma_client.get_paged(
        endpoint="paged",
        record_type="fake_records",
        limit=10,
    )
    assert len(list(records)) == 15  # noqa: PLR2004


def test_get_brief_po_lines_without_acquisition_method(alma_client):
    result = list(alma_client.get_brief_po_lines())
    assert len(result) == 1
    assert result[0]["number"] == "POL-other-acq-method"


def test_get_brief_po_lines_with_acquisition_method(alma_client):
    result = list(alma_client.get_brief_po_lines("PURCHASE_NOLETTER"))
    assert len(result) == 3  # noqa: PLR2004
    assert result[0]["number"] == "POL-all-fields"
    assert result[1]["number"] == "POL-missing-fields"
    assert result[2]["number"] == "POL-wrong-date"


def test_get_full_po_line(alma_client):
    assert alma_client.get_full_po_line("POL-all-fields") == {
        "acquisition_method": {"desc": "Credit Card"},
        "created_date": "2023-01-02Z",
        "fund_distribution": [
            {"fund_code": {"value": "FUND-abc"}, "amount": {"sum": "7"}},
            {"fund_code": {"value": "FUND-def"}, "amount": {"sum": "5.0"}},
        ],
        "location": [{"quantity": 1}, {"quantity": 2}],
        "note": [{"note_text": "CC-cardholder name"}],
        "number": "POL-all-fields",
        "price": {"sum": "12.0"},
        "resource_metadata": {"title": "Book title"},
        "vendor_account": "CORP",
        "vendor": {"value": "CORP", "desc": "Corporation"},
    }


def test_get_full_po_lines_with_defaults(alma_client):
    result = list(alma_client.get_full_po_lines())
    assert len(result) == 1
    assert result[0]["number"] == "POL-other-acq-method"


def test_get_full_po_lines_with_parameters(alma_client):
    result = list(
        alma_client.get_full_po_lines(
            acquisition_method="PURCHASE_NOLETTER", date="2023-01-02"
        )
    )
    assert len(result) == 2  # noqa: PLR2004
    assert result[0]["number"] == "POL-all-fields"
    assert result[1]["number"] == "POL-missing-fields"


def test_alma_get_fund_by_code(alma_client):
    fund = alma_client.get_fund_by_code("FUND-abc")
    assert fund["fund"][0]["code"] == "FUND-abc"
