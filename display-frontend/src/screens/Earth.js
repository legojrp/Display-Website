import React, { useState, useEffect } from 'react';

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
};

const imageStyle = {
    width: '100vw',
    height: '100vh',
    objectFit: 'cover',
};

const Earth = ({ theme }) => {
    const [imageData, setImageData] = useState(null);
    const [lastUpdate, setLastUpdate] = useState('');
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(true);
    
    // Function to fetch GOES satellite image data
    const fetchGoesImage = async () => {
        try {
            setLoading(true);
            const response = await fetch(`${process.env.REACT_APP_SERVER_URL}/goes-image`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.text();
            
            // Assuming the API returns base64 image data
            // If it returns JSON with base64 data, parse it accordingly
            let base64Image;
            try {
                const jsonData = JSON.parse(data);
                base64Image = jsonData.image || jsonData.data || data;
            } catch {
                base64Image = data;
            }
            
            // Ensure the base64 string has the proper data URL format
            if (!base64Image.startsWith('data:image/')) {
                base64Image = `data:image/png;base64,${base64Image}`;
            }
            
            setImageData(base64Image);
            setLastUpdate(new Date().toLocaleString());
            setError(null);
        } catch (err) {
            console.error('Error fetching GOES image:', err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    // Fetch data on component mount
    useEffect(() => {
        fetchGoesImage();
    }, []);

    // Set up interval to fetch data every 10 minutes (600,000 milliseconds)
    useEffect(() => {
        const interval = setInterval(fetchGoesImage, 10 * 60 * 1000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div style={{ height: '100vh', width: '100vw', position: 'relative' }}>
            <div style={fullScreenStyle}>
                {loading && !imageData && (
                    <div style={{
                        color: 'white',
                        fontSize: '24px',
                        textAlign: 'center'
                    }}>
                        Loading GOES Satellite Image...
                    </div>
                )}
                
                {error && !imageData && (
                    <div style={{
                        color: '#ff6b6b',
                        fontSize: '18px',
                        textAlign: 'center',
                        padding: '20px'
                    }}>
                        <div>Error loading satellite image:</div>
                        <div>{error}</div>
                        <button 
                            onClick={fetchGoesImage}
                            style={{
                                marginTop: '10px',
                                padding: '10px 20px',
                                backgroundColor: '#4CAF50',
                                color: 'white',
                                border: 'none',
                                borderRadius: '4px',
                                cursor: 'pointer'
                            }}
                        >
                            Retry
                        </button>
                    </div>
                )}
                
                {imageData && (
                    <img 
                        src={imageData} 
                        alt="GOES Satellite Earth View" 
                        style={imageStyle}
                        onError={() => setError('Failed to display image')}
                    />
                )}
            </div>
            
            {/* Status display */}
            <div style={{
                position: 'absolute',
                bottom: '20px',
                right: '20px',
                backgroundColor: 'rgba(0, 0, 0, 0.7)',
                color: 'white',
                padding: '10px',
                borderRadius: '4px',
                zIndex: 999,
                fontSize: '14px'
            }}>
                <div><strong>GOES Satellite - Earth View</strong></div>
                <div>Last Update: {lastUpdate}</div>
                <div>Update Interval: 10 minutes</div>
                {error && <div style={{ color: '#ff6b6b' }}>Error: {error}</div>}
                {loading && <div style={{ color: '#4CAF50' }}>Loading...</div>}
            </div>
        </div>
    );
};

export default Earth;
