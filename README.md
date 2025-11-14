
# Secure Vault System

This project provides a production-ready system for securely encrypting, storing, and managing sensitive files. It uses strong cryptography, perceptual and cryptographic hashing, and a robust database system to ensure data integrity and confidentiality.

## Features

- **Strong Encryption:** Files are encrypted using Fernet (AES-128-CBC with a 128-bit IV and HMAC-SHA256 authentication).
- **Secure Key Management:** A 256-bit secret key is generated on the first run and stored in a permissions-restricted `secret.key` file.
- **Dual Hashing System:**
    - **SHA-256:** For cryptographic integrity verification, ensuring files are not corrupted or tampered with.
    - **Perceptual Hash (dHash):** For identifying similar images, enabling detection of modified or resized copies.
- **Database Storage:** A SQLite database (`vault.db`) stores all file metadata, including hashes, original filenames, and storage paths.
- **Secure File Naming:** Encrypted files are named using the first 16 characters of their SHA-256 hash, preventing information leakage from filenames.
- **Orchestrated Workflow:** The `VaultManager` class provides a simple interface for complex upload and download operations, including hash verification and cleanup.

## Project Structure

```
vault_project/
├── encrypted/              # Storage for encrypted .enc files
├── uploads/                # Temporary folder for file processing
├── vault_demo/             # Directory for the main.py demonstration
├── secret.key              # Auto-generated secret encryption key
├── vault.db                # Auto-generated SQLite database
├── file_encryptor.py       # Handles encryption/decryption
├── image_hasher.py         # Handles hash generation
├── vault_database.py       # Manages the SQLite database
├── vault_manager.py        # Orchestrates all operations
├── main.py                 # Example usage script
├── test_vault.py           # Unit tests for the system
└── requirements.txt        # Python dependencies
```

## How to Run

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the Demonstration:**
    The `main.py` script provides a comprehensive demonstration of all features. It will create a `vault_demo` directory to run in, so it won't interfere with any existing vault data.
    ```bash
    python main.py
    ```

3.  **Run the Unit Tests:**
    To ensure all components are working correctly, you can run the built-in unit tests.
    ```bash
    python test_vault.py
    ```

## Security Notes and Limitations

-   **Key Security is Critical:** The entire security of this system rests on the `secret.key` file. **Anyone with access to this key can decrypt all files.** It is imperative to protect this key file. Never commit it to version control (add it to `.gitignore`). In a production environment, this key should be managed by a dedicated secrets management service (like HashiCorp Vault, AWS KMS, or Azure Key Vault).
-   **Database Security:** The `vault.db` file contains metadata that could be sensitive (e.g., original filenames). Ensure this file is also protected with appropriate file system permissions.
-   **Perceptual Hash Collisions:** Perceptual hashes are not unique. While unlikely for distinct images, it is possible for two different images to have the same or a very similar dHash. They should only be used for similarity searching, not for unique identification.
-   **No User Authentication:** This system is a file-handling backend. It does not include any concept of user accounts, access control lists (ACLs), or multi-user separation. A wrapping application would be needed to implement such features.
-   **Replay Attacks:** Fernet tokens include a timestamp to mitigate replay attacks, but this is only effective within a limited time-to-live (TTL). The default TTL is 60 seconds. For this application, where tokens are stored long-term, the primary defense against tampering is the HMAC signature, which is verified upon every decryption.

## Production Deployment Recommendations

1.  **Key Management:**
    -   **DO NOT** store the `secret.key` file directly on the application server's filesystem in a production environment.
    -   **DO** use a secure secrets management service (e.g., AWS Secrets Manager, HashiCorp Vault). The application should fetch the key from this service at startup. This prevents the key from being exposed if the server's disk is compromised.

2.  **File Storage:**
    -   Local filesystem storage (`encrypted/` folder) is suitable for single-server deployments.
    -   For scalable or distributed systems, use a cloud object storage service like **Amazon S3**, **Google Cloud Storage**, or **Azure Blob Storage**. The `encrypted_path` in the database would then become the object key or URL. Ensure the storage bucket is private and accessible only by the application's service account.

3.  **Database:**
    -   SQLite is excellent for single-node applications or embedded use cases.
    -   For applications requiring high concurrency, scalability, or replication, migrate to a dedicated database server like **PostgreSQL** or **MySQL**. The `VaultDatabase` class can be adapted to use a different database driver (e.g., `psycopg2`).

4.  **Application Architecture:**
    -   This vault system should be exposed as a service, likely via a secure REST API (e.g., using FastAPI or Flask).
    -   The API endpoints would handle user authentication and authorization before calling the `VaultManager` methods.
    -   Implement robust logging and monitoring to track access patterns and potential security events.

5.  **Permissions:**
    -   Run the application with a dedicated, low-privilege user account.
    -   Ensure the application process only has read/write access to the directories it absolutely needs.
    -   Set file permissions for all application code and data to be as restrictive as possible.