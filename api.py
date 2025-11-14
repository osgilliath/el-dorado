
import os
import tempfile
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from vault_manager import VaultManager

app = Flask(__name__)
CORS(app)

# Configuration
VAULT_BASE_PATH = 'my_secure_vault'
UPLOAD_FOLDER = os.path.join(VAULT_BASE_PATH, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize VaultManager
vault_manager = VaultManager(base_path=VAULT_BASE_PATH)

@app.route('/api/files', methods=['GET'])
def get_files():
    """Returns a list of all files in the vault."""
    files = vault_manager.db.get_all_files()
    return jsonify([dict(file) for file in files])

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Uploads a new file to the vault."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file:
        filename = secure_filename(file.filename)
        # Use a temporary file to store the upload
        with tempfile.NamedTemporaryFile(delete=False, suffix=filename) as temp_file:
            file.save(temp_file.name)
            temp_path = temp_file.name

        file_id = None
        try:
            file_id = vault_manager.upload_and_encrypt(temp_path)
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)

        if file_id:
            return jsonify({'message': 'File uploaded successfully', 'file_id': file_id})
        else:
            # The file might already exist or an error occurred.
            return jsonify({'error': 'Failed to upload file. It may already exist.'}), 409


@app.route('/api/files/<int:file_id>', methods=['GET'])
def download_file(file_id):
    """Downloads a decrypted file from the vault."""
    # Create a temporary directory for the decrypted file
    temp_dir = os.path.join(app.root_path, 'temp_decrypted')
    os.makedirs(temp_dir, exist_ok=True)
    
    file_info = vault_manager.get_file_info(file_id)
    if not file_info:
        return jsonify({'error': 'File not found'}), 404

    output_path = os.path.join(temp_dir, file_info['filename'])
    
    if vault_manager.download_and_decrypt(file_id, output_path):
        return send_from_directory(temp_dir, file_info['filename'], as_attachment=True)
    else:
        return jsonify({'error': 'Failed to decrypt file'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
