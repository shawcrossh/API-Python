from typing import Generator

import pytest
from playwright.sync_api import Playwright, APIRequestContext

from google.cloud import bigquery
from google.oauth2 import service_account

import time
import allure
import json

@pytest.fixture(scope="session")
def api_request_context(
    playwright: Playwright,
) -> Generator[APIRequestContext, None, None]:
    request_context = playwright.request.new_context()
    yield request_context
    request_context.dispose()

def test_first_name_missing(api_request_context: APIRequestContext) -> None:
    data = {
      "description": "",
      "camp_lejeune": "Before 1953",
      "relationship": "Other military contractor relationship",
      "injury": "Birth defects (non-cardiac)",
      "attorney": "No",
      "first_name": "",
      "last_name": "test",
      "email_address": "heather@fuzablesoftware.com",
      "phone_home": "7323287329",
      "page_version": "Lejeune Split",
      "jornaya_lead_id": "aaaaa",
      "connection_id": "aaaaa",
      "anura_response": "bad",
      "ip_address": "91.199.84.162",
      "pageurl": "https://testing.com",
      "xxTrustedFormToken": "https://cert...",
      "xxTrustedFormCertUrl": "https://cert...",
      "xxTrustedFormPingUrl": "https://ping...",
      "lp_test": "true", 
      "s1": "[s1]",
      "s2": "[s2]",
      "s3": "[s3]",
      "s4": "[s4]",
      "s5": "[s5]",
      "cr": "[cr]",
      "cid": "[cid]",
      "asid": "[asid]]",
      "aid": "[aid]]",
      "efid": "[efid]",
      "referrer": "",
      "utm_medium": "[utm_medium]",
      "utm_campaign": "[utm_campaign]",
      "utm_content": "[utm_content]",
      "utm_source": "[utm_source]",
      "affid": "[affid]",
      "mediabuy": "[mediabuy]",
      "requestid": "[requestid]",
    }

    # Post request to create a new lead
    new_lead = api_request_context.post("https://internal-api-gateway", data=data)

    # Test response status
    assert new_lead.ok

    # Test response content
    response = new_lead.json()
    allure.attach(json.dumps(response, indent=4), name="API Response", attachment_type=allure.attachment_type.JSON)
    assert response.get('result') == 'failed'

    # verify BigQuery message databases

    # Read response and get lead_id
    lead_id = response['lead_id']

    # Initialize BigQuery client with credentials
    credentials = service_account.Credentials.from_service_account_file('xxxxx')
    bigquery_client = bigquery.Client(project='testing', credentials=credentials)

    # Query request and response info
    query = f"SELECT request_email, response_response_result FROM testing.testing_views.lead_capture_testing WHERE response_response_lead_id = '{lead_id}'"

    class BigQueryResult:
        def __init__(self, request_email, response_response_result):
            self.request_email = request_email
            self.response_response_result = response_response_result

    # Initialize first_row
    first_row = None

    # Loop until first_row has a value
    while first_row is None:
        query_job = bigquery_client.query(query)
        results = query_job.result()

        # Attempt to take the first row as result
        for row in results:
            first_row = BigQueryResult(row['request_email'], row['response_response_result'])
            break

        # Add a delay between retries
        if first_row is None:
            time.sleep(1) 

    # Test results
    assert first_row.request_email == "heather@fuzablesoftware.com"
    assert first_row.response_response_result == "failed"
