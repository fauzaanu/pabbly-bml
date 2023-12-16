import json
import os

import requests

from Subscriptions.exceptions import UnknownResponse


class Subscription:
    def __init__(self, username, password):
        self.apiUrl = "https://payments.pabbly.com/api/v1/"
        self.thankyouUrl = "https://payments.pabbly.com/thankyou/"
        self.username = username
        self.password = password

        self.headers = {
            "cookie": "SameSite=None",
            "Content-Type": "application/json",
        }

    def apiPath(self, path):
        return self.apiUrl + path

    def hostedPage(self, hostedpage):

        payload = {
            "hostedpage": f"{hostedpage}"
        }

        response = requests.request("POST", self.apiPath('hostedpage'), json=payload, headers=self.headers,
                                    auth=(self.username, self.password))

        if response.status_code != 200:
            raise UnknownResponse(response.text)

        return response

    def subscribe(self, data):
        """
        not ready to be used
        :param data:
        :type data:
        :return:
        :rtype:
        """
        response = requests.post(self.apiPath('subscription'), auth=(self.username, self.password), data=data)
        if response.status_code != 200:
            raise UnknownResponse(response.text)
        return response.json()

    def recordPayment(self, invoice_id, payment_mode, payment_note, transaction_data):
        """
        Record the payment, return the product id
        """
        response = requests.post(self.apiPath('invoice/recordpayment/' + invoice_id),
                                 auth=(self.username, self.password), data={
                'payment_mode': payment_mode,
                'payment_note': payment_note,
                'transaction': transaction_data
            })
        if response.status_code == 200:
            response = response.json()
            product_id = response['data']['product']['id']
            return product_id
        else:
            raise UnknownResponse(response.text)

    def redirect(self, productId: str):
        # https://payments.pabbly.com/api/v1/checkoutpage/6557ba7dd851d8cbc68570e8
        response = requests.get(self.apiPath('checkoutpage/' + productId), auth=(self.username, self.password))
        if response.status_code == 200:
            response = response.json()
            try:
                redirectUrl = response['data'][0]['redirect_url']
                return redirectUrl
            except:
                redirectUrl = os.getenv('DEFAULT_REDIRECT_URL')
                return redirectUrl
        else:
            return 'NONE'


    def get_plancode(self, productId: str):
        """
        Gets the plan code for a given product ID.

        Args:
            self: The instance of the class.
            productId (str): The ID of the product for which to retrieve the plan code.

        Returns:
            str: The plan code of the product.

        Raises:
            Exception: If there is an error retrieving the plan code.

        Example:
            # Create an instance of the class
            obj = ClassName()

            # Get the plan code for a product with ID 'example_id'
            plan_code = obj.get_plancode('example_id')
        """
        response = requests.get(self.apiPath('checkoutpage/' + productId), auth=(self.username, self.password))
        if response.status_code == 200:
            response = response.json()
            if response['status'] != 'success':
                raise Exception('Error: ' + str(response.text))
            try:
                plan_code = response['data'][0]['plan_code']
                return plan_code
            except:
                raise Exception('Error: ' + str(response.text))
        else:
            return 'NONE'


    def payment_status(self, invoice_id:str):
        """
        Get the payment status
        :param invoice_id: invoice id from pabbly
        :type invoice_id: str
        :return: status, product_id
        :rtype: str, str
        """
        # check payment status from pabbly
        response = requests.get(self.apiPath('invoices/transactions/' + invoice_id),
                                      auth=(self.username, self.password))
        if response.status_code == 200:
            invoice_status = response.json()
            status = invoice_status["message"][0]["status"]
            product_id = invoice_status["message"][0]["product_id"]
            return status, product_id
        else:
            raise Exception('Error: ' + str(response.status_code) + ': ' + str(response.text))

    def get_customer_id(self, invoice_id:str):
        """
        Gets the customer ID and product ID associated with a given invoice ID.

        Parameters:
            invoice_id (str): The ID of the invoice to retrieve customer and product information for.

        Returns:
            tuple: A tuple containing the customer ID and product ID.

        Raises:
            Exception: If there is an error while retrieving the invoice data.
        """
        # Get invoice data from pabbly
        response = requests.get(self.apiPath('invoice/' + invoice_id),
                                auth=(self.username, self.password))
        if response.status_code == 200:
            invoice_data = response.json()
            customer_id = invoice_data.get('data').get('customer_id')
            product_id = invoice_data.get('data').get('product_id')
            return product_id, customer_id,
        else:
            raise Exception('Error: ' + str(response.status_code) + ': ' + str(response.text))


    def get_customer_details(self, customer_id:str):
        """
        Get the customer details
        :param customer_id: customer id from pabbly
        :type customer_id: str
        :return: first_name, last_name, email_id
        :rtype: str, str, str
        """
        # Get customer data from pabbly
        response = requests.get(self.apiPath('customer/' + customer_id),
                                auth=(self.username, self.password))
        if response.status_code == 200:
            customer_data = response.json()
            first_name = customer_data.get('data').get('first_name')
            last_name = customer_data.get('data').get('last_name')
            email_id = customer_data.get('data').get('email_id')
            return first_name, last_name, email_id
        else:
            raise Exception('Error: ' + str(response.status_code) + ': ' + str(response.text))





    # def activateTrialSubscription(self, subscription_id):
    #     if not subscription_id:
    #         error = {'Error': 'invoice id is required'}
    #         return json.dumps(error)
    #     response = requests.post(self.apiPath('subscription/activatetrial/' + subscription_id),
    #                              auth=(self.username, self.password))
    #     if response.status_code != 200:
    #         error = {'Error': str(response.status_code) + ': ' + response.text}
    #         return json.dumps(error)
    #     return response.json()
    #
    # def getCustomer(self, customerId):
    #     response = requests.get(self.apiPath('customer/' + customerId), auth=(self.username, self.password))
    #     if response.status_code != 200:
    #         error = {'Error': str(response.status_code) + ': ' + response.text}
    #         return json.dumps(error)
    #     return response.json()
