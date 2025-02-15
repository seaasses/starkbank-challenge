import requests
import base64
from starkbank import Project
from datetime import datetime
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization


class StarkBankSignatureVerifier:
    def __init__(self, starkbank_project: Project):
        self.api_url = (
            "https://sandbox.api.starkbank.com"
            if starkbank_project.environment == "sandbox"
            else "https://api.starkbank.com"
        )
        self.__get_public_keys()

    def check_signature(
        self, message: str, signature: str, signature_datetime: datetime
    ):
        try:
            signature_bytes = base64.b64decode(signature)
            public_key = self.__get_public_key(signature_datetime)
            public_key.verify(signature_bytes, message, ec.ECDSA(hashes.SHA256()))
            return True
        except InvalidSignature:
            return False
        except Exception:  # TODO: add more specific exceptions
            return False

    def __get_public_key(self, signature_datetime: datetime):
        return self.public_keys[0][
            "content"
        ]  # TODO: use the datetime to get the correct key

    def __get_public_keys(self):
        response = requests.get(f"{self.api_url}/v2/public-key")
        if response.status_code != 200:
            raise Exception(f"Failed to get signatures: {response.status_code}")
        public_keys = [
            {
                "content": serialization.load_pem_public_key(
                    key["content"].encode("utf-8")
                ),
                "created": datetime.fromisoformat(key["created"]),
            }
            for key in response.json()["publicKeys"]
        ]
        self.public_keys = list(
            sorted(public_keys, key=lambda x: x["created"], reverse=True)
        )
