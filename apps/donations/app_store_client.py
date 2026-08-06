# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Thin client for verifying Apple StoreKit signed transactions.

Built on Apple's own `app-store-server-library`, which owns the cryptographic
signature verification (`SignedDataVerifier`) — so this module only has to
wire that library to this project's settings and translate its exceptions
into ours.

`signed_transaction` is the JWS blob the client obtains locally from
StoreKit (`Transaction.jwsRepresentation`) for its own purchase, and submits
as-is; verifying its signature is what authenticates the purchase.

Isolated from services.py so those details stay out of the business logic,
and so tests can stub `_verifier` instead of mocking certificate chains.

`SignedDataVerifier` is built with `enable_online_checks=False`, so
verification is fully local and never makes a network call — see its
docstring for the offline/online tradeoff.
"""

from pathlib import Path

from appstoreserverlibrary.models.Environment import Environment
from appstoreserverlibrary.models.JWSTransactionDecodedPayload import (
    JWSTransactionDecodedPayload,
)
from appstoreserverlibrary.signed_data_verifier import (
    SignedDataVerifier,
    VerificationException,
    VerificationStatus,
)
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

_ROOT_CERTIFICATE_PATH = (
    Path(__file__).resolve().parent / "certs" / "AppleRootCA-G3.cer"
)


class AppleStoreError(Exception):
    """Base class for App Store transaction verification failures."""


class TransactionVerificationError(AppleStoreError):
    """Apple's signature over a transaction payload could not be verified.

    Covers an untrusted/malformed signature, a bundle id or app id that
    doesn't match this app, and a transaction whose environment matches
    neither production nor sandbox.
    """


def verify_signed_transaction(signed_transaction: str) -> JWSTransactionDecodedPayload:
    """Verify and decode a client-submitted signed transaction blob.

    Tries production first, then falls back to the sandbox environment when
    the payload turns out to be a sandbox (TestFlight) transaction — the
    verifier can only tell after decoding, since the client has no reliable
    way to say which environment it's running in.

    Args:
        signed_transaction: The JWS string the client obtained from StoreKit
            for its own transaction (`Transaction.jwsRepresentation`).

    Returns:
        JWSTransactionDecodedPayload: The verified, decoded transaction.

    Raises:
        TransactionVerificationError: If Apple's signature over the payload
            could not be verified, for either environment.
    """
    try:
        return _verifier(Environment.PRODUCTION).verify_and_decode_signed_transaction(
            signed_transaction
        )
    except VerificationException as exc:
        if exc.status != VerificationStatus.INVALID_ENVIRONMENT:
            raise TransactionVerificationError(str(exc)) from exc

    try:
        return _verifier(Environment.SANDBOX).verify_and_decode_signed_transaction(
            signed_transaction
        )
    except VerificationException as exc:
        raise TransactionVerificationError(str(exc)) from exc


def _verifier(environment: Environment) -> SignedDataVerifier:
    """Build a signature verifier for one environment.

    Isolated in its own function so tests can stub this seam instead of
    performing a real certificate-chain verification.

    Raises:
        ImproperlyConfigured: If the Apple app identity is not set.
    """
    if not settings.APPLE_BUNDLE_ID or not settings.APPLE_APP_APPLE_ID:
        raise ImproperlyConfigured(
            "APPLE_BUNDLE_ID and APPLE_APP_APPLE_ID must both be configured "
            "to verify App Store signed transactions."
        )
    return SignedDataVerifier(
        [_ROOT_CERTIFICATE_PATH.read_bytes()],
        False,
        environment,
        settings.APPLE_BUNDLE_ID,
        settings.APPLE_APP_APPLE_ID,
    )
