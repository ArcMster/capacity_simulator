import React, { useState } from 'react';
import axios from 'axios';
import { Upload as UploadIcon, FileText, CheckCircle, AlertCircle, Loader, ArrowLeft } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

const Upload = () => {
    const navigate = useNavigate();
    const [file, setFile] = useState(null);
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState([]);
    const [error, setError] = useState(null);

    const handleFileChange = (e) => {
        setFile(e.target.files[0]);
        setError(null);
        setResults([]);
    };

    const handleUpload = async (e) => {
        e.preventDefault();
        if (!file) {
            setError("Please select a file first.");
            return;
        }

        // Clear previous state
        setError(null);
        setResults([]);
        setLoading(true);

        const formData = new FormData();
        formData.append('schedule_file', file);

        try {
            const response = await axios.post('http://localhost:8000/api/upload/', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            setResults(response.data.results);
        } catch (err) {
            setError(err.response?.data?.error || "An error occurred while uploading.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="container" style={{ maxWidth: '800px' }}>

            <div className="card">
                <h2 style={{ color: 'var(--primary-color)', marginTop: 0 }}>Import Vessel Schedule</h2>
                <p style={{ color: 'var(--text-muted)', marginBottom: '32px' }}>
                    Upload a vessel schedule (Image or PDF) to automatically parse and import the data.
                </p>

                <form onSubmit={handleUpload}>
                    <div style={{
                        border: '2px dashed var(--border-color)',
                        borderRadius: '12px',
                        padding: '40px',
                        textAlign: 'center',
                        marginBottom: '24px',
                        background: '#f9fafb'
                    }}>
                        <input
                            type="file"
                            id="file-upload"
                            onChange={handleFileChange}
                            style={{ display: 'none' }}
                            accept="image/*,application/pdf"
                        />
                        <label htmlFor="file-upload" style={{ cursor: 'pointer' }}>
                            <UploadIcon size={48} color="var(--text-muted)" style={{ marginBottom: '16px' }} />
                            <div style={{ fontWeight: '600', marginBottom: '4px' }}>
                                {file ? file.name : 'Click to select or drag and drop'}
                            </div>
                            <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>PNG, JPG, PDF up to 10MB</div>
                        </label>
                    </div>

                    <button
                        type="submit"
                        disabled={loading || !file}
                        style={{
                            width: '100%',
                            background: 'var(--primary-color)',
                            color: 'white',
                            padding: '12px',
                            borderRadius: '8px',
                            border: 'none',
                            fontWeight: '600',
                            cursor: (loading || !file) ? 'not-allowed' : 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center'
                        }}
                    >
                        {loading ? <Loader className="animate-spin" style={{ marginRight: '8px' }} /> : <FileText style={{ marginRight: '8px' }} />}
                        {loading ? 'Processing...' : 'Upload and Process'}
                    </button>
                </form>

                {error && (
                    <div style={{ marginTop: '24px', padding: '16px', background: '#fee2e2', color: '#b91c1c', borderRadius: '8px', display: 'flex', alignItems: 'center', fontSize: '14px' }}>
                        <AlertCircle style={{ minWidth: '20px', marginRight: '12px' }} />
                        <div style={{ overflowWrap: 'anywhere' }}>{error}</div>
                    </div>
                )}

                {results.length > 0 && (
                    <div style={{ marginTop: '24px' }}>
                        <h3 style={{ fontSize: '16px', marginBottom: '12px' }}>Processing Results:</h3>
                        <div style={{ maxHeight: '300px', overflowY: 'auto', marginBottom: '24px', border: '1px solid var(--border-color)', borderRadius: '8px' }}>
                            {results.map((res, i) => (
                                <div key={i} style={{ padding: '12px', borderBottom: i === results.length - 1 ? 'none' : '1px solid var(--border-color)', fontSize: '14px', display: 'flex', alignItems: 'start' }}>
                                    <CheckCircle size={16} color="var(--success-color)" style={{ marginTop: '3px', marginRight: '8px', minWidth: '16px' }} />
                                    {res}
                                </div>
                            ))}
                        </div>

                        <button
                            onClick={() => navigate('/search')}
                            style={{
                                width: '100%',
                                background: 'white',
                                border: '2px solid var(--primary-color)',
                                color: 'var(--primary-color)',
                                padding: '12px',
                                borderRadius: '8px',
                                fontWeight: '700',
                                cursor: 'pointer'
                            }}
                        >
                            Done - View Updated Schedules
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Upload;
