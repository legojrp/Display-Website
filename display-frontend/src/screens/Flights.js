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

    // Fetch flight heatmaps from the server
    const getFlightHeatmapUrls = () => {
        fetch("http://192.168.0.152:5050/flights")
            .then(res => res.json())
            .then(data => {
                const urls = data.map(([url, time]) => ({
                    url: `http://192.168.0.152:5050/heatmap/accum/${time}.png`,
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
    }, []);

    // Refresh URLs every 10 minutes
    useEffect(() => {
        const interval = setInterval(() => {
            getFlightHeatmapUrls();
        }, 600000); // 10 minutes
        return () => clearInterval(interval);
    }, []);

    // Update the timestamp display when the image changes
    useEffect(() => {
        if (images.length > 0) {
            const currentTimestamp = images[currentIndex]?.time;
            setTimestamp(convertToEST(currentTimestamp));
        }
    }, [images, currentIndex]);

    // Set an interval to update the current image in the slideshow
    useEffect(() => {
        const interval = setInterval(() => {
            setCurrentIndex((prevIndex) => (prevIndex + 1) % images.length);
        }, 1000); // 1 second interval
        return () => clearInterval(interval);
    }, [images.length]);

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
        </div>
    );
};

export default Flights;
