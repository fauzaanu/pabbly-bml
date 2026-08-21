"""Tests for the Flask route handlers."""

import pytest

from tests.conftest import make_response


class TestIndex:
    def test_redirects_to_default(self, client, env):
        response = client.get("/")
        assert response.status_code == 302
        assert response.headers["Location"] == env["DEFAULT_REDIRECT_URL"]

    def test_is_silent(self, client, telegram):
        """Anyone can find the root path -- crawler hits must not reach Telegram."""
        client.get("/", headers={"User-Agent": "crawler/1.0", "CF-Connecting-IP": "203.0.113.7"})
        telegram.assert_not_called()


class TestPabbly:
    def test_converts_rufiyaa_to_cents_and_redirects(self, client, pabbly_api, bml_api):
        pabbly_api.hostedPage.return_value = make_response(
            json_body={"data": {"subscription": {}, "invoice": {"due_amount": 250, "id": "inv_1"}}}
        )
        bml_api.create_transaction.return_value = make_response(201, {"url": "https://bml.example.com/pay/abc"})

        response = client.get("/pabbly?hostedpage=hp_1")

        assert response.status_code == 302
        assert response.headers["Location"] == "https://bml.example.com/pay/abc"
        payload = bml_api.create_transaction.call_args.args[0]
        assert payload["amount"] == 25000, "amount must be sent to BML in cents"
        assert payload["currency"] == "MVR"
        assert payload["localId"] == "inv_1"
        assert payload["redirectUrl"] == "https://pay.example.com/thankyou"

    def test_raises_when_bml_rejects(self, client, pabbly_api, bml_api):
        pabbly_api.hostedPage.return_value = make_response(
            json_body={"data": {"subscription": {}, "invoice": {"due_amount": 10, "id": "inv_2"}}}
        )
        bml_api.create_transaction.return_value = make_response(400, text="bad request")

        with pytest.raises(Exception, match="Invalid response from bml"):
            client.get("/pabbly?hostedpage=hp_2")


class TestHook:
    def test_confirmed_records_payment(self, client, bml_api, pabbly_api):
        bml_api.get_transaction.return_value = make_response(200, {"state": "CONFIRMED", "localId": "inv_3"})
        pabbly_api.payment_status.return_value = ("created", "prod_1")
        pabbly_api.recordPayment.return_value = "prod_1"

        response = client.post("/hook", json={"transactionId": "txn_3"})

        assert response.status_code == 200
        pabbly_api.recordPayment.assert_called_once()
        assert pabbly_api.recordPayment.call_args.args[0] == "inv_3"

    def test_already_paid_is_not_recorded_twice(self, client, bml_api, pabbly_api):
        bml_api.get_transaction.return_value = make_response(200, {"state": "CONFIRMED", "localId": "inv_4"})
        pabbly_api.payment_status.return_value = ("success", "prod_2")

        response = client.post("/hook", json={"transactionId": "txn_4"})

        assert response.status_code == 200
        pabbly_api.recordPayment.assert_not_called()

    def test_qr_generated_is_acknowledged(self, client, bml_api):
        bml_api.get_transaction.return_value = make_response(200, {"state": "QR_CODE_GENERATED"})
        response = client.post("/hook", json={"transactionId": "txn_5"})
        assert response.status_code == 200

    def test_cancelled_raises(self, client, bml_api):
        bml_api.get_transaction.return_value = make_response(200, {"state": "CANCELLED"})
        with pytest.raises(Exception, match="Transaction was cancelled"):
            client.post("/hook", json={"transactionId": "txn_6"})


class TestThankyou:
    def test_confirmed_redirects_to_product_url(self, client, bml_api, pabbly_api):
        bml_api.get_transaction.return_value = make_response(200, {"state": "CONFIRMED", "localId": "inv_7"})
        pabbly_api.payment_status.return_value = ("success", "prod_3")
        pabbly_api.redirect.return_value = "https://course.example.com/welcome"

        response = client.get("/thankyou?transactionId=txn_7&state=CONFIRMED")

        assert response.status_code == 302
        assert response.headers["Location"] == "https://course.example.com/welcome"

    def test_falls_back_when_no_product_redirect(self, client, bml_api, pabbly_api, env):
        bml_api.get_transaction.return_value = make_response(200, {"state": "CONFIRMED", "localId": "inv_8"})
        pabbly_api.payment_status.return_value = ("success", "prod_4")
        pabbly_api.redirect.return_value = "NONE"

        response = client.get("/thankyou?transactionId=txn_8&state=CONFIRMED")

        assert response.headers["Location"] == env["DEFAULT_REDIRECT_URL"]

    def test_cancelled_param_short_circuits(self, client, bml_api):
        response = client.get("/thankyou?transactionId=txn_9&state=CANCELLED")
        assert response.status_code == 200
        assert response.get_data(as_text=True) == "CANCELLED"
        bml_api.get_transaction.assert_not_called()

    def test_bank_disagrees_with_confirmed_param(self, client, bml_api, env):
        bml_api.get_transaction.return_value = make_response(200, {"state": "CANCELLED"})
        response = client.get("/thankyou?transactionId=txn_10&state=CONFIRMED")
        assert response.headers["Location"] == env["DEFAULT_REDIRECT_URL"]

    def test_missing_state_redirects_to_default(self, client, env):
        response = client.get("/thankyou")
        assert response.headers["Location"] == env["DEFAULT_REDIRECT_URL"]


class TestHealth:
    def test_returns_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.get_json() == {"status": "ok"}

    def test_is_silent(self, client, telegram):
        """A healthcheck runs constantly -- it must never reach Telegram."""
        for _ in range(5):
            client.get("/health")
        telegram.assert_not_called()


class TestCrawlerSilence:
    """Public GET paths must not report to Telegram -- anyone can find them."""

    def test_public_paths_send_nothing(self, client, telegram):
        for path in ("/", "/health", "/thankyou"):
            client.get(path)
        telegram.assert_not_called()
