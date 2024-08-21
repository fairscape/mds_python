from pydantic import BaseModel, Field
from cryptography.fernet import Fernet
import os

class APIToken(BaseModel):
    user_id: str
    encrypted_token: str

    @classmethod
    def create(cls, user_id: str, token: str):
        key = os.environ.get('ENCRYPTION_KEY')
        if not key:
            raise ValueError("Encryption key not set in environment variables")
        f = Fernet(key)
        encrypted_token = f.encrypt(token.encode()).decode()
        return cls(user_id=user_id, encrypted_token=encrypted_token)

    def decrypt_token(self):
        key = os.environ.get('ENCRYPTION_KEY')
        if not key:
            raise ValueError("Encryption key not set in environment variables")
        f = Fernet(key)
        return f.decrypt(self.encrypted_token.encode()).decode()

class DataversePublishSettings(BaseModel):
    base_url: str = Field(..., description="Base URL of the Dataverse instance")
    dataverse_id: str = Field(..., description="ID or alias of the target dataverse")