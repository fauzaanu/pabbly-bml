import requests


class BankofmaldivesAPI:
    def __init__(self, api_key, development=False):
        self.api_key = api_key
        if development:
            self.base_api_url = "https://api.merchants.bankofmaldives.com.mv"
        else:
            self.base_api_url = "https://api.merchants.bankofmaldives.com.mv"

        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": api_key
        }

    def api_path(self, path):
        return self.base_api_url + path

    def get_transaction(self,transaction_id):
        """
        Get transaction data from bml
        :param transaction_id:
        :type transaction_id:
        :return:
        :rtype:
        """
        endpoint = "/public/v2/transactions/" + transaction_id
        response = requests.get(self.api_path(endpoint), headers=self.headers)
        return response

    def create_transaction(self, payload):
        """
        Create transaction in bml
        :param payload:
        :type payload:
        :return:
        :rtype:
        """
        endpoint = "/public/v2/transactions"
        response = requests.post(self.api_path(endpoint), json=payload, headers=self.headers)
        return response