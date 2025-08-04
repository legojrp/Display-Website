import React, { useState, useEffect, useRef, useCallback } from 'react';

// Custom styles for full-screen display
const fullScreenStyle = {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: '#000000',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    fontFamily: '"Segoe UI", Roboto, -apple-system, BlinkMacSystemFont, sans-serif',
    overflow: 'hidden',
};

const imageStyle = {
    maxWidth: '100vw',
    maxHeight: '100vh',
    objectFit: 'contain',
    borderRadius: '8px',
    boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
    transition: 'opacity 0.5s ease-in-out',
};

const uploadOverlayStyle = {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.9)',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000,
    backdropFilter: 'blur(10px)',
};

const uploadAreaStyle = {
    width: '500px',
    maxWidth: '90vw',
    padding: '40px',
    border: '2px dashed #667eea',
    borderRadius: '12px',
    textAlign: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    color: '#ffffff',
    transition: 'all 0.3s ease',
};

const uploadAreaActiveStyle = {
    ...uploadAreaStyle,
    borderColor: '#4CAF50',
    backgroundColor: 'rgba(76, 175, 80, 0.1)',
};

const statusStyle = {
    position: 'absolute',
    bottom: '30px',
    right: '30px',
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    color: '#e0e0e0',
    padding: '15px 20px',
    borderRadius: '12px',
    zIndex: 999,
    fontSize: '14px',
    fontWeight: '300',
    border: '1px solid rgba(255,255,255,0.1)',
    backdropFilter: 'blur(15px)',
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
    minWidth: '180px',
};

const controlsStyle = {
    position: 'absolute',
    top: '30px',
    right: '30px',
    display: 'flex',
    gap: '10px',
    zIndex: 999,
};

const buttonStyle = {
    padding: '12px 16px',
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    color: '#ffffff',
    border: '1px solid rgba(255,255,255,0.2)',
    borderRadius: '8px',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: '500',
    backdropFilter: 'blur(15px)',
    transition: 'all 0.3s ease',
};

const progressBarStyle = {
    position: 'absolute',
    bottom: '0',
    left: '0',
    right: '0',
    height: '3px',
    backgroundColor: 'rgba(255,255,255,0.1)',
};

const progressFillStyle = {
    height: '100%',
    backgroundColor: '#667eea',
    transition: 'width 0.1s linear',
    borderRadius: '2px',
};

const pictureInfoStyle = {
    position: 'absolute',
    bottom: '100px',
    left: '30px',
    right: '30px',
    textAlign: 'center',
    color: '#ffffff',
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    padding: '20px',
    borderRadius: '12px',
    backdropFilter: 'blur(15px)',
    border: '1px solid rgba(255,255,255,0.1)',
};

const Pictures = ({ theme }) => {
    const [pictures, setPictures] = useState([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [lastUpdate, setLastUpdate] = useState('');
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(true);
    const [progress, setProgress] = useState(0);
    const [isVisible, setIsVisible] = useState(true);
    const [showUpload, setShowUpload] = useState(false);
    const [isDragging, setIsDragging] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [uploadProgress, setUploadProgress] = useState([]);
    const [actionFeedback, setActionFeedback] = useState('');
    const fileInputRef = useRef(null);

    // Function to fetch pictures data
    const fetchPictures = async () => {
        try {
            setLoading(true);
            const response = await fetch(`${process.env.REACT_APP_SERVER_URL}/pictures/get_pictures?limit=100`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success && Array.isArray(data.pictures) && data.pictures.length > 0) {
                // Filter only visible pictures (show_picture = 1)
                const visiblePictures = data.pictures.filter(pic => pic.show_picture === 1);
                setPictures(visiblePictures);
                setCurrentIndex(0);
                setLastUpdate(new Date().toLocaleString());
                setError(null);
            } else {
                throw new Error('No pictures available');
            }
        } catch (err) {
            console.error('Error fetching pictures:', err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    // Function to upload pictures
    const uploadPictures = async (files) => {
        setUploading(true);
        const uploadResults = [];
        const progressArray = new Array(files.length).fill(0);
        setUploadProgress(progressArray);

        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            try {
                // Convert file to base64
                const base64 = await new Promise((resolve, reject) => {
                    const reader = new FileReader();
                    reader.onload = () => resolve(reader.result);
                    reader.onerror = reject;
                    reader.readAsDataURL(file);
                });

                // Update progress
                progressArray[i] = 50;
                setUploadProgress([...progressArray]);

                // Upload to server
                const response = await fetch(`${process.env.REACT_APP_SERVER_URL}/pictures/upload_picture`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        picture: base64,
                        title: file.name.split('.')[0],
                        description: `Uploaded on ${new Date().toLocaleDateString()}`
                    })
                });

                if (!response.ok) {
                    throw new Error(`Upload failed for ${file.name}`);
                }

                const result = await response.json();
                
                // Check if the server returned an error even with 200 status
                if (result.success === false) {
                    throw new Error(result.error || `Upload failed for ${file.name}`);
                }
                
                uploadResults.push({ file: file.name, success: true, result });
                
                // Complete progress for this file
                progressArray[i] = 100;
                setUploadProgress([...progressArray]);

            } catch (err) {
                console.error(`Error uploading ${file.name}:`, err);
                uploadResults.push({ file: file.name, success: false, error: err.message });
                progressArray[i] = -1; // Error state
                setUploadProgress([...progressArray]);
            }
        }

        setUploading(false);
        setShowUpload(false);
        
        // Refresh pictures list
        await fetchPictures();
        
        // Show results
        const successCount = uploadResults.filter(r => r.success).length;
        alert(`Upload complete! ${successCount}/${files.length} pictures uploaded successfully.`);
    };

    // Function to like a picture
    const likePicture = async (filename) => {
        try {
            const response = await fetch(`${process.env.REACT_APP_SERVER_URL}/pictures/like_picture`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ filename })
            });

            if (!response.ok) {
                throw new Error(`Failed to like picture: ${response.status}`);
            }

            const result = await response.json();
            
            if (result.success) {
                // Update the pictures array with new like count
                setPictures(prevPictures => 
                    prevPictures.map(pic => 
                        pic.filename === filename 
                            ? { ...pic, likes: result.likes }
                            : pic
                    )
                );
                
                // Show feedback
                setActionFeedback(`❤️ Liked! (${result.likes} total)`);
                setTimeout(() => setActionFeedback(''), 2000);
            } else {
                throw new Error(result.error || 'Failed to like picture');
            }
        } catch (err) {
            console.error('Error liking picture:', err);
            setError(`Failed to like picture: ${err.message}`);
        }
    };

    // Function to toggle picture visibility
    const togglePictureVisibility = async (filename) => {
        try {
            const response = await fetch(`${process.env.REACT_APP_SERVER_URL}/pictures/toggle_picture_visibility`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ filename })
            });

            if (!response.ok) {
                throw new Error(`Failed to toggle visibility: ${response.status}`);
            }

            const result = await response.json();
            
            if (result.success) {
                // Show feedback
                setActionFeedback(`👁️ Picture ${result.show_picture ? 'shown' : 'hidden'}`);
                setTimeout(() => setActionFeedback(''), 2000);
                
                // Refresh pictures to update the list
                await fetchPictures();
            } else {
                throw new Error(result.error || 'Failed to toggle visibility');
            }
        } catch (err) {
            console.error('Error toggling visibility:', err);
            setError(`Failed to toggle visibility: ${err.message}`);
        }
    };

    // File conversion helper
    const convertFileToBase64 = (file) => {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.onerror = reject;
            reader.readAsDataURL(file);
        });
    };

    // Handle file selection
    const handleFileSelect = (files) => {
        const imageFiles = Array.from(files).filter(file => 
            file.type.startsWith('image/')
        );
        
        if (imageFiles.length === 0) {
            alert('Please select valid image files.');
            return;
        }

        uploadPictures(imageFiles);
    };

    // Drag and drop handlers
    const handleDragOver = useCallback((e) => {
        e.preventDefault();
        setIsDragging(true);
    }, []);

    const handleDragLeave = useCallback((e) => {
        e.preventDefault();
        setIsDragging(false);
    }, []);

    const handleDrop = useCallback((e) => {
        e.preventDefault();
        setIsDragging(false);
        const files = e.dataTransfer.files;
        handleFileSelect(files);
    }, []);

    // Get current picture
    const currentPicture = pictures[currentIndex];

    // Fetch data on component mount
    useEffect(() => {
        fetchPictures();
    }, []);

    // Set up interval to cycle through pictures every 30 seconds
    useEffect(() => {
        if (pictures.length === 0 || showUpload) return;

        let progressInterval;
        let cycleTimeout;
        let fadeTimeout;

        const startCycle = () => {
            setProgress(0);
            setIsVisible(true);
            
            // Update progress bar every 100ms
            progressInterval = setInterval(() => {
                setProgress(prev => {
                    const newProgress = prev + (100 / 300); // 30 seconds = 300 intervals of 100ms
                    return newProgress >= 100 ? 100 : newProgress;
                });
            }, 100);

            // Start fade out 500ms before switching pictures
            fadeTimeout = setTimeout(() => {
                setIsVisible(false);
            }, 29500);

            // Move to next picture after 30 seconds
            cycleTimeout = setTimeout(() => {
                const nextIndex = (currentIndex + 1) % pictures.length;
                
                // If we're about to start a new cycle (going back to index 0), fetch new pictures
                if (nextIndex === 0 && currentIndex === pictures.length - 1) {
                    fetchPictures().then(() => {
                        setCurrentIndex(0);
                    });
                } else {
                    setCurrentIndex(nextIndex);
                }
                
                clearInterval(progressInterval);
                startCycle();
            }, 30000);
        };

        startCycle();

        return () => {
            clearInterval(progressInterval);
            clearTimeout(cycleTimeout);
            clearTimeout(fadeTimeout);
        };
    }, [pictures, currentIndex, showUpload]);

    // Reset visibility when picture changes
    useEffect(() => {
        setIsVisible(true);
    }, [currentIndex]);

    // Keyboard shortcuts
    useEffect(() => {
        const handleKeyPress = (e) => {
            if (e.key === 'u' || e.key === 'U') {
                setShowUpload(!showUpload);
            } else if (e.key === 'Escape') {
                setShowUpload(false);
            } else if (e.key === 'ArrowRight' && pictures.length > 0) {
                setCurrentIndex(prev => (prev + 1) % pictures.length);
            } else if (e.key === 'ArrowLeft' && pictures.length > 0) {
                setCurrentIndex(prev => (prev - 1 + pictures.length) % pictures.length);
            } else if ((e.key === 'l' || e.key === 'L') && currentPicture) {
                likePicture(currentPicture.filename);
            } else if ((e.key === 'h' || e.key === 'H') && currentPicture) {
                togglePictureVisibility(currentPicture.filename);
            }
        };

        window.addEventListener('keydown', handleKeyPress);
        return () => window.removeEventListener('keydown', handleKeyPress);
    }, [showUpload, pictures.length, currentPicture]);

    return (
        <div style={{ height: '100vh', width: '100vw', position: 'relative' }}>
            <style>
                {`
                    @keyframes fadeIn {
                        from { opacity: 0; transform: scale(0.95); }
                        to { opacity: 1; transform: scale(1); }
                    }
                    
                    .loading-spinner {
                        animation: spin 2s linear infinite;
                        font-size: 2rem;
                    }
                    
                    @keyframes spin {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }

                    .fade-in {
                        animation: fadeIn 0.5s ease-in-out;
                    }
                `}
            </style>

            <div style={fullScreenStyle}>
                {loading && pictures.length === 0 && (
                    <div style={{
                        color: '#667eea',
                        fontSize: '24px',
                        textAlign: 'center',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '15px',
                    }}>
                        <div className="loading-spinner">🖼️</div>
                        Loading Pictures...
                    </div>
                )}
                
                {error && pictures.length === 0 && (
                    <div style={{
                        color: '#ff6b6b',
                        fontSize: '18px',
                        textAlign: 'center',
                        padding: '20px',
                        backgroundColor: 'rgba(255, 107, 107, 0.1)',
                        borderRadius: '8px',
                        border: '1px solid rgba(255, 107, 107, 0.3)',
                    }}>
                        <div><strong>Error loading pictures:</strong></div>
                        <div>{error}</div>
                        <div style={{
                            marginTop: '15px',
                            fontSize: '14px',
                            color: '#ffcccc'
                        }}>
                            Pictures will be retried automatically on next cycle
                        </div>
                    </div>
                )}
                
                {currentPicture && (
                    <div style={{ opacity: isVisible ? 1 : 0, transition: 'opacity 0.5s ease-in-out' }}>
                        <img 
                            src={`${process.env.REACT_APP_SERVER_URL}/pictures/${currentPicture.filename}`}
                            alt={currentPicture.title || 'Picture'}
                            style={imageStyle}
                            className="fade-in"
                            onError={() => setError(`Failed to display picture: ${currentPicture.filename}`)}
                        />
                    </div>
                )}

                {pictures.length === 0 && !loading && !error && (
                    <div style={{
                        color: '#ffffff',
                        fontSize: '20px',
                        textAlign: 'center',
                        padding: '40px',
                    }}>
                        <div style={{ fontSize: '48px', marginBottom: '20px' }}>📷</div>
                        <div>No pictures available</div>
                        <div style={{ fontSize: '16px', color: '#999', marginTop: '10px' }}>
                            Press 'U' to upload pictures
                        </div>
                    </div>
                )}
            </div>

            {/* Upload Overlay */}
            {showUpload && (
                <div 
                    style={uploadOverlayStyle}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                >
                    <div style={isDragging ? uploadAreaActiveStyle : uploadAreaStyle}>
                        {!uploading ? (
                            <>
                                <div style={{ fontSize: '48px', marginBottom: '20px' }}>
                                    {isDragging ? '📤' : '📷'}
                                </div>
                                <h2 style={{ margin: '0 0 20px 0', color: '#ffffff' }}>
                                    Upload Pictures
                                </h2>
                                <p style={{ margin: '0 0 30px 0', color: '#cccccc' }}>
                                    Drag and drop pictures here or click to select files
                                </p>
                                <input
                                    type="file"
                                    ref={fileInputRef}
                                    multiple
                                    accept="image/*"
                                    style={{ display: 'none' }}
                                    onChange={(e) => handleFileSelect(e.target.files)}
                                />
                                <div style={{ display: 'flex', gap: '15px', justifyContent: 'center' }}>
                                    <button
                                        onClick={() => fileInputRef.current?.click()}
                                        style={{
                                            padding: '12px 24px',
                                            backgroundColor: '#667eea',
                                            color: 'white',
                                            border: 'none',
                                            borderRadius: '6px',
                                            cursor: 'pointer',
                                            fontSize: '16px',
                                            fontWeight: '500',
                                        }}
                                    >
                                        Select Files
                                    </button>
                                    <button
                                        onClick={() => setShowUpload(false)}
                                        style={{
                                            padding: '12px 24px',
                                            backgroundColor: 'transparent',
                                            color: 'white',
                                            border: '1px solid #666',
                                            borderRadius: '6px',
                                            cursor: 'pointer',
                                            fontSize: '16px',
                                            fontWeight: '500',
                                        }}
                                    >
                                        Cancel
                                    </button>
                                </div>
                                <p style={{ margin: '20px 0 0 0', color: '#999', fontSize: '14px' }}>
                                    Supports: JPG, PNG, GIF, WebP • Multiple files supported
                                </p>
                            </>
                        ) : (
                            <div style={{ textAlign: 'center' }}>
                                <div style={{ fontSize: '48px', marginBottom: '20px' }}>⏳</div>
                                <h2 style={{ margin: '0 0 20px 0', color: '#ffffff' }}>
                                    Uploading Pictures...
                                </h2>
                                {uploadProgress.map((progress, index) => (
                                    <div key={index} style={{ 
                                        margin: '10px 0',
                                        padding: '8px',
                                        backgroundColor: 'rgba(255,255,255,0.1)',
                                        borderRadius: '4px',
                                        fontSize: '14px'
                                    }}>
                                        <div style={{ marginBottom: '5px' }}>
                                            File {index + 1}: {
                                                progress === -1 ? '❌ Error' :
                                                progress === 100 ? '✅ Complete' :
                                                `${Math.round(progress)}%`
                                            }
                                        </div>
                                        <div style={{
                                            width: '100%',
                                            height: '4px',
                                            backgroundColor: 'rgba(255,255,255,0.2)',
                                            borderRadius: '2px',
                                            overflow: 'hidden'
                                        }}>
                                            <div style={{
                                                width: `${Math.max(0, progress)}%`,
                                                height: '100%',
                                                backgroundColor: progress === -1 ? '#ff6b6b' : '#4CAF50',
                                                transition: 'width 0.3s ease'
                                            }} />
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Controls */}
            <div style={controlsStyle}>
                <button
                    onClick={() => setShowUpload(!showUpload)}
                    style={buttonStyle}
                    onMouseOver={(e) => e.target.style.backgroundColor = 'rgba(102, 126, 234, 0.8)'}
                    onMouseOut={(e) => e.target.style.backgroundColor = 'rgba(0, 0, 0, 0.7)'}
                >
                    📤 Upload
                </button>
                {currentPicture && (
                    <>
                        <button
                            onClick={() => likePicture(currentPicture.filename)}
                            style={buttonStyle}
                            onMouseOver={(e) => e.target.style.backgroundColor = 'rgba(244, 67, 54, 0.8)'}
                            onMouseOut={(e) => e.target.style.backgroundColor = 'rgba(0, 0, 0, 0.7)'}
                        >
                            ❤️ Like
                        </button>
                        <button
                            onClick={() => togglePictureVisibility(currentPicture.filename)}
                            style={buttonStyle}
                            onMouseOver={(e) => e.target.style.backgroundColor = 'rgba(156, 39, 176, 0.8)'}
                            onMouseOut={(e) => e.target.style.backgroundColor = 'rgba(0, 0, 0, 0.7)'}
                        >
                            👁️ Hide
                        </button>
                    </>
                )}
            </div>
            {/* Progress bar */}
            {pictures.length > 0 && !showUpload && (
                <div style={progressBarStyle}>
                    <div style={{
                        ...progressFillStyle,
                        width: `${progress}%`
                    }} />
                </div>
            )}
            
            {/* Status display */}
            <div style={statusStyle}>
                <div style={{ 
                    color: '#667eea', 
                    fontWeight: '500',
                    fontSize: '16px'
                }}>
                    🖼️ Digital Frame
                </div>
                <div style={{ 
                    color: '#ffffff',
                    fontSize: '14px'
                }}>
                    {pictures.length > 0 ? `${currentIndex + 1} of ${pictures.length}` : 'No pictures'}
                </div>
                {actionFeedback && (
                    <div style={{ 
                        color: '#4CAF50', 
                        fontSize: '11px',
                        marginTop: '2px'
                    }}>
                        {actionFeedback}
                    </div>
                )}
                {error && (
                    <div style={{ 
                        color: '#ff6b6b', 
                        fontSize: '11px',
                        marginTop: '2px'
                    }}>
                        ⚠️ {error}
                    </div>
                )}
                {loading && (
                    <div style={{ 
                        color: '#4CAF50', 
                        fontSize: '11px',
                        marginTop: '2px'
                    }}>
                        🔄 Loading...
                    </div>
                )}
            </div>
        </div>
    );
};

export default Pictures;
