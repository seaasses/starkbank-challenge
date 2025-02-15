import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta, timezone
import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from app.services.starkbank_signature_verifier.implementation import (
    StarkBankSignatureVerifier,
)


@pytest.fixture
def mock_starkbank_project():
    project = Mock()
    project.environment = "sandbox"
    return project


@pytest.fixture
def mock_key_pairs():
    old_private_key = ec.generate_private_key(ec.SECP256K1())
    old_public_key = old_private_key.public_key()

    current_private_key = ec.generate_private_key(ec.SECP256K1())
    current_public_key = current_private_key.public_key()

    return {
        "old": (old_private_key, old_public_key),
        "current": (current_private_key, current_public_key),
    }


@pytest.fixture
def mock_public_key_response(mock_key_pairs):
    current_time = datetime.now(timezone.utc)
    old_time = current_time - timedelta(days=30)

    def key_to_pem(key):
        return key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")

    return {
        "publicKeys": [
            {
                "content": key_to_pem(mock_key_pairs["current"][1]),
                "created": current_time.isoformat(),
            },
            {
                "content": key_to_pem(mock_key_pairs["old"][1]),
                "created": old_time.isoformat(),
            },
        ]
    }


@pytest.fixture
def verifier(mock_starkbank_project, mock_public_key_response):
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_public_key_response
        return StarkBankSignatureVerifier(mock_starkbank_project)


def test_valid_signature_with_current_key(
    verifier, mock_key_pairs, mock_public_key_response
):
    current_private_key, _ = mock_key_pairs["current"]
    message = "test message"
    current_time = datetime.fromisoformat(
        mock_public_key_response["publicKeys"][0]["created"]
    )

    signature = current_private_key.sign(
        message.encode("utf-8"), ec.ECDSA(hashes.SHA256())
    )
    signature_b64 = base64.b64encode(signature).decode("utf-8")

    result = verifier.check_signature(
        message.encode("utf-8"), signature_b64, current_time + timedelta(hours=1)
    )

    assert result is True


def test_valid_signature_with_old_key(
    verifier, mock_key_pairs, mock_public_key_response
):
    old_private_key, _ = mock_key_pairs["old"]
    message = "test message"
    old_time = datetime.fromisoformat(
        mock_public_key_response["publicKeys"][1]["created"]
    )

    signature = old_private_key.sign(message.encode("utf-8"), ec.ECDSA(hashes.SHA256()))
    signature_b64 = base64.b64encode(signature).decode("utf-8")

    result = verifier.check_signature(
        message.encode("utf-8"),
        signature_b64,
        old_time + timedelta(hours=1),
    )

    assert result is True


def test_invalid_signature(verifier):
    message = "test message"
    invalid_signature = base64.b64encode(b"invalid signature").decode("utf-8")

    result = verifier.check_signature(
        message.encode("utf-8"), invalid_signature, datetime.now(timezone.utc)
    )

    assert result is False


def test_malformed_signature(verifier):
    message = "test message"
    malformed_signature = "not base64 encoded"

    result = verifier.check_signature(
        message.encode("utf-8"), malformed_signature, datetime.now(timezone.utc)
    )

    assert result is False


def test_api_error_handling():
    project = Mock()
    project.environment = "sandbox"

    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 500

        with pytest.raises(Exception) as exc_info:
            StarkBankSignatureVerifier(project)

        assert "Failed to get signatures" in str(exc_info.value)
