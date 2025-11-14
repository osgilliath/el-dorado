
import sqlite3
import datetime
from typing import List, Optional, Tuple, Any

class VaultDatabase:
    """
    Manages the SQLite database for storing file metadata.
    """

    def __init__(self, db_path: str = 'vault.db'):
        """
        Initializes and connects to the SQLite database.

        Args:
            db_path (str): The path to the SQLite database file.
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        """
        Creates the necessary tables ('files' and 'scan_results') if they don't exist.
        """
        # files table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                original_hash TEXT NOT NULL UNIQUE,
                perceptual_hash TEXT,
                encrypted_path TEXT NOT NULL,
                upload_date TEXT NOT NULL,
                last_scan_date TEXT
            )
        ''')
        
        # scan_results table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS scan_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                found_date TEXT NOT NULL,
                similarity_score INTEGER,
                FOREIGN KEY (file_id) REFERENCES files (id)
            )
        ''')
        self.conn.commit()
        print("Database tables created or already exist.")

    def add_file(self, filename: str, original_hash: str, perceptual_hash: Optional[str], encrypted_path: str) -> Optional[int]:
        """
        Adds a new file record to the database.

        Args:
            filename (str): The original name of the file.
            original_hash (str): The SHA-256 hash of the original file.
            perceptual_hash (Optional[str]): The dHash of the file (if an image).
            encrypted_path (str): The path to the stored encrypted file.

        Returns:
            Optional[int]: The ID of the newly inserted row, or None on failure.
        """
        try:
            upload_date = datetime.datetime.now().isoformat()
            self.cursor.execute('''
                INSERT INTO files (filename, original_hash, perceptual_hash, encrypted_path, upload_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (filename, original_hash, perceptual_hash, encrypted_path, upload_date))
            self.conn.commit()
            print(f"Added file '{filename}' to the database.")
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            print(f"Error: A file with the same original hash '{original_hash}' already exists.")
            return None

    def get_file(self, file_id: int) -> Optional[sqlite3.Row]:
        """
        Retrieves a file's metadata by its primary key ID.

        Args:
            file_id (int): The ID of the file to retrieve.

        Returns:
            Optional[sqlite3.Row]: A Row object with the file's metadata, or None if not found.
        """
        self.cursor.execute('SELECT * FROM files WHERE id = ?', (file_id,))
        return self.cursor.fetchone()

    def get_all_files(self) -> List[sqlite3.Row]:
        """
        Retrieves metadata for all files in the database.

        Returns:
            List[sqlite3.Row]: A list of Row objects, each containing a file's metadata.
        """
        self.cursor.execute('SELECT * FROM files ORDER BY upload_date DESC')
        return self.cursor.fetchall()

    def update_last_scan(self, file_id: int, scan_date: Optional[datetime.datetime] = None):
        """
        Updates the last_scan_date for a specific file.

        Args:
            file_id (int): The ID of the file to update.
            scan_date (Optional[datetime.datetime]): The timestamp of the scan. Defaults to now.
        """
        if scan_date is None:
            scan_date = datetime.datetime.now()
        
        self.cursor.execute('UPDATE files SET last_scan_date = ? WHERE id = ?', (scan_date.isoformat(), file_id))
        self.conn.commit()
        print(f"Updated last scan date for file ID {file_id}.")

    def add_scan_result(self, file_id: int, url: str, similarity_score: int) -> int:
        """
        Records a new scan result, indicating a potential leak was found.

        Args:
            file_id (int): The ID of the file that was found.
            url (str): The URL where the similar file was found.
            similarity_score (int): The Hamming distance between the file and the found image.

        Returns:
            int: The ID of the newly inserted scan result.
        """
        found_date = datetime.datetime.now().isoformat()
        self.cursor.execute('''
            INSERT INTO scan_results (file_id, url, found_date, similarity_score)
            VALUES (?, ?, ?, ?)
        ''', (file_id, url, found_date, similarity_score))
        self.conn.commit()
        print(f"Added scan result for file ID {file_id} found at {url}.")
        return self.cursor.lastrowid

    def close(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()
            print("Database connection closed.")

if __name__ == '__main__':
    import os
    DB_FILE = 'test_vault.db'
    
    # 1. Initialize database
    db = VaultDatabase(db_path=DB_FILE)

    # 2. Add a file record
    file_id = db.add_file(
        filename='my_photo.jpg',
        original_hash='a1b2c3d4e5f6...',
        perceptual_hash='f0e1d2c3b4a5...',
        encrypted_path='encrypted/a1b2c3d4e5f6.enc'
    )
    assert file_id is not None

    # Try adding a duplicate
    duplicate_id = db.add_file("duplicate.jpg", "a1b2c3d4e5f6...", "...", "...")
    assert duplicate_id is None

    # 3. Retrieve the file record
    retrieved_file = db.get_file(file_id)
    print(f"Retrieved file: {dict(retrieved_file)}")
    assert retrieved_file is not None
    assert retrieved_file['filename'] == 'my_photo.jpg'

    # 4. Update scan date
    db.update_last_scan(file_id)
    retrieved_file_after_scan = db.get_file(file_id)
    print(f"File after scan update: {dict(retrieved_file_after_scan)}")
    assert retrieved_file_after_scan['last_scan_date'] is not None

    # 5. Add a scan result
    scan_id = db.add_scan_result(
        file_id=file_id,
        url='http://example.com/leak.jpg',
        similarity_score=3
    )
    assert scan_id is not None

    # 6. Get all files
    all_files = db.get_all_files()
    print(f"Total files in DB: {len(all_files)}")
    assert len(all_files) == 1

    # 7. Close connection and clean up
    db.close()
    os.remove(DB_FILE)
    print("Cleaned up test database.")
