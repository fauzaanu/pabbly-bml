"""
This is the main file for the flask app.
"""
import os
import requests
from flask import Flask, request, redirect
from flask.cli import load_dotenv

from Subscriptions.subscription import Subscription
from bankofmaldives.bankofmaldives import BankofmaldivesAPI
from xperiencify.exceptions import InvalidMagicLink
from xperiencify.redirect import create_student

app = Flask(__name__)

# Load the environment variables from .env file
load_dotenv()

# Create instances of the APIs
bml_instance = BankofmaldivesAPI(os.getenv('BML_API_KEY'))
pabbly_instance = Subscription(os.getenv('PABBLY_USERNAME'), os.getenv('PABBLY_PASSWORD'))


def error_logging(message):
    """

    This method sends an error message to a specific Telegram chat using the Telegram Bot API.

    Parameters:
    - message (str): The error message to be sent.

    Returns:
    - True: If the error message was successfully sent to the Telegram chat.

    Example usage:
        error_logging("An error occurred while processing the data.")

    Please make sure to set the environment variables TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID before using this method.

    """

    # send in markdown format with code block
    message = "``` " + "\n" + message + "\n" + " ```"

    requests.post("https://api.telegram.org/bot" + os.getenv('TELEGRAM_BOT_TOKEN') + "/sendMessage?parse_mode=Markdown",
                  data={'chat_id': os.getenv('TELEGRAM_CHAT_ID'), 'text': message})

    return True


@app.route('/pabbly', methods=['GET'])  # DONT ASK WHY LOL
def process_subscription_pabbly():
    """

    Process Subscription Pabbly

    This method handles the processing of a subscription through Pabbly payment gateway. It extracts relevant data from the API response, prepares a payload for the BML payment gateway,
    * and redirects the user to the BML payment URL.

    Parameters:
        None

    Returns:
        None

    Raises:
        Exception: If there is an invalid response from the BML payment gateway.

    Example:
        This method is typically used as a route handler for the '/pabbly.php' endpoint in a Flask application.

    """
    # Get hosted page details
    hosted_page = request.args.get('hostedpage')
    api_data = pabbly_instance.hostedPage(hosted_page)
    api_data = api_data.json()
    api_data = api_data["data"]

    # Extract relevant data
    _subscription = api_data["subscription"]
    invoice = api_data["invoice"]
    amount = invoice["charge_amount"]
    invoice_id = invoice["id"]
    amount *= 100  # because cents

    payload = {
        "amount": amount,
        "currency": "MVR",
        "localId": invoice_id,
        "tokenizationDetails": {
            "tokenize": False,
            "paymentType": "UNSCHEDULED",
            "recurringFrequency": "UNSCHEDULED"
        },
        "redirectUrl": str(os.getenv("DOMAIN")) + "/thankyou"
    }

    username, password = os.getenv('PABBLY_USERNAME'), os.getenv('PABBLY_PASSWORD')

    # Create instances of the APIs
    error_logging("Username: " + username)
    error_logging("Password: " + password)


    error_logging("Hosted Page Data: " + str(hosted_page))

    error_logging("Creating BML Transaction: " + str(payload))

    transaction = bml_instance.create_transaction(payload)
    if transaction.status_code == 201:
        transaction = transaction.json()
        bml_payment_url = transaction["url"]
        return redirect(bml_payment_url)
    else:
        error_logging("Invalid response from bml: " + str(transaction.text))
        error_logging("BML sent unexpected status code: " + str(transaction.status_code))
        raise Exception("Invalid response from bml: " + str(transaction.text))


def record_payment(transaction_id):
    """

    Record Payment

    Queries the transaction to get the local ID and records the payment if it hasn't been recorded already.

    Parameters:
    - transaction_id (str): The ID of the transaction

    Returns:
    - product_id (str): The ID of the product associated with the payment

    Raises:
    - Exception: If the API call to get the transaction data is unsuccessful or if the invoice status is invalid

    """
    # Query the transaction to get the local id
    transaction_data = bml_instance.get_transaction(transaction_id)

    if transaction_data.status_code == 200:
        transaction_data = transaction_data.json()
        pabbly_invoice_id = transaction_data['localId']  # localId was set to invoice id we got from pabbly
        pabbly_invoice_status, product_id = pabbly_instance.payment_status(pabbly_invoice_id)

        if pabbly_invoice_status == "success":  # payment was already recorded, therefore we can just return the product id
            return product_id

        elif pabbly_invoice_status == "created":  # payment want recorded, so we record it
            # Invoice hasn't been paid yet, so we record the payment
            payment_mode, transaction_data, payment_note = "BML", "Transaction Completed", "Payment Success"
            product_id = pabbly_instance.recordPayment(pabbly_invoice_id, payment_mode, payment_note,
                                                       transaction_data)
            return product_id
        else:
            error_logging("Invalid invoice status: " + pabbly_invoice_status)
            raise Exception("Invalid invoice status: " + pabbly_invoice_status)
    else:
        # API call unsuccessful
        transaction_data = transaction_data.text
        error_logging("Invalid transaction data: " + str(transaction_data))
        raise Exception("Invalid transaction data: " + str(transaction_data))


@app.route('/hook', methods=['POST'])
def bml_hook():
    """
    This method is the endpoint for a webhook that handles BML transaction events.

    Parameters:
        None

    Returns:
        None

    Raises:
        Exception: If the transaction state is "CANCELLED" or an invalid state.

    Note:
        This method is an endpoint for a Flask route and must be decorated with the `@app.route` decorator.

    Example Usage:
        The `bml_hook()` method will be called when a POST request is made to the '/hook' route.
    """
    # Create instances of the APIs
    webhook_data = request.json
    transaction_id = webhook_data['transactionId']
    transaction = bml_instance.get_transaction(transaction_id)

    if transaction.status_code == 200:
        transaction = transaction.json()
        if transaction["state"] == "CONFIRMED":
            return record_payment(transaction_id)

        elif transaction["state"] == "CANCELLED":
            error_logging("Transaction was cancelled")
            raise Exception("Transaction was cancelled")

        else:
            error_logging("Invalid transaction state: " + str(transaction["state"]))
            raise Exception("Invalid transaction state: " + str(transaction["state"]))


@app.route('/thankyou', methods=['GET'])
def thankyou():
    """
    This method handles the /thankyou.php route with a GET request.

    Returns:
        - If the `state` parameter is "CONFIRMED", it checks with bml servers to confirm the payment. If the transaction state is "CONFIRMED", it records the payment, generates a redirect
    * URL using the Pabbly instance, and redirects the user to that URL. If the transaction state is "CANCELLED", it logs an error and redirects the user to the default redirect URL. If
    * the transaction state is neither "CONFIRMED" nor "CANCELLED", it logs an error and raises an exception with the invalid state.

        - If the `state` parameter is "CANCELLED", it returns the string "CANCELLED".

        - If the `state` parameter is not provided or is invalid, it logs an error and redirects the user to the default redirect URL.

    Parameters:
        - None

    Example usage:
        @app.route('/thankyou.php', methods=['GET'])
        def thankyou():
            ...
    """
    product_based_redirect_url = None

    # Get the get parameters
    # signature = request.args.get('signature')
    transactionId_param = request.args.get('transactionId')
    state_param = request.args.get('state')

    if state_param == "CONFIRMED":
        # The Get Param says the payment was successful, so we check with bml servers to confirm
        transaction = bml_instance.get_transaction(transactionId_param)
        transaction = transaction.json()

        if transaction["state"] == "CONFIRMED":
            product_id = record_payment(transactionId_param)
            redirect_url = pabbly_instance.redirect(product_id)
            if redirect_url == "NONE":
                redirect_url = os.getenv('DEFAULT_REDIRECT_URL')
            else:
                product_based_redirect_url = redirect_url

            # if experiencify api key is in env, create student
            if os.getenv("XPERIENCIFY_API_KEY"):
                pabbly_invoice_id = transaction['localId']
                product_id, customer_id = pabbly_instance.get_customer_id(pabbly_invoice_id)
                product_code = pabbly_instance.get_plancode(product_id)
                fname, lname, email = pabbly_instance.get_customer_details(customer_id)

                try:
                    redirect_url = create_student(os.getenv("XPERIENCIFY_API_KEY"), email, fname, lname,
                                                  course_id=product_code, )
                    if not redirect_url.startswith("https://"):
                        error_logging("Invalid magic link, falling back")
                        error_logging(redirect_url)
                        if product_based_redirect_url:
                            redirect_url = product_based_redirect_url
                        else:
                            redirect_url = os.getenv('DEFAULT_REDIRECT_URL')
                except InvalidMagicLink:
                    error_logging("Invalid magic link, defaulting back to default redirect url")
                    redirect_url = os.getenv('DEFAULT_REDIRECT_URL')

            error_logging("Redirecting to: " + redirect_url)
            return redirect(redirect_url)

        elif transaction["state"] == "CANCELLED":
            error_logging("Transaction was cancelled")
            return redirect(os.getenv('DEFAULT_REDIRECT_URL'))

        else:
            error_logging("Invalid transaction state: " + transaction["state"])
            raise Exception("Invalid transaction state: " + transaction["state"])

    elif state_param == "CANCELLED":
        return 'CANCELLED'

    else:
        error_logging("State param is None, redirecting to default redirect url")
        return redirect(os.getenv('DEFAULT_REDIRECT_URL'))


@app.route('/', methods=['GET'])
def index():
    """
    This method is the endpoint for the root route.

    Parameters:
        None

    Returns:
        None

    Raises:
        None

    Note:
        This method is an endpoint for a Flask route and must be decorated with the `@app.route` decorator.

    Example Usage:
        The `index()` method will be called when a GET request is made to the '/' route.
    """

    user_agent = request.headers.get('User-Agent')
    ip = request.remote_addr
    cloudflare = request.headers.get('CF-Connecting-IP')
    forwarded_for = request.headers.get('X-Forwarded-For')
    forwarded_proto = request.headers.get('X-Forwarded-Proto')
    forwarded_host = request.headers.get('X-Forwarded-Host')
    log = f"User Agent: {user_agent}\nIP: {ip}\nCloudflare: {cloudflare}\nForwarded For: {forwarded_for}\nForwarded Proto: {forwarded_proto}\nForwarded Host: {forwarded_host}"

    error_logging(log)
    return redirect(os.getenv('DEFAULT_REDIRECT_URL'))


# as app starts, send a message to telegram
error_logging("APP STARTED")
