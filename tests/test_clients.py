"""Tests for the Pabbly and Bank of Maldives API clients."""

from unittest.mock import patch

import pytest

from Subscriptions.exceptions import UnknownResponse
from tests.conftest import make_response


class TestBankOfMaldives:
    def test_get_transaction_targets_v2_endpoint(self, bml):
        with patch("bankofmaldives.bankofmaldives.requests.get") as get:
            get.return_value = make_response(200, {"state": "CONFIRMED"})
            bml.get_transaction("txn_1")

        url = get.call_args.args[0]
        assert url.endswith("/public/v2/transactions/txn_1")
        assert get.call_args.kwargs["headers"]["Authorization"] == "test-bml-key"

    def test_create_transaction_posts_json(self, bml):
        with patch("bankofmaldives.bankofmaldives.requests.post") as post:
            post.return_value = make_response(201, {"url": "https://bml.example.com/pay"})
            bml.create_transaction({"amount": 100})

        assert post.call_args.args[0].endswith("/public/v2/transactions")
        assert post.call_args.kwargs["json"] == {"amount": 100}


class TestPabblyHostedPage:
    def test_returns_response_on_success(self, pabbly):
        with patch("Subscriptions.subscription.requests.request") as request:
            request.return_value = make_response(200, {"data": {}})
            result = pabbly.hostedPage("hp_1")

        assert result.status_code == 200
        assert request.call_args.kwargs["json"] == {"hostedpage": "hp_1"}
        assert request.call_args.kwargs["auth"] == ("test-user", "test-pass")

    def test_raises_on_non_200(self, pabbly):
        with patch("Subscriptions.subscription.requests.request") as request:
            request.return_value = make_response(500, text="boom")
            with pytest.raises(UnknownResponse):
                pabbly.hostedPage("hp_2")


class TestPabblyRecordPayment:
    def test_returns_product_id(self, pabbly):
        with patch("Subscriptions.subscription.requests.post") as post:
            post.return_value = make_response(200, {"data": {"product": {"id": "prod_9"}}})
            product_id = pabbly.recordPayment("inv_1", "BML", "Payment Success", "Completed")

        assert product_id == "prod_9"
        assert post.call_args.args[0].endswith("invoice/recordpayment/inv_1")

    def test_raises_on_failure(self, pabbly):
        with patch("Subscriptions.subscription.requests.post") as post:
            post.return_value = make_response(422, text="nope")
            with pytest.raises(UnknownResponse):
                pabbly.recordPayment("inv_2", "BML", "note", "data")


class TestPabblyPaymentStatus:
    def test_unpacks_status_and_product(self, pabbly):
        body = {"message": [{"status": "created", "product_id": "prod_3"}]}
        with patch("Subscriptions.subscription.requests.get") as get:
            get.return_value = make_response(200, body)
            status, product_id = pabbly.payment_status("inv_3")

        assert (status, product_id) == ("created", "prod_3")

    def test_raises_on_error_status(self, pabbly):
        with patch("Subscriptions.subscription.requests.get") as get:
            get.return_value = make_response(404, text="missing")
            with pytest.raises(Exception, match="404"):
                pabbly.payment_status("inv_4")


class TestPabblyRedirect:
    def test_returns_configured_redirect_url(self, pabbly):
        body = {"data": [{"redirect_url": "https://course.example.com"}]}
        with patch("Subscriptions.subscription.requests.get") as get:
            get.return_value = make_response(200, body)
            assert pabbly.redirect("prod_1") == "https://course.example.com"

    def test_falls_back_to_default_when_field_absent(self, pabbly, env):
        with patch("Subscriptions.subscription.requests.get") as get:
            get.return_value = make_response(200, {"data": [{}]})
            assert pabbly.redirect("prod_2") == env["DEFAULT_REDIRECT_URL"]

    def test_returns_none_sentinel_on_error(self, pabbly):
        with patch("Subscriptions.subscription.requests.get") as get:
            get.return_value = make_response(500)
            assert pabbly.redirect("prod_3") == "NONE"
