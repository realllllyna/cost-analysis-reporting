from urllib.parse import quote

import requests
from requests.auth import HTTPBasicAuth

from config import Config


class NavClient:
    def __init__(self):
        self.base_url = Config.NAV_BASE_URL.rstrip("/")
        self.auth = HTTPBasicAuth(Config.NAV_USERNAME, Config.NAV_PASSWORD)

    def build_company_endpoint(self, company_name: str, service_name: str) -> str:
        encoded_company = quote(company_name, safe="")
        return f"{self.base_url}/Company('{encoded_company}')/{service_name}"

    def get_json(self, url: str, params: dict | None = None) -> dict:
        headers = {
            "Accept": "application/json",
            "Prefer": f"odata.maxpagesize={Config.NAV_PAGE_SIZE}",
        }

        response = requests.get(
            url,
            auth=self.auth,
            params=params,
            headers=headers,
            timeout=Config.NAV_TIMEOUT_SECONDS,
        )

        response.raise_for_status()
        return response.json()

    def get_odata_values(
        self,
        company_name: str,
        service_name: str,
        params: dict | None = None,
    ) -> list[dict]:
        url = self.build_company_endpoint(company_name, service_name)

        all_rows = []
        current_params = params.copy() if params else None

        while url:
            data = self.get_json(url, params=current_params)

            rows = data.get("value", [])
            all_rows.extend(rows)

            print(
                f"Loaded {len(rows)} rows from {service_name}. "
                f"Total so far: {len(all_rows)}"
            )

            next_link = data.get("@odata.nextLink")

            if next_link:
                url = next_link
                current_params = None
            else:
                url = None

        return all_rows