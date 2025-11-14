
import hashlib
import imagehash
from PIL import Image
from typing import Optional

class ImageHasher:
    """
    Handles the generation of perceptual and cryptographic hashes for files.
    - Perceptual hash (dHash) for image similarity.
    - Cryptographic hash (SHA-256) for file integrity.
    """

    def get_perceptual_hash(self, image_path: str) -> Optional[str]:
        """
        Generates a perceptual hash (dHash) for an image file.

        Args:
            image_path (str): The path to the image file.

        Returns:
            Optional[str]: The hexadecimal representation of the dHash, 
                           or None if the file is not a valid image.
        """
        try:
            with Image.open(image_path) as img:
                # Convert to grayscale for consistent hashing
                hash_val = imagehash.dhash(img.convert('L'))
            return str(hash_val)
        except FileNotFoundError:
            print(f"Error: Image file not found at '{image_path}'.")
            return None
        except Exception as e:
            # Pillow will raise an exception for non-image files
            print(f"Could not generate perceptual hash for '{image_path}': {e}")
            return None

    def get_cryptographic_hash(self, file_path: str) -> Optional[str]:
        """
        Generates a cryptographic hash (SHA-256) for any file.
        Reads the file in chunks to handle large files efficiently.

        Args:
            file_path (str): The path to the file.

        Returns:
            Optional[str]: The hexadecimal representation of the SHA-256 hash,
                           or None if the file is not found.
        """
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                # Read and update hash in chunks of 4K
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except FileNotFoundError:
            print(f"Error: File not found at '{file_path}'.")
            return None
        except IOError as e:
            print(f"Error reading file '{file_path}': {e}")
            return None

    def compare_hashes(self, hash1: str, hash2: str) -> int:
        """
        Calculates the Hamming distance between two perceptual hashes.

        Args:
            hash1 (str): The first perceptual hash (hex string).
            hash2 (str): The second perceptual hash (hex string).

        Returns:
            int: The Hamming distance (number of differing bits).
        """
        h1 = imagehash.hex_to_hash(hash1)
        h2 = imagehash.hex_to_hash(hash2)
        return h1 - h2

    def is_match(self, hash1: str, hash2: str, threshold: int = 5) -> bool:
        """
        Determines if two perceptual hashes are a match based on a threshold.

        Args:
            hash1 (str): The first perceptual hash (hex string).
            hash2 (str): The second perceptual hash (hex string).
            threshold (int): The maximum allowed Hamming distance for a match.

        Returns:
            bool: True if the Hamming distance is within the threshold, False otherwise.
        """
        return self.compare_hashes(hash1, hash2) <= threshold

if __name__ == '__main__':
    import os
    # Example Usage
    hasher = ImageHasher()

    # Create a dummy image file for testing
    try:
        from PIL import Image, ImageDraw
        
        def create_test_image(path, text):
            img = Image.new('RGB', (200, 100), color = (73, 109, 137))
            d = ImageDraw.Draw(img)
            d.text((10,10), text, fill=(255,255,0))
            img.save(path)

        IMAGE1_PATH = "test_image1.png"
        IMAGE2_PATH = "test_image2.png" # Slightly different
        IMAGE3_PATH = "test_image3.jpg" # Different format, same content
        TEXT_FILE = "not_an_image.txt"

        create_test_image(IMAGE1_PATH, "Hello")
        create_test_image(IMAGE2_PATH, "Hallo") # Small change
        create_test_image(IMAGE3_PATH, "Hello")

        with open(TEXT_FILE, "w") as f:
            f.write("This is not an image.")

        # 1. Test Perceptual Hashing
        p_hash1 = hasher.get_perceptual_hash(IMAGE1_PATH)
        p_hash2 = hasher.get_perceptual_hash(IMAGE2_PATH)
        p_hash3 = hasher.get_perceptual_hash(IMAGE3_PATH)
        p_hash_fail = hasher.get_perceptual_hash(TEXT_FILE)

        print(f"Perceptual Hash 1 (Original): {p_hash1}")
        print(f"Perceptual Hash 2 (Similar): {p_hash2}")
        print(f"Perceptual Hash 3 (Same): {p_hash3}")
        print(f"Perceptual Hash (Non-image): {p_hash_fail}")

        assert p_hash1 is not None and p_hash2 is not None and p_hash3 is not None
        assert p_hash_fail is None
        assert p_hash1 == p_hash3 # Same content should have same hash

        # 2. Test Hash Comparison
        distance_similar = hasher.compare_hashes(p_hash1, p_hash2)
        distance_same = hasher.compare_hashes(p_hash1, p_hash3)
        print(f"Hamming distance between original and similar image: {distance_similar}")
        print(f"Hamming distance between original and same image: {distance_same}")

        assert hasher.is_match(p_hash1, p_hash2, threshold=5) == True
        assert distance_same == 0

        # 3. Test Cryptographic Hashing
        c_hash1 = hasher.get_cryptographic_hash(IMAGE1_PATH)
        c_hash2 = hasher.get_cryptographic_hash(IMAGE2_PATH)
        c_hash3 = hasher.get_cryptographic_hash(IMAGE3_PATH)
        c_hash_text = hasher.get_cryptographic_hash(TEXT_FILE)

        print(f"Cryptographic Hash 1: {c_hash1}")
        print(f"Cryptographic Hash 2: {c_hash2}")
        print(f"Cryptographic Hash 3: {c_hash3}")
        print(f"Cryptographic Hash Text: {c_hash_text}")

        assert c_hash1 != c_hash2 # Different content, different hash
        assert c_hash1 != c_hash3 # Different file format, different hash
        assert c_hash1 is not None and c_hash_text is not None

        # Clean up
        os.remove(IMAGE1_PATH)
        os.remove(IMAGE2_PATH)
        os.remove(IMAGE3_PATH)
        os.remove(TEXT_FILE)
        print("Cleaned up test files.")

    except ImportError:
        print("Pillow is not installed. Skipping ImageHasher example.")
    except Exception as e:
        print(f"An error occurred during example execution: {e}")

