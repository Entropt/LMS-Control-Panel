# utils/key_generator.py - Generate RSA keys for LTI authentication
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import os
import base64
import json

def generate_rsa_keys():
    """Generate RSA key pair for LTI tool"""
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    
    # Extract public key
    public_key = private_key.public_key()
    
    # Serialize private key to PEM format
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # Serialize public key to PEM format
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    return {
        'private_key': private_pem.decode('utf-8'),
        'public_key': public_pem.decode('utf-8')
    }

def create_jwk_from_public_key(public_key_pem):
    """
    Create a JWK (JSON Web Key) representation of the public key
    This will be exposed to Canvas LMS
    """
    # Load the public key
    public_key = serialization.load_pem_public_key(
        public_key_pem.encode('utf-8')
    )
    
    # Export the key in DER format
    public_numbers = public_key.public_numbers()
    
    # Create JWK
    jwk = {
        "kty": "RSA",
        "e": base64.urlsafe_b64encode(public_numbers.e.to_bytes((public_numbers.e.bit_length() + 7) // 8, byteorder='big')).decode('utf-8').rstrip('='),
        "n": base64.urlsafe_b64encode(public_numbers.n.to_bytes((public_numbers.n.bit_length() + 7) // 8, byteorder='big')).decode('utf-8').rstrip('='),
        "alg": "RS256",
        "use": "sig",
        "kid": "juice-shop-tool-key"
    }
    
    return json.dumps(jwk)

if __name__ == "__main__":
    # Generate keys and print them
    keys = generate_rsa_keys()
    print("Private Key:")
    print(keys['private_key'])
    print("\nPublic Key:")
    print(keys['public_key'])
    
    # Generate JWK
    jwk = create_jwk_from_public_key(keys['public_key'])
    print("\nJWK:")
    print(jwk)