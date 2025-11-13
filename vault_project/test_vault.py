
import unittest
import os
import shutil
import sqlite3
from PIL import Image, ImageDraw

# Add project root to path to allow imports
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from file_encryptor import FileEncryptor
from image_hasher import ImageHasher
from vault_database import VaultDatabase
from vault_manager import VaultManager

class TestVaultSystem(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """Set up a temporary directory and test files for all tests."""
        cls.test_dir = "test_vault_workspace"
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir)
        os.makedirs(cls.test_dir)
        
        # Create test images with content to ensure valid perceptual hashes
        cls.image1_path = os.path.join(cls.test_dir, "image1.png")
        cls.image2_path = os.path.join(cls.test_dir, "image2.png")
        cls.text_path = os.path.join(cls.test_dir, "document.txt")
        
        def create_image(path, text, color):
            img = Image.new('RGB', (100, 100), color=color)
            d = ImageDraw.Draw(img)
            d.text((10, 10), text, fill='white')
            img.save(path)

        create_image(cls.image1_path, "Test 1", "red")
        create_image(cls.image2_path, "Test 2", "blue")
        
        with open(cls.text_path, "w") as f:
            f.write("This is a test document.")

    @classmethod
    def tearDownClass(cls):
        """Clean up the temporary directory after all tests."""
        shutil.rmtree(cls.test_dir)

    def setUp(self):
        """Set up a fresh vault instance for each test."""
        self.vault_path = os.path.join(self.test_dir, "vault")
        os.makedirs(self.vault_path, exist_ok=True)
        self.manager = VaultManager(base_path=self.vault_path)

    def tearDown(self):
        """Clean up the vault instance directory after each test."""
        self.manager.close_db()
        shutil.rmtree(self.vault_path)

    def test_01_file_encryptor(self):
        """Test the FileEncryptor class for a full encryption-decryption round trip."""
        encryptor = self.manager.encryptor
        encrypted_file = os.path.join(self.vault_path, "text.enc")
        decrypted_file = os.path.join(self.vault_path, "text.dec")
        
        encryptor.encrypt_file(self.text_path, encrypted_file)
        self.assertTrue(os.path.exists(encrypted_file))
        
        success = encryptor.decrypt_file(encrypted_file, decrypted_file)
        self.assertTrue(success)
        
        with open(self.text_path, "r") as f1, open(decrypted_file, "r") as f2:
            self.assertEqual(f1.read(), f2.read())

    def test_02_image_hasher(self):
        """Test the ImageHasher for both cryptographic and perceptual hashes."""
        hasher = self.manager.hasher
        
        # Test cryptographic hash
        crypto_hash1 = hasher.get_cryptographic_hash(self.image1_path)
        crypto_hash2 = hasher.get_cryptographic_hash(self.image2_path)
        self.assertIsNotNone(crypto_hash1)
        self.assertIsNotNone(crypto_hash2)
        self.assertNotEqual(crypto_hash1, crypto_hash2)
        
        # Test perceptual hash
        p_hash1 = hasher.get_perceptual_hash(self.image1_path)
        p_hash2 = hasher.get_perceptual_hash(self.image2_path)
        self.assertIsNotNone(p_hash1)
        self.assertIsNotNone(p_hash2)
        self.assertNotEqual(p_hash1, p_hash2)
        
        # Test comparison
        distance = hasher.compare_hashes(p_hash1, p_hash2)
        self.assertGreater(distance, 0)

    def test_03_vault_database(self):
        """Test the VaultDatabase for CRUD operations."""
        db = self.manager.db
        
        # Add a file
        file_id = db.add_file("test.jpg", "hash123", "phash456", "/path/to/file.enc")
        self.assertIsNotNone(file_id)
        
        # Get the file
        retrieved = db.get_file(file_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved['filename'], "test.jpg")
        
        # Add a duplicate (should fail)
        duplicate_id = db.add_file("test2.jpg", "hash123", "phash789", "/path/to/file2.enc")
        self.assertIsNone(duplicate_id)
        
        # Get all files
        all_files = db.get_all_files()
        self.assertEqual(len(all_files), 1)

    def test_04_vault_manager_full_cycle(self):
        """Test the VaultManager for a complete upload and download cycle."""
        # Upload
        file_id = self.manager.upload_and_encrypt(self.image1_path)
        self.assertIsNotNone(file_id)
        
        # Verify upload
        info = self.manager.get_file_info(file_id)
        self.assertIsNotNone(info)
        self.assertTrue(os.path.exists(info['encrypted_path']))
        
        # Download
        download_path = os.path.join(self.test_dir, "downloaded_image.png")
        success = self.manager.download_and_decrypt(file_id, download_path)
        self.assertTrue(success)
        
        # Verify integrity
        original_hash = self.manager.hasher.get_cryptographic_hash(self.image1_path)
        downloaded_hash = self.manager.hasher.get_cryptographic_hash(download_path)
        self.assertEqual(original_hash, downloaded_hash)

    def test_05_duplicate_upload_rejection(self):
        """Test that the VaultManager rejects duplicate file uploads."""
        # First upload should succeed
        file_id1 = self.manager.upload_and_encrypt(self.text_path)
        self.assertIsNotNone(file_id1)
        
        # Second upload of the same file should fail
        file_id2 = self.manager.upload_and_encrypt(self.text_path)
        self.assertIsNone(file_id2)

if __name__ == '__main__':
    unittest.main(verbosity=2)
