import os
import shutil
import platform
import subprocess
import tempfile
import tkinter as tk
from tkinter import filedialog

from vault_manager import VaultManager

def open_file(path: str):
    """Opens a file with its default application in a cross-platform way."""
    try:
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", path], check=True)
        else:  # Linux and other Unix-like systems
            subprocess.run(["xdg-open", path], check=True)
    except Exception as e:
        print(f"Error: Could not open the file '{path}'.")
        print(f"Reason: {e}")

def handle_upload(vault: VaultManager):
    """Handles the file upload process with a fallback for the file dialog."""
    
    file_path = ""
    method = input("How would you like to select a file?\n1. Open file dialog\n2. Paste file path directly\nEnter choice (1 or 2): ")

    if method == '1':
        try:
            print("Opening file dialog...")
            root = tk.Tk()
            root.withdraw()
            # Force the window to the top and update before opening the dialog
            root.attributes('-topmost', True)
            root.update()
            file_path = filedialog.askopenfilename(title="Select a file to upload to the vault")
            root.destroy()
        except tk.TclError as e:
            print("\n❌ Could not open file dialog. This may be because you are not in a graphical environment.")
            print("Please try pasting the file path directly next time.")
            return
    elif method == '2':
        file_path = input("Please paste the full path to the file and press Enter: ")
    else:
        print("Invalid choice. Returning to main menu.")
        return

    if not file_path or not os.path.exists(file_path):
        print("No file selected or path does not exist. Returning to main menu.")
        return

    print(f"Selected file: {file_path}")
    file_id = vault.upload_and_encrypt(file_path)
    
    if file_id:
        print(f"\n✅ Success! File '{os.path.basename(file_path)}' was securely added to the vault with ID: {file_id}")
    else:
        print("\n❌ Failure! The file could not be added to the vault. It may already exist.")

def handle_access(vault: VaultManager):
    """Handles the vault access and file viewing process."""
    special_key = input("Enter the special key to access the vault: ")
    if not special_key:
        print("No key entered. Access denied.")
        return
    
    print("Accessing vault...")
    files = vault.db.get_all_files()
    
    if not files:
        print("The vault is currently empty.")
        return

    print("\n--- Files in Vault ---")
    for i, file_row in enumerate(files):
        print(f"{i + 1}. {file_row['filename']}")
    print("--------------------")

    try:
        selection = int(input(f"Enter the number of the file to open (1-{len(files)}): "))
        if not 1 <= selection <= len(files):
            print("Invalid selection.")
            return
    except ValueError:
        print("Invalid input. Please enter a number.")
        return

    selected_file = dict(files[selection - 1])

    # Create a temporary directory to hold the decrypted file
    with tempfile.TemporaryDirectory() as tmpdir:
        decrypted_path = os.path.join(tmpdir, selected_file['filename'])
        
        print(f"\nDecrypting '{selected_file['filename']}' to a temporary location for viewing...")
        success = vault.download_and_decrypt(selected_file['id'], decrypted_path)
        
        if success:
            print(f"  > Opening '{selected_file['filename']}'...")
            open_file(decrypted_path)
            input("  > Press Enter to close the temporary file and return to the main menu...")
        else:
            print(f"  > Failed to decrypt '{selected_file['filename']}'.")
    
    print("Temporary file has been securely deleted.")

def main():
    """
    Main function to run the interactive vault application.
    """
    # Use a persistent directory for the vault
    VAULT_DIR = "vault_project/my_secure_vault"
    print(f"--- Secure Vault Application ---")
    print(f"Using vault directory: '{VAULT_DIR}'")

    # Initialize the VaultManager
    vault = VaultManager(base_path=VAULT_DIR)
    
    while True:
        print("\n" + "="*30)
        print("Main Menu")
        print("1. Upload a file to the vault")
        print("2. Access and view files in the vault")
        print("3. Exit")
        print("="*30)
        
        choice = input("Enter your choice (1, 2, or 3): ")
        
        if choice == '1':
            handle_upload(vault)
        elif choice == '2':
            handle_access(vault)
        elif choice == '3':
            print("Exiting the application. Goodbye!")
            vault.close_db()
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

if __name__ == '__main__':
    main()