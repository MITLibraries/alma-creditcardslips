import logging
import time
from typing import Generator, Optional
from urllib.parse import urljoin

import requests

from ccslips.config import load_alma_config

logger = logging.getLogger(__name__)


class AlmaClient:
    """AlmaClient class.

    An Alma API client with specific functionality necessary for credit card slips
    processing.

    Notes:
        - All requests to the Alma API include a 0.1 second wait to ensure we don't
          exceed the API rate limit.
        - If no records are found for a given endpoint with the provided parameters,
          Alma will still return a 200 success response with a json object of
          {"total_record_count": 0} and these methods will return that object.
    """

    def __init__(self) -> None:
        """Initialize AlmaClient instance."""
        alma_config = load_alma_config()
        self.base_url = alma_config["BASE_URL"]
        self.headers = {
            "Authorization": f"apikey {alma_config['API_KEY']}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        self.timeout = float(alma_config["TIMEOUT"])

    def get_paged(
        self,
        endpoint: str,
        record_type: str,
        params: Optional[dict] = None,
        limit: int = 100,
        _offset: int = 0,
        _records_retrieved: int = 0,
    ) -> Generator[dict, None, None]:
        """Retrieve paginated results from the Alma API for a given endpoint.

        Args:
            endpoint: The paged Alma API endpoint to call, e.g. "acq/invoices".
            record_type: The type of record returned by the Alma API for the specified
                endpoint, e.g. "invoice" record_type returned by the "acq/invoices"
                endpoint. See <https://developers.exlibrisgroup.com/alma/apis/docs/xsd/
                rest_invoice.xsd/?tags=POST#invoice> for example.
            params: Any endpoint-specific params to supply to the GET request.
            limit: The maximum number of records to retrieve per page. Valid values are
                0-100.
            _offset: The offset value to supply to paged request. Should only be used
                internally by this method's recursion.
            _records_retrieved: The number of records retrieved so far for a given
                paged endpoint. Should only be used internally by this method's
                recursion.
        """
        params = params or {}
        params["limit"] = str(limit)
        params["offset"] = str(_offset)
        response = requests.get(
            url=urljoin(self.base_url, endpoint),
            params=params,
            headers=self.headers,
            timeout=self.timeout,
        )
        response.raise_for_status()
        time.sleep(0.1)
        total_record_count = int(response.json()["total_record_count"])
        records = response.json().get(record_type, [])
        records_retrieved = _records_retrieved + len(records)
        for record in records:
            yield record
        if records_retrieved < total_record_count:
            yield from self.get_paged(
                endpoint,
                record_type,
                params=params,
                limit=limit,
                _offset=_offset + limit,
                _records_retrieved=records_retrieved,
            )

    def get_brief_po_lines(
        self, acquisition_method: Optional[str] = None
    ) -> Generator[dict, None, None]:
        """
        Get brief PO line records, optionally filtered by acquisition_method.

        The PO line records retrieved from this endpoint do not contain all of the PO
        line data and users may wish to retrieve the full PO line records with the
        get_full_po_lines method.
        """
        po_line_params = {
            "status": "ACTIVE",
            "acquisition_method": acquisition_method,
        }
        return self.get_paged(
            endpoint="acq/po-lines", record_type="po_line", params=po_line_params
        )

    def get_full_po_line(self, po_line_id: str) -> dict:
        """Get a single full PO line record using the PO line ID."""
        response = requests.get(
            url=str(urljoin(self.base_url, f"acq/po-lines/{po_line_id}")),
            headers=self.headers,
            timeout=self.timeout,
        )
        response.raise_for_status()
        time.sleep(0.1)
        return response.json()

    def get_full_po_lines(
        self,
        acquisition_method: Optional[str] = None,
        date: Optional[str] = None,
    ) -> Generator[dict, None, None]:
        """Get full PO line records, optionally filtered by acquisition_method/date."""
        for line in self.get_brief_po_lines(acquisition_method):
            number = line["number"]
            if date is None:
                yield self.get_full_po_line(number)
            elif line.get("created_date") == f"{date}Z":
                yield self.get_full_po_line(number)

    def get_fund_by_code(self, fund_code: str) -> dict:
        """Get fund details using the fund code.

        Note: this technically returns a list of funds as the request uses a search
        query rather than getting a single fund directly, which is not supported by the
        API. Theoretically the result could include multiple funds, however in practice
        we expect there to only be one.
        """
        response = requests.get(
            urljoin(self.base_url, "acq/funds"),
            headers=self.headers,
            params={"q": f"fund_code~{fund_code}", "view": "full"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        time.sleep(0.1)
        return response.json()
