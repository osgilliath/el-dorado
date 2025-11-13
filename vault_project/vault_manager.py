
import os
import shutil
from typing import Optional, Dict, Any

from file_encryptor import FileEncryptor
from image_hasher import ImageHasher
from vault_database import VaultDatabase

class VaultManager:
    """
    Orchestrates the entire file encryption, storage, and retrieval process.
    """

    def __init__(self, base_path: str = '.'):
        """
        Initializes the VaultManager and its components.

        Args:
            base_path (str): The base directory of the vault project.
        """
        self.base_path = base_path
        self.encrypted_folder = os.path.join(base_path, 'encrypted')
        self.upload_folder = os.path.join(base_path, 'uploads')
        
        # Ensure directories exist
        os.makedirs(self.encrypted_folder, exist_ok=True)
        os.makedirs(self.upload_folder, exist_ok=True)

        # Initialize components
        self.encryptor = FileEncryptor(key_path=os.path.join(base_path, 'secret.key'))
        self.hasher = ImageHasher()
        self.db = VaultDatabase(db_path=os.path.join(base_path, 'vault.db'))

    def upload_and_encrypt(self, file_path: str) -> Optional[int]:
        """
        Manages the full process of uploading a file to the vault.
        1. Moves file to the upload folder.
        2. Generates cryptographic and perceptual hashes.
        3. Encrypts the file.
        4. Saves encrypted file to the 'encrypted' directory.
        5. Records metadata in the database.
        6. Deletes the original file from the 'uploads' folder.

        Args:
            file_path (str): The path to the file to be uploaded.

        Returns:
            Optional[int]: The ID of the file in the database, or None on failure.
        """
        if not os.path.exists(file_path):
            print(f"Error: Source file not found at '{file_path}'.")
            return None

        original_filename = os.path.basename(file_path)
        temp_path = os.path.join(self.upload_folder, original_filename)

        try:
            # Move file to a temporary processing location
            shutil.copy(file_path, temp_path)

            # 1. Generate Hashes
            crypto_hash = self.hasher.get_cryptographic_hash(temp_path)
            if not crypto_hash:
                raise ValueError("Failed to generate cryptographic hash.")
            
            perceptual_hash = self.hasher.get_perceptual_hash(temp_path) # Can be None

            # 2. Define Encrypted File Path
            encrypted_filename = f"{crypto_hash[:16]}.enc"
            encrypted_path = os.path.join(self.encrypted_folder, encrypted_filename)

            # 3. Encrypt File
            self.encryptor.encrypt_file(temp_path, encrypted_path)

            # 4. Add to Database
            file_id = self.db.add_file(
                filename=original_filename,
                original_hash=crypto_hash,
                perceptual_hash=perceptual_hash,
                encrypted_path=encrypted_path
            )
            
            if file_id is None:
                # This likely means the file hash already exists. Clean up encrypted file.
                os.remove(encrypted_path)
                raise ValueError("File with this content already exists in the vault.")

            print(f"Successfully uploaded and encrypted '{original_filename}' with File ID: {file_id}.")
            return file_id

        except Exception as e:
            print(f"An error occurred during the upload process: {e}")
            return None
        finally:
            # 5. Clean up original file from uploads
            if os.path.exists(temp_path):
                os.remove(temp_path)
                print(f"Cleaned up temporary file: '{temp_path}'")

    def download_and_decrypt(self, file_id: int, output_path: str) -> bool:
        """
        Manages the full process of downloading and decrypting a file from the vault.
        1. Retrieves file metadata from the database.
        2. Decrypts the file to the specified output path.
        3. Verifies the integrity of the decrypted file using its SHA-256 hash.

        Args:
            file_id (int): The database ID of the file to download.
            output_path (str): The path to save the decrypted file.

        Returns:
            bool: True if download, decryption, and verification succeed, False otherwise.
        """
        # 1. Retrieve metadata
        file_info = self.db.get_file(file_id)
        if not file_info:
            print(f"Error: No file found with ID {file_id}.")
            return False

        encrypted_path = file_info['encrypted_path']
        original_hash = file_info['original_hash']
        
        # Ensure the output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        # 2. Decrypt file
        if not self.encryptor.decrypt_file(encrypted_path, output_path):
            print("Decryption failed. Aborting download.")
            return False

        # 3. Verify Integrity
        decrypted_hash = self.hasher.get_cryptographic_hash(output_path)
        if decrypted_hash == original_hash:
            print(f"Integrity check passed. Decrypted file hash matches original.")
            return True
        else:
            print("CRITICAL: Integrity check failed! The decrypted file is corrupt or has been tampered with.")
            # Clean up potentially corrupt file
            os.remove(output_path)
            return False

    def get_file_info(self, file_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieves and returns a file's metadata as a dictionary.

        Args:
            file_id (int): The ID of the.

        Returns:
            Optional[Dict[str, Any]]: A dictionary of the file's metadata or None if not found.
        """
        file_info = self.db.get_file(file_id)
        return dict(file_info) if file_info else None

    def close_db(self):
        """Closes the database connection."""
        self.db.close()

if __name__ == '__main__':
    # Example Usage
    import tempfile
    from PIL import Image

    # Create a temporary directory for the vault project
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"--- Running VaultManager example in temporary directory: {tmpdir} ---")
        
        # 1. Initialize the manager
        vault = VaultManager(base_path=tmpdir)

        # 2. Create a test file
        test_image_path = os.path.join(tmpdir, "my_secret_photo.png")
        Image.new('RGB', (100, 100), color='red').save(test_image_path)

        # 3. Upload and encrypt the file
        print("\n--- Uploading file ---")
        file_id = vault.upload_and_encrypt(test_image_path)
        assert file_id is not None
        print(f"Upload complete. File ID: {file_id}")

        # 4. Get file info
        print("\n--- Retrieving file info ---")
        info = vault.get_file_info(file_id)
        assert info is not None
        print(f"File Info: {info}")
        assert info['filename'] == "my_secret_photo.png"

        # 5. Download and decrypt the file
        print("\n--- Downloading file ---")
        decrypted_path = os.path.join(tmpdir, "downloads", "retrieved_photo.png")
        success = vault.download_and_decrypt(file_id, decrypted_path)
        assert success
        print(f"Download complete. Decrypted file at: {decrypted_path}")

        # 6. Verify the downloaded file is identical to the original
        original_hash = vault.hasher.get_cryptographic_hash(test_image_path)
        decrypted_hash = vault.hasher.get_cryptographic_hash(decrypted_path)
        assert original_hash == decrypted_hash
        print("\nVerification successful: Original and decrypted files are identical.")

        # 7. Attempt to upload the same file again (should fail)
        print("\n--- Attempting to upload duplicate file ---")
        duplicate_id = vault.upload_and_encrypt(test_image_path)
        assert duplicate_id is None
        print("Duplicate upload correctly rejected.")

        # 8. Clean up
        vault.close_db()
        print("\n--- Example finished ---")
