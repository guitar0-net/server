# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for the Apple signed-transaction verification client."""

import pytest
from appstoreserverlibrary.models.Environment import Environment
from appstoreserverlibrary.models.JWSTransactionDecodedPayload import (
    JWSTransactionDecodedPayload,
)
from appstoreserverlibrary.signed_data_verifier import (
    VerificationException,
    VerificationStatus,
)
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from django.core.exceptions import ImproperlyConfigured

from apps.donations import app_store_client


@pytest.fixture(autouse=True)
def _configure_apple_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "apps.donations.app_store_client.settings.APPLE_BUNDLE_ID", "net.guitar0.app"
    )
    monkeypatch.setattr(
        "apps.donations.app_store_client.settings.APPLE_APP_APPLE_ID", 987654321
    )


class _FakeVerifier:
    """Stands in for SignedDataVerifier, avoiding a real certificate check."""

    def __init__(
        self,
        decoded: JWSTransactionDecodedPayload | None = None,
        error: Exception | None = None,
    ) -> None:
        self._decoded = decoded
        self._error = error

    def verify_and_decode_signed_transaction(
        self, signed_transaction: str
    ) -> JWSTransactionDecodedPayload:
        assert signed_transaction
        if self._error is not None:
            raise self._error
        assert self._decoded is not None
        return self._decoded


def _stub_verifiers(
    monkeypatch: pytest.MonkeyPatch, verifiers_by_environment: dict[Environment, object]
) -> None:
    monkeypatch.setattr(
        "apps.donations.app_store_client._verifier",
        lambda environment: verifiers_by_environment[environment],
    )


def test_verify_signed_transaction_returns_the_verified_production_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    decoded = JWSTransactionDecodedPayload(productId="thank-you", transactionId="1")
    _stub_verifiers(
        monkeypatch, {Environment.PRODUCTION: _FakeVerifier(decoded=decoded)}
    )

    result = app_store_client.verify_signed_transaction("jws-1")

    assert result.productId == "thank-you"


def test_verify_signed_transaction_falls_back_to_sandbox_on_environment_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    decoded = JWSTransactionDecodedPayload(productId="thank-you", transactionId="2")
    _stub_verifiers(
        monkeypatch,
        {
            Environment.PRODUCTION: _FakeVerifier(
                error=VerificationException(VerificationStatus.INVALID_ENVIRONMENT)
            ),
            Environment.SANDBOX: _FakeVerifier(decoded=decoded),
        },
    )

    result = app_store_client.verify_signed_transaction("jws-2")

    assert result.transactionId == "2"


def test_verify_signed_transaction_raises_when_the_signature_is_untrusted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_verifiers(
        monkeypatch,
        {
            Environment.PRODUCTION: _FakeVerifier(
                error=VerificationException(VerificationStatus.INVALID_CERTIFICATE)
            )
        },
    )

    with pytest.raises(app_store_client.TransactionVerificationError):
        app_store_client.verify_signed_transaction("jws-3")


def test_verify_signed_transaction_raises_when_sandbox_also_rejects_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_verifiers(
        monkeypatch,
        {
            Environment.PRODUCTION: _FakeVerifier(
                error=VerificationException(VerificationStatus.INVALID_ENVIRONMENT)
            ),
            Environment.SANDBOX: _FakeVerifier(
                error=VerificationException(VerificationStatus.INVALID_ENVIRONMENT)
            ),
        },
    )

    with pytest.raises(app_store_client.TransactionVerificationError):
        app_store_client.verify_signed_transaction("jws-4")


def test_verify_signed_transaction_raises_when_the_bundle_id_is_not_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "apps.donations.app_store_client.settings.APPLE_BUNDLE_ID", None
    )

    with pytest.raises(ImproperlyConfigured):
        app_store_client.verify_signed_transaction("jws-5")


def test_verify_signed_transaction_raises_when_the_apple_app_id_is_not_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "apps.donations.app_store_client.settings.APPLE_APP_APPLE_ID", None
    )

    with pytest.raises(ImproperlyConfigured):
        app_store_client.verify_signed_transaction("jws-6")


def test_bundled_root_certificate_is_a_valid_der_encoded_certificate() -> None:
    certificate_bytes = app_store_client._ROOT_CERTIFICATE_PATH.read_bytes()

    certificate = x509.load_der_x509_certificate(certificate_bytes, default_backend())

    assert certificate.subject.rfc4514_string() == (
        "C=US,O=Apple Inc.,OU=Apple Certification Authority,CN=Apple Root CA - G3"
    )
