import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, ImageOverlay } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Custom styles for full-screen map
const fullScreenStyle = {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
};

// Set default icon paths for Leaflet markers
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
    iconUrl: require('leaflet/dist/images/marker-icon.png'),
    shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

const Flights = ({ theme }) => {
    const [images, setImages] = useState([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [bounds, setBounds] = useState([[49, -125], [24, -60]]);
    const [timestamp, setTimestamp] = useState('');
    const [selectedType, setSelectedType] = useState('rolling');
    const [selectedDuration, setSelectedDuration] = useState(30);

    // Fetch flight heatmaps from the server
    const getFlightHeatmapUrls = () => {
        fetch("http://192.168.0.152:5050/flightsdata", {
            headers: {
                'Content-Type': 'application/json'
            },
            method: 'POST',
            body: JSON.stringify({ type: selectedType, duration: selectedDuration })
        })
            .then(res => res.json())
            .then(data => {
                const urls = data.map(([url, time]) => ({
                    url: `http://192.168.0.244:5050/heatmap/${selectedType}/${time}.png`,
                    time
                }));
                setImages(urls);
            });
    };

    // Convert UNIX timestamp to EST format
    const convertToEST = (unixTimestamp) => {
        const date = new Date(unixTimestamp * 1000);
        return date.toLocaleString('en-US', { timeZone: 'America/New_York', hour12: false, hourCycle: 'h23' });
    };

    // Fetch URLs on initial render
    useEffect(() => {
        getFlightHeatmapUrls();
    }, [selectedType, selectedDuration]);

    // Refresh URLs every 10 minutes
    useEffect(() => {
        const interval = setInterval(() => {
            getFlightHeatmapUrls();
        }, 120000); // 2 minutes
        return () => clearInterval(interval);
    }, []);

    // Update the timestamp display when the image changes
    useEffect(() => {
        if (images.length > 0) {
            if (isNaN(currentIndex)) {
                setCurrentIndex(0);
            }
            const currentTimestamp = images[currentIndex]?.time;
            setTimestamp(convertToEST(currentTimestamp));
            console.log(currentIndex)
        }
    }, [images, currentIndex]);

    // Set an interval to update the current image in the slideshow
    useEffect(() => {
        const interval = setInterval(() => {
            setCurrentIndex((prevIndex) => (prevIndex + 1) % images.length);
        }, 1000); // 1 second interval
        return () => clearInterval(interval);
    }, [images.length]);

    // Button selection styling
    const buttonStyle = (isSelected) => ({
        backgroundColor: isSelected ? '#808080' : '#050505',
        border: '1px solid #808080',
        color: 'white',
        width: '40px',
        height: '40px',
        margin: '5px',
        borderRadius: '4px',
        cursor: 'pointer',
        textAlign: 'center',
        zIndex: 999
    });

    return (
        <div style={{ height: '100vh', width: '100vw', position: 'relative' }}>
            <MapContainer
                center={[37, -95]} // Center of the US
                zoom={4}
                style={fullScreenStyle}
                zoomControl={false}
                attributionControl={false}
            >
                <TileLayer
                    url={
                        theme === 'dark'
                            ? 'https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
                            : 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
                    }
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                />
                {images[currentIndex] && (
                    <ImageOverlay
                        bounds={bounds}
                        url={images[currentIndex].url}
                        opacity={0.7} // Set opacity to make overlay semi-transparent
                    />
                )}
            </MapContainer>
            <div style={{
                position: 'absolute',
                top: '10px',
                left: '10px',
                backgroundColor: 'rgba(0, 0, 0, 0.5)',
                color: 'white',
                padding: '5px 10px',
                borderRadius: '4px',
                zIndex: 999
            }}>
                {timestamp || 'Loading...'}
            </div>
            {/* Bottom right buttons */}
            <div style={{
                position: 'absolute',
                bottom: '20px',
                right: '20px',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'flex-end'
            }}>
                {/* Type selection row */}
                <div style={{ display: 'flex' }}>
                    {['type', 'rolling', 'reset_30_mins', 'reset_hour'].map((type) => (
                        <div
                            key={type}
                            style={buttonStyle(selectedType === type)}
                            onClick={() => setSelectedType(type)}
                        >
                            {type === 'rolling' ? 'Roll' : type.split('_')[1]}
                        </div>
                    ))}
                </div>
                {/* Duration selection row */}
                <div style={{ display: 'flex' }}>
                    {[30, 60, 360, 1440].map((duration) => (
                        <div
                            key={duration}
                            style={buttonStyle(selectedDuration === duration)}
                            onClick={() => setSelectedDuration(duration)}
                        >
                            {duration === 360 ? '6h' : duration === 1440 ? '24h' : `${duration}m`}
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default Flights;
