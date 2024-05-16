from collections.abc import Generator, Iterator
from copy import deepcopy
from datetime import datetime
from decimal import Decimal
from xml.etree import ElementTree

from ccslips.alma import AlmaClient


def process_po_lines(date: str) -> Generator[dict, None, None]:
    """Retrieve PO line records for a given date and yield processed data for each."""
    client = AlmaClient()
    for po_line in client.get_full_po_lines("PURCHASE_NOLETTER", date):
        yield extract_credit_card_slip_data(client, po_line)


def extract_credit_card_slip_data(client: AlmaClient, po_line_record: dict) -> dict:
    """Extract required data for a credit card slip from a PO line record.

    The keys of the returned dict map to the appropriate element classes in the XML
    template used to generate a formatted slip.
    """
    created_date = (
        datetime.strptime(po_line_record["created_date"], "%Y-%m-%dZ")
        .astimezone()
        .strftime("%y%m%d")
    )
    fund_distribution = po_line_record.get("fund_distribution", [])
    price = Decimal(po_line_record.get("price", {}).get("sum", "0.00"))
    title = po_line_record.get("resource_metadata", {}).get("title", "Unknown title")

    po_line_data = {
        "cardholder": get_cardholder_from_notes(po_line_record.get("note")),
        "invoice_number": (
            f"Invoice #: {created_date}{title.replace(' ', '')[:3].upper()}"
        ),
        "po_date": created_date,
        "po_line_number": po_line_record["number"],
        "price": f"${price:.2f}",
        "quantity": get_quantity_from_locations(po_line_record.get("location")),
        "item_title": title,
        "total_price": (
            f"${get_total_price_from_fund_distribution(fund_distribution, price):.2f}"
        ),
        "vendor_code": po_line_record.get("vendor_account", "No vendor found"),
        "vendor_name": po_line_record.get("vendor", {}).get("desc", "No vendor found"),
    }
    po_line_data.update(get_account_data(client, fund_distribution))

    return po_line_data


def get_cardholder_from_notes(notes: list[dict] | None) -> str:
    """Get first note that begins with 'CC-' from a PO line record notes field."""
    if notes:
        for note in [n for n in notes if n.get("note_text", "").startswith("CC-")]:
            return note["note_text"][3:]
    return "No cardholder note found"


def get_quantity_from_locations(locations: list[dict] | None) -> str:
    """Get the total quantity of items associated with PO line locations.

    This function adds the quantities from each location in the PO line. This is an
    imperfect method as it may generate a total quantity than differs from what is
    visible in the UI if some if the items are not associated with a location.
    Regardless, this is the best available method given that the quantity listed in the
    UI is not available in the API response. Stakeholders requested this with full
    knowledge of the imperfections.
    """
    if locations is None:
        return "0"
    return str(sum(location.get("quantity", 0) for location in locations))


def get_total_price_from_fund_distribution(
    fund_distribution: list[dict], unit_price: Decimal
) -> Decimal:
    """Get total price from fund distribution of PO line record.

    If no amounts or amount sums are listed in the fund distribution, the unit price is
    returned as the total price.
    """
    return (
        sum(
            Decimal(fund.get("amount", {}).get("sum", "0.00"))
            for fund in fund_distribution
        )
        or unit_price
    )


def get_account_data(client: AlmaClient, fund_distribution: list[dict]) -> dict[str, str]:
    """Get account information needed for a credit card slip.

    If the fund_distribution is empty, returns a single account with default text.
    Otherwise returns up to two accounts with their associated account numbers.
    """
    result = {"account_1": "No fund code found"}
    for count, fund in enumerate(fund_distribution, start=1):
        if count == 3:  # noqa: PLR2004
            break
        if account_number := get_account_number_from_fund(client, fund):
            result[f"account_{count}"] = account_number
    return result


def get_account_number_from_fund(client: AlmaClient, fund: dict) -> str | None:
    """Get account number for a given fund.

    Returns None if fund has no fund code, fund record cannot be retrieved via fund
    code, or fund record does not contain an external_id field value.
    """
    account = None
    if fund_code := fund.get("fund_code", {}).get("value"):  # noqa: SIM102
        if fund_records := client.get_fund_by_code(fund_code).get("fund"):
            account = fund_records[0].get("external_id")
    return account


def generate_credit_card_slips_html(po_line_data: Iterator[dict]) -> str:
    """Create credit card slips HTML from a set of credit card slip data."""
    template_tree = ElementTree.parse(  # noqa: S314
        "config/credit_card_slip_template.xml"
    )
    xml_template = template_tree.getroot()
    output = ElementTree.fromstring("<html></html>")  # noqa: S314
    for line in po_line_data:
        output.append(populate_credit_card_slip_xml_fields(deepcopy(xml_template), line))
    if len(output) == 0:
        return "<html><p>No credit card orders on this date</p></html>"
    return ElementTree.tostring(output, encoding="unicode", method="xml")


def populate_credit_card_slip_xml_fields(
    credit_card_slip_xml_template: ElementTree.Element, credit_card_slip_data: dict
) -> ElementTree.Element:
    """Populate credit card slip XML template with data extracted from a PO line.

    The credit_card_slip_data keys must correspond to their associated element classes
    in the XML template.
    """
    for key, value in credit_card_slip_data.items():
        for element in credit_card_slip_xml_template.findall(f'.//td[@class="{key}"]'):
            element.text = value
    return credit_card_slip_xml_template
