"""
This is the main file for the flask app.
"""

import os

import requests
from dotenv import load_dotenv
from flask import Flask, redirect, request

from bankofmaldives.bankofmaldives import BankofmaldivesAPI
from Subscriptions.subscription import Subscription

app = Flask(__name__)

# Load the environment variables from .env file
load_dotenv()


def require_env(name):
    """Read a required environment variable, failing loudly at startup if it is missing."""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Required environment variable {name} is not set. See README.md.")
    return value


BML_API_KEY = require_env("BML_API_KEY")
PABBLY_USERNAME = require_env("PABBLY_USERNAME")
PABBLY_PASSWORD = require_env("PABBLY_PASSWORD")
DEFAULT_REDIRECT_URL = require_env("DEFAULT_REDIRECT_URL")
TELEGRAM_BOT_TOKEN = require_env("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = require_env("TELEGRAM_CHAT_ID")
DOMAIN = require_env("DOMAIN")

# Create instances of the APIs
bml_instance = BankofmaldivesAPI(BML_API_KEY)
pabbly_instance = Subscription(PABBLY_USERNAME, PABBLY_PASSWORD)


def error_logging(message):
    """Send a message to the configured Telegram chat, wrapped in a code block.

    Requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to be set.
    """

    # send in markdown format with code block
    message = "``` " + "\n" + message + "\n" + " ```"

    requests.post(
        "https://api.telegram.org/bot" + TELEGRAM_BOT_TOKEN + "/sendMessage?parse_mode=Markdown",
        data={"chat_id": TELEGRAM_CHAT_ID, "text": message},
    )

    return True


@app.route("/pabbly", methods=["GET"])  # DONT ASK WHY LOL
def process_subscription_pabbly():
    """Start a BML payment for a Pabbly hosted page.

    Reads the hosted page from Pabbly, converts the invoice into a BML transaction
    payload, and redirects the customer to the BML payment URL.

    Raises:
        Exception: if BML does not return a 201.
    """
    # Get hosted page details
    hosted_page = request.args.get("hostedpage")
    api_data = pabbly_instance.hostedPage(hosted_page)
    api_data = api_data.json()
    api_data = api_data["data"]

    # Extract relevant data
    _subscription = api_data["subscription"]
    invoice = api_data["invoice"]
    amount = invoice["due_amount"]
    invoice_id = invoice["id"]
    amount *= 100  # because cents

    payload = {
        "amount": amount,
        "currency": "MVR",
        "localId": invoice_id,
        "tokenizationDetails": {"tokenize": False, "paymentType": "UNSCHEDULED", "recurringFrequency": "UNSCHEDULED"},
        "redirectUrl": DOMAIN + "/thankyou",
    }

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
    """Record a completed BML payment against its Pabbly invoice.

    The BML transaction carries the Pabbly invoice id in ``localId``. Recording is
    skipped if the invoice is already marked paid, so this is safe to call twice.

    Returns:
        str: the Pabbly product id for the invoice.

    Raises:
        Exception: if BML rejects the lookup or the invoice is in an unexpected state.
    """
    # Query the transaction to get the local id
    transaction_data = bml_instance.get_transaction(transaction_id)

    if transaction_data.status_code == 200:
        transaction_data = transaction_data.json()
        pabbly_invoice_id = transaction_data["localId"]  # localId was set to invoice id we got from pabbly
        pabbly_invoice_status, product_id = pabbly_instance.payment_status(pabbly_invoice_id)

        if pabbly_invoice_status == "success":  # already recorded; just hand back the product id
            return product_id

        elif pabbly_invoice_status == "created":  # not recorded yet, so record it now
            # Invoice hasn't been paid yet, so we record the payment
            payment_mode, transaction_data, payment_note = "BML", "Transaction Completed", "Payment Success"
            product_id = pabbly_instance.recordPayment(pabbly_invoice_id, payment_mode, payment_note, transaction_data)
            return product_id
        else:
            error_logging("Invalid invoice status: " + pabbly_invoice_status)
            raise Exception("Invalid invoice status: " + pabbly_invoice_status)
    else:
        # API call unsuccessful
        transaction_data = transaction_data.text
        error_logging("Invalid transaction data: " + str(transaction_data))
        raise Exception("Invalid transaction data: " + str(transaction_data))


@app.route("/hook", methods=["POST"])
def bml_hook():
    """Webhook BML calls when a transaction changes state.

    Confirms the state with BML directly rather than trusting the payload, then
    records the payment. BML retries any non-2xx response.
    """
    webhook_data = request.get_json(silent=True) or {}
    transaction_id = webhook_data.get("transactionId")
    if not transaction_id:
        error_logging("Webhook received without a transactionId: " + str(webhook_data))
        return "Missing transactionId", 400

    transaction = bml_instance.get_transaction(transaction_id)

    if transaction.status_code != 200:
        error_logging("Invalid transaction data: " + str(transaction.text))
        raise Exception("Invalid transaction data: " + str(transaction.text))

    transaction = transaction.json()
    state = transaction["state"]

    if state == "CONFIRMED":
        return record_payment(transaction_id)

    elif state == "CANCELLED":
        error_logging("Transaction was cancelled")
        raise Exception("Transaction was cancelled")

    elif state == "QR_CODE_GENERATED":
        # Informational only -- BML retries any non-2xx, so acknowledge it.
        error_logging("QR Code was generated for transaction")
        return "QR_CODE_GENERATED", 200

    else:
        error_logging("Invalid transaction state: " + str(state))
        raise Exception("Invalid transaction state: " + str(state))


@app.route("/thankyou", methods=["GET"])
def thankyou():
    """Landing route BML redirects the customer to after payment.

    The ``state`` query parameter is treated as a hint only -- the transaction is
    re-checked against BML before anything is recorded. On success the customer is
    sent to the product's configured redirect URL, otherwise to DEFAULT_REDIRECT_URL.
    """
    # Get the get parameters
    # signature = request.args.get('signature')
    transactionId_param = request.args.get("transactionId")
    state_param = request.args.get("state")

    if state_param == "CONFIRMED":
        # The Get Param says the payment was successful, so we check with bml servers to confirm
        transaction = bml_instance.get_transaction(transactionId_param)
        transaction = transaction.json()

        if transaction["state"] == "CONFIRMED":
            product_id = record_payment(transactionId_param)
            redirect_url = pabbly_instance.redirect(product_id)
            if not redirect_url or redirect_url == "NONE":
                redirect_url = DEFAULT_REDIRECT_URL

            error_logging("Redirecting to: " + redirect_url)
            return redirect(redirect_url)

        elif transaction["state"] == "CANCELLED":
            error_logging("Transaction was cancelled")
            return redirect(DEFAULT_REDIRECT_URL)

        else:
            error_logging("Invalid transaction state: " + transaction["state"])
            raise Exception("Invalid transaction state: " + transaction["state"])

    elif state_param == "CANCELLED":
        return "CANCELLED"

    else:
        # Reachable by anyone who finds the domain, so this stays silent too. A real
        # customer always arrives here with a state from BML.
        return redirect(DEFAULT_REDIRECT_URL)


@app.route("/", methods=["GET"])
def index():
    """Redirect to DEFAULT_REDIRECT_URL.

    Deliberately silent: this path is reachable by anyone who finds the domain, so
    reporting hits to Telegram just means crawler traffic floods the chat.
    """
    return redirect(DEFAULT_REDIRECT_URL)


@app.route("/health", methods=["GET"])
def health():
    """Liveness probe. Deliberately silent -- safe to poll on a short interval."""
    return {"status": "ok"}, 200


# as app starts, send a message to telegram
error_logging("APP STARTED")
