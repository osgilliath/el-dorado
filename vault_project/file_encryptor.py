
import os
from cryptography.fernet import Fernet, InvalidToken
from typing import Optional

class FileEncryptor:
    """
    Handles file encryption and decryption using Fernet (AES-128-CBC + HMAC-SHA256).
    Manages a secret key for cryptographic operations.
    """

    def __init__(self, key_path: str = 'secret.key'):
        """
        Initializes the FileEncryptor, loading or creating the secret key.

        Args:
            key_path (str): The path to the file where the secret key is stored.
        """
        self.key_path = key_path
        self.key = self._load_or_create_key()
        self.cipher = Fernet(self.key)

    def _load_or_create_key(self) -> bytes:
        """
        Loads the secret key from the key_path. If the file doesn't exist,
        it generates a new key and saves it.

        Returns:
            bytes: The loaded or newly generated encryption key.
        """
        if os.path.exists(self.key_path):
            with open(self.key_path, 'rb') as key_file:
                key = key_file.read()
            print("Loaded existing secret key.")
        else:
            print("No secret key found. Generating a new one.")
            key = Fernet.generate_key()
            with open(self.key_path, 'wb') as key_file:
                key_file.write(key)
            # Set file permissions to be readable only by the owner
            os.chmod(self.key_path, 0o600)
            print(f"Generated and saved a new secret key to {self.key_path}")
        return key

    def encrypt_file(self, input_path: str, output_path: str) -> None:
        """
        Encrypts a file and saves it to the specified output path.

        Args:
            input_path (str): The path to the file to encrypt.
            output_path (str): The path to save the encrypted file.

        Raises:
            FileNotFoundError: If the input file does not exist.
            IOError: If there's an error reading the input or writing the output file.
        """
        try:
            with open(input_path, 'rb') as f:
                plaintext = f.read()
            
            encrypted_data = self.cipher.encrypt(plaintext)
            
            with open(output_path, 'wb') as f:
                f.write(encrypted_data)
            
            print(f"File '{input_path}' encrypted successfully to '{output_path}'.")

        except FileNotFoundError:
            print(f"Error: Input file not found at '{input_path}'.")
            raise
        except IOError as e:
            print(f"Error during file operation: {e}")
            raise

    def decrypt_file(self, encrypted_path: str, output_path: str) -> bool:
        """
        Decrypts a file and saves it to the specified output path.

        Args:
            encrypted_path (str): The path to the encrypted file.
            output_path (str): The path to save the decrypted file.

        Returns:
            bool: True if decryption is successful, False otherwise.
        """
        try:
            with open(encrypted_path, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.cipher.decrypt(encrypted_data)
            
            with open(output_path, 'wb') as f:
                f.write(decrypted_data)
            
            print(f"File '{encrypted_path}' decrypted successfully to '{output_path}'.")
            return True

        except FileNotFoundError:
            print(f"Error: Encrypted file not found at '{encrypted_path}'.")
            return False
        except InvalidToken:
            print("Error: Decryption failed. The key is incorrect or the data has been tampered with.")
            return False
        except IOError as e:
            print(f"Error during file operation: {e}")
            return False

    def get_key(self) -> bytes:
        """
        Returns the current encryption key.

        Returns:
            bytes: The encryption key.
        """
        return self.key

if __name__ == '__main__':
    # Example Usage
    
    # Create a dummy file to encrypt
    DUMMY_FILE = "test_file.txt"
    ENCRYPTED_FILE = "test_file.enc"
    DECRYPTED_FILE = "decrypted_file.txt"
    
    with open(DUMMY_FILE, "w") as f:
        f.write("This is a secret message for testing purposes.")

    # 1. Initialize the encryptor (will create secret.key on first run)
    encryptor = FileEncryptor(key_path='secret.key')

    # 2. Encrypt the file
    encryptor.encrypt_file(DUMMY_FILE, ENCRYPTED_FILE)

    # 3. Decrypt the file
    if encryptor.decrypt_file(ENCRYPTED_FILE, DECRYPTED_FILE):
        # 4. Verify content
        with open(DECRYPTED_FILE, "r") as f:
            content = f.read()
        print(f"Decrypted content: '{content}'")
        assert content == "This is a secret message for testing purposes."
        print("Round-trip encryption and decryption successful!")

    # Clean up the dummy files
    os.remove(DUMMY_FILE)
    os.remove(ENCRYPTED_FILE)
    os.remove(DECRYPTED_FILE)
    os.remove('secret.key')
    print("Cleaned up test files.")
