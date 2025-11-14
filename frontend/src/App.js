import React, { useState, useEffect } from 'react';
import { getFiles, uploadFile, downloadFile } from './api';
import 'bootstrap/dist/css/bootstrap.min.css';
import { Modal, Button } from 'react-bootstrap';
import PinInput from './PinInput';
import './PinInput.css';

function App() {
  const [files, setFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [pinEntered, setPinEntered] = useState(false);
  const [searchResults, setSearchResults] = useState(null);

  useEffect(() => {
    if (pinEntered) {
      fetchFiles();
    }
  }, [pinEntered]);

  const fetchFiles = async () => {
    try {
      const response = await getFiles();
      setFiles(response.data);
    } catch (error) {
      console.error('Error fetching files:', error);
      setError('Failed to fetch files. Is the backend server running?');
    }
  };

  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a file to upload.');
      return;
    }
    setUploading(true);
    setError(null);
    try {
      const response = await uploadFile(selectedFile);
      fetchFiles(); // Refresh file list
      setSelectedFile(null);
      setSearchResults(response.search_results);
    } catch (error) {
      console.error('Error uploading file:', error);
      if (error.response && error.response.status === 409) {
        setError('Failed to upload file. It may already exist in the vault.');
      } else {
        setError('Failed to upload file. Please try again.');
      }
    } finally {
      setUploading(false);
    }
  };

  const handleDownload = async (fileId, filename) => {
    try {
      const response = await downloadFile(fileId);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
    } catch (error) {
      console.error('Error downloading file:', error);
      setError('Failed to download file.');
    }
  };

  const handlePinEntered = () => {
    setPinEntered(true);
  };

  const handleCloseSearchResults = () => {
    setSearchResults(null);
  };

  return (
    <div className="container mt-5">
      {!pinEntered ? (
        <PinInput onPinEntered={handlePinEntered} />
      ) : (
        <div>
          <h1 className="mb-4">My Secure Vault</h1>

          {error && <div className="alert alert-danger">{error}</div>}

          <div className="card mb-4">
            <div className="card-body">
              <h5 className="card-title">Upload New File</h5>
              <div className="input-group">
                <input type="file" className="form-control" onChange={handleFileChange} />
                <button className="btn btn-primary" onClick={handleUpload} disabled={uploading}>
                  {uploading ? 'Uploading...' : 'Upload'}
                </button>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              Vault Files
            </div>
            <ul className="list-group list-group-flush">
              {files.length === 0 ? (
                <li className="list-group-item">No files in the vault.</li>
              ) : (
                files.map((file) => (
                  <li key={file.id} className="list-group-item d-flex justify-content-between align-items-center">
                    {file.filename}
                    <button className="btn btn-success btn-sm" onClick={() => handleDownload(file.id, file.filename)}>
                      Download
                    </button>
                  </li>
                ))
              )}
            </ul>
          </div>
        </div>
      )}

      <Modal show={searchResults !== null} onHide={handleCloseSearchResults}>
        <Modal.Header closeButton>
          <Modal.Title>Reverse Image Search Results</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {searchResults && searchResults.image_results && (
            <ul>
              {searchResults.image_results.map((result, index) => (
                <li key={index}>
                  <a href={result.link} target="_blank" rel="noopener noreferrer">
                    {result.title}
                  </a>
                </li>
              ))}
            </ul>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={handleCloseSearchResults}>
            Close
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
}

export default App;