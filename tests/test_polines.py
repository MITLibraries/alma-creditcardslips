from decimal import Decimal

from ccslips import polines as po


def test_process_po_lines():
    result = list(po.process_po_lines("2023-01-02"))
    assert len(result) == 2  # noqa: PLR2004


def test_extract_credit_card_slip_data_all_fields_present(alma_client, po_line_records):
    assert po.extract_credit_card_slip_data(
        alma_client, po_line_records["all_fields"]
    ) == {
        "account_1": "account-abc",
        "account_2": "account-def",
        "cardholder": "cardholder name",
        "invoice_number": "Invoice #: 230102BOO",
        "po_date": "230102",
        "po_line_number": "POL-all-fields",
        "price": "$12.00",
        "quantity": "3",
        "item_title": "Book title",
        "total_price": "$12.00",
        "vendor_code": "CORP",
        "vendor_name": "Corporation",
    }


def test_extract_credit_card_slip_data_missing_fields(alma_client, po_line_records):
    assert po.extract_credit_card_slip_data(
        alma_client, po_line_records["missing_fields"]
    ) == {
        "account_1": "No fund code found",
        "cardholder": "No cardholder note found",
        "invoice_number": "Invoice #: 230102UNK",
        "po_date": "230102",
        "po_line_number": "POL-missing-fields",
        "price": "$0.00",
        "quantity": "0",
        "item_title": "Unknown title",
        "total_price": "$0.00",
        "vendor_code": "No vendor found",
        "vendor_name": "No vendor found",
    }


def test_get_cardholder_from_notes_no_notes():
    assert po.get_cardholder_from_notes(None) == "No cardholder note found"


def test_get_cardholder_from_notes_no_note_text_field():
    notes = [{"not-note_text": "CC-wrong field"}]
    assert po.get_cardholder_from_notes(notes) == "No cardholder note found"


def test_get_cardholder_from_notes_gets_correct_note():
    notes = [
        {"note_text": "not this one"},
        {"note_text": "CC or this one"},
        {"note_text": "CC-winner"},
        {"note_text": "CC- nope, first one only"},
    ]
    assert po.get_cardholder_from_notes(notes) == "winner"


def test_get_quantity_from_locations_no_locations():
    assert po.get_quantity_from_locations(None) == "0"


def test_get_quantity_from_locations_no_location_quantity_field():
    locations = [{"not-quantity": 1}]
    assert po.get_quantity_from_locations(locations) == "0"


def test_get_quantity_from_locations_sums_quantities():
    locations = [{"quantity": 0}, {"quantity": 3}, {"quantity": 7}]
    assert po.get_quantity_from_locations(locations) == "10"


def test_get_total_price_from_fund_distribution_no_funds_returns_unit_price():
    funds = []
    assert po.get_total_price_from_fund_distribution(
        funds, unit_price=Decimal("1.23")
    ) == Decimal("1.23")


def test_get_total_price_from_fund_distribution_no_amounts_or_sums_returns_unit_price():
    funds = [
        {"fund_code": {"value": "no-amount"}},
        {"fund_code": {"value": "no-amount-sum"}, "amount": {"no-sum-here": "0.00"}},
    ]
    assert po.get_total_price_from_fund_distribution(
        funds, unit_price=Decimal("1.23")
    ) == Decimal("1.23")


def test_get_total_price_from_fund_distribution_sums_fund_amounts():
    funds = [
        {"fund_code": {"value": "amount-is-zero"}, "amount": {"sum": "0.00"}},
        {"fund_code": {"value": "first-amount"}, "amount": {"sum": "5.15"}},
        {"fund_code": {"value": "second-amount"}, "amount": {"sum": "4.85"}},
    ]
    assert po.get_total_price_from_fund_distribution(
        funds, unit_price=Decimal("1.23")
    ) == Decimal("10.00")


def test_get_account_data_no_fund_distribution(alma_client):
    assert po.get_account_data(alma_client, []) == {"account_1": "No fund code found"}


def test_get_account_data_with_one_account(alma_client):
    fund_distribution = [{"fund_code": {"value": "FUND-abc"}}]
    assert po.get_account_data(alma_client, fund_distribution) == {
        "account_1": "account-abc"
    }


def test_get_account_data_with_two_accounts(alma_client):
    fund_distribution = [
        {"fund_code": {"value": "FUND-abc"}},
        {"fund_code": {"value": "FUND-def"}},
    ]
    assert po.get_account_data(alma_client, fund_distribution) == {
        "account_1": "account-abc",
        "account_2": "account-def",
    }


def test_get_account_data_with_more_than_two_accounts_only_returns_two(alma_client):
    fund_distribution = [
        {"fund_code": {"value": "FUND-abc"}},
        {"fund_code": {"value": "FUND-def"}},
        {"fund_code": {"value": "FUND-ghi"}},
    ]
    assert po.get_account_data(alma_client, fund_distribution) == {
        "account_1": "account-abc",
        "account_2": "account-def",
    }


def test_get_account_number_from_fund_no_fund_code(alma_client):
    fund = {"no-fund_code": {"value": "doesn't matter"}}
    assert po.get_account_number_from_fund(alma_client, fund) is None


def test_get_account_number_from_fund_no_fund_code_value(alma_client):
    fund = {"fund_code": {"no-value": "doesn't matter"}}
    assert po.get_account_number_from_fund(alma_client, fund) is None


def test_get_account_number_from_fund_no_fund_retrieved(alma_client):
    fund = {"fund_code": {"value": "FUND-nothing-here"}}
    assert po.get_account_number_from_fund(alma_client, fund) is None


def test_get_account_number_from_fund_no_external_id(alma_client):
    fund = {"fund_code": {"value": "FUND-no-external-id"}}
    assert po.get_account_number_from_fund(alma_client, fund) is None


def test_get_account_number_from_fund_returns_account_number(alma_client):
    fund = {"fund_code": {"value": "FUND-abc"}}
    assert po.get_account_number_from_fund(alma_client, fund) == "account-abc"


def test_generate_credit_card_slips_html_populates_with_default_text_if_no_data():
    po_line_data = []
    assert (
        po.generate_credit_card_slips_html(po_line_data)
        == "<html><p>No credit card orders on this date</p></html>"
    )


def test_generate_credit_card_slips_html_populates_all_fields():
    po_line_data = [
        {
            "account_1": "account-abc",
            "account_2": "account-def",
            "cardholder": "cardholder name",
            "invoice_number": "Invoice #: 230102BOO",
            "po_date": "230102",
            "po_line_number": "POL-all-fields",
            "price": "$12.00",
            "quantity": "3",
            "item_title": "Book title",
            "total_price": "$12.00",
            "vendor_code": "CORP",
            "vendor_name": "Corporation",
        }
    ]
    assert (
        po.generate_credit_card_slips_html(po_line_data)
        == """<html><ccslip>
  <p align="center">
    <b>MIT Libraries Credit Card Purchase</b>
    <br />
      Monograph Acquisitions, Rm. NE36-6101</p>
  <br />
  <br />
  <table border="0" width="100%" align="left">
    <tr>
      <td colspan="2">
        <u>CHARGE INFORMATION</u>
      </td>
    </tr>
    <tr>
      <td align="left">Date:</td>
      <td class="po_date" align="left">230102</td>
      <td />
    </tr>
    <tr>
      <td align="left">Cardholder:</td>
      <td class="cardholder" align="left">cardholder name</td>
      <td />
    </tr>
    <tr>
      <td align="left">Vendor name:
      </td>
      <td class="vendor_name" align="left">Corporation</td>
      <td />
    </tr>
    <tr>
      <td align="left">Vendor code:
      </td>
      <td class="vendor_code" align="left">CORP</td>
      <td />
    </tr>
    <tr>
      <td align="left">Account 1:
      </td>
      <td class="account_1" align="left">account-abc</td>
      <td />
    </tr>
    <tr>
      <td align="left">Account 2:
      </td>
      <td class="account_2" align="left">account-def</td>
      <td />
    </tr>
    <tr>
      <td>
        <br />
      </td>
    </tr>
    <tr>
      <td>PO Line #:</td>
      <td>TITLE:</td>
      <td>QUANTITY</td>
      <td>PRICE</td>
    </tr>
    <tr>
      <td class="po_line_number">POL-all-fields</td>
      <td class="item_title">Book title</td>
      <td class="quantity">3</td>
      <td class="price">$12.00</td>
    </tr>
    <tr>
      <td>
        <br />
      </td>
    </tr>
    <tr>
      <td />
      <td align="right">Transaction fee:
      </td>
      <td>__________</td>
    </tr>
    <tr>
      <td />
      <td align="right">TOTAL DUE:
      </td>
      <td class="total_price">$12.00</td>
    </tr>
    <tr>
      <td colspan="2">
        <u>SAP INFORMATION</u>
      </td>
      <td />
    </tr>
    <tr>
      <td colspan="2">SAP document #:</td>
      <td />
    </tr>
    <tr>
      <td colspan="2">Date posted in SAP:</td>
      <td />
    </tr>
    <tr>
      <td colspan="2">Verified by:</td>
      <td />
    </tr>
    <tr>
      <td colspan="2">Verified date:</td>
      <td />
    </tr>
    <tr>
      <td>
        <br />
      </td>
    </tr>
    <tr>
      <td colspan="2">
        <u>ALMA INVOICE INFORMATION</u>
      </td>
      <td />
    </tr>
    <tr>
      <td class="invoice_number" colspan="2">Invoice #: 230102BOO</td>
      <td />
    </tr>
    <tr>
      <td style="padding-left:30px;" colspan="3">Inv #: Date charged + 1st 3 letters of\
 title (YYMMDD "xxx")</td>
    </tr>
    <tr>
      <td style="padding-left:30px;" class="credit_memo_num" colspan="3">For Credit \
Memo #, use Invoice # + CRE (YYMMDD"XXX"CRE)</td>
    </tr>
    <tr>
      <td colspan="2">Use Charge Date above for Invoice Date.</td>
      <td />
    </tr>
    <tr>
      <td>
        <br />
      </td>
    </tr>
    <tr>
      <td colspan="2">Date entered in Alma:
      </td>
      <td />
    </tr>
    <tr>
      <td colspan="2">Entered by:
      </td>
      <td />
    </tr>
  </table>
  <hr class="pb" />
  <p style="page-break-before: always" />
</ccslip></html>"""
    )
