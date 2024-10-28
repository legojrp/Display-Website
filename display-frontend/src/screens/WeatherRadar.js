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

const WeatherRadar = ({ theme }) => {
    const [images, setImages] = useState([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [radarUrls, setRadarUrls] = useState([]);
    const [bounds, setBounds] = useState([[40, -110], [30, -100]]); // Example bounds
    const [coords, setCoords] = useState({ lat: 39.06142304508583, lon: -96.97938417503661, zoom: 2 });
    const [timestamp, setTimestamp] = useState('');

    const getRadarUrls = () => {
        fetch("http://192.168.0.152:5050/weather")
            .then(res => res.json())
            .then(data => {
                const urls = data.radar.past.map(url => ({ url: url.url, time: url.time }));
                console.log(urls);
                setRadarUrls(urls);
                setBounds([data.bounds["top_left"], data.bounds["bottom_right"]]);
                setCoords(data.coords);
            });
    };

    const convertToEST = (unixTimestamp) => {
        const date = new Date(unixTimestamp * 1000);
        return date.toLocaleString('en-US', { timeZone: 'America/New_York', hour12: false, hourCycle: 'h23' });
    };

    useEffect(() => {
        getRadarUrls();
    }, []);

    useEffect(() => {
        const radarInterval = setInterval(() => {
            getRadarUrls();
        }, 600000);
        return () => clearInterval(radarInterval);
    }, [radarUrls]);

    const loadImages = () => {
        const loadedImages = radarUrls.map(url => {
            const img = new Image();
            img.setAttribute("timestamp", url.timestamp);
            img.src = url.url;
            return img;
        });
        setImages(loadedImages);
    };

    useEffect(() => {
        loadImages();
    }, [radarUrls]);

    useEffect(() => {
        if (radarUrls.length > 0) {
            const currentTimestamp = radarUrls[currentIndex]?.time;
            console.log(currentTimestamp);
            console.log(currentIndex);
            setTimestamp(convertToEST(currentTimestamp));

        }
    }, [radarUrls, currentIndex]);
    
    useEffect(() => {
        const interval = setInterval(() => {
            if (isNaN(currentIndex)) {
                setCurrentIndex(0);
            }
            setCurrentIndex((prevIndex) => (prevIndex + 1) % images.length);
        }, 1000);
        return () => clearInterval(interval);
    }, [images.length, currentIndex]);

    return (
        <div style={{ height: '100vh', width: '100vw', position: 'relative' }}>
            <MapContainer
                center={[coords.lat, coords.lon]}
                zoom={coords.zoom + 2}
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
                        url={images[currentIndex].src}
                        opacity={1}
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

export default WeatherRadar;
