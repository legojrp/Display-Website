import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
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

// Create a custom aircraft icon with direction and info
const createAircraftIcon = (aircraft) => {
    const { altitude, track, callsign } = aircraft;
    
    // Color aircraft markers based on altitude
    let color = '#ffffff'; // Default white
    if (altitude > 30000) {
        color = '#ff0000'; // Red for high altitude
    } else if (altitude > 20000) {
        color = '#ffff00'; // Yellow for medium altitude
    } else if (altitude > 10000) {
        color = '#00ff00'; // Green for medium-low altitude
    } else if (altitude > 0) {
        color = '#0000ff'; // Blue for low altitude
    }

    // Format altitude for display
    const altDisplay = altitude > 0 ? `${Math.round(altitude/100)}` : '---';
    const callsignDisplay = callsign !== 'N/A' ? callsign : "N/A";

    return L.divIcon({
        className: 'custom-aircraft-icon',
        html: `
            <div style="position: relative; text-align: center;">
                <!-- Aircraft symbol pointing in direction -->
                <div style="
                    width: 0; 
                    height: 0; 
                    border-left: 4px solid transparent;
                    border-right: 4px solid transparent;
                    border-bottom: 12px solid ${color};
                    transform: rotate(${track}deg);
                    filter: drop-shadow(0 0 2px rgba(0,0,0,0.8));
                    margin: 0 auto;
                "></div>
                
                <!-- Flight info below aircraft -->
                <div style="
                    font-family: monospace;
                    font-size: 10px;
                    color: white;
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
                    margin-top: 2px;
                    white-space: nowrap;
                    font-weight: bold;
                ">
                    ${callsignDisplay}<br/>
                    ${altDisplay}
                </div>
            </div>
        `,
        iconSize: [60, 40],
        iconAnchor: [30, 20]
    });
};

const Radar = ({ theme }) => {
    const [aircraft, setAircraft] = useState([]);
    const [lastUpdate, setLastUpdate] = useState('');
    const [error, setError] = useState(null);
    
    // Define your map bounds - adjust these to your desired viewing area
    const mapBounds = {
        center: [39.9335548,-85.8868422], // Center around Indiana area based on your sample data
        zoom: 10,
        minLat: 39.4,
        maxLat: 40.5,
        minLon: -87.3,
        maxLon: -85.0
    };

    // Function to fetch aircraft data from your FR24 feeder
    const fetchAircraftData = async () => {
        try {
            const response = await fetch(`${process.env.REACT_APP_SERVER_URL}/radar-json`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ ipad: 'your_ipad_value' }) // Replace with actual value
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Parse the aircraft data
            const aircraftList = Object.entries(data).map(([key, ac]) => {
                // Based on the FR24 format: ["4A914F", 59.2893, 18.1239, 305, 2275, 179, "5322", 0, "", "", 1415781759, "", "", "", 0, -640, "SCW10"]
                const [modeS, lat, lon, track, altitude, speed, squawk, , , , timestamp, , , , , , callsign] = ac;
                
                // Only include aircraft with valid coordinates
                if (lat && lon && Math.abs(lat) > 0.001 && Math.abs(lon) > 0.001) {
                    // Check if aircraft is within your specified bounds
                    if (lat >= mapBounds.minLat && lat <= mapBounds.maxLat && 
                        lon >= mapBounds.minLon && lon <= mapBounds.maxLon) {
                        return {
                            id: key,
                            modeS,
                            lat: parseFloat(lat),
                            lon: parseFloat(lon),
                            altitude: parseInt(altitude) || 0,
                            speed: parseInt(speed) || 0,
                            track: parseInt(track) || 0,
                            squawk: squawk || 'N/A',
                            callsign: callsign || 'N/A',
                            timestamp
                        };
                    }
                }
                return null;
            }).filter(aircraft => aircraft !== null);
            
            setAircraft(aircraftList);
            setLastUpdate(new Date().toLocaleTimeString());
            setError(null);
        } catch (err) {
            console.error('Error fetching aircraft data:', err);
            setError(err.message);
        }
    };

    // Fetch data on component mount
    useEffect(() => {
        fetchAircraftData();
    }, []);

    // Set up interval to fetch data every 5 seconds
    useEffect(() => {
        const interval = setInterval(fetchAircraftData, 5000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div style={{ height: '100vh', width: '100vw', position: 'relative' }}>
            <MapContainer
                center={[mapBounds.center[0], mapBounds.center[1]]}
                zoom={mapBounds.zoom}
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
                
                {/* Render aircraft markers */}
                {aircraft.map((ac) => (
                    <Marker
                        key={ac.id}
                        position={[ac.lat, ac.lon]}
                        icon={createAircraftIcon(ac)}
                    >
                    </Marker>
                ))}
            </MapContainer>
            
            {/* Status display */}
            <div style={{
                position: 'absolute',
                top: '10px',
                left: '10px',
                backgroundColor: 'rgba(0, 0, 0, 0.7)',
                color: 'white',
                padding: '10px',
                borderRadius: '4px',
                zIndex: 999,
                fontSize: '14px'
            }}>
                <div><strong>Aircraft Radar</strong></div>
                <div>Aircraft: {aircraft.length}</div>
                <div>Last Update: {lastUpdate}</div>
                {error && <div style={{ color: '#ff6b6b' }}>Error: {error}</div>}
            </div>
            
            {/* Legend */}
            <div style={{
                position: 'absolute',
                bottom: '20px',
                left: '20px',
                backgroundColor: 'rgba(0, 0, 0, 0.7)',
                color: 'white',
                padding: '10px',
                borderRadius: '4px',
                zIndex: 999,
                fontSize: '12px'
            }}>
                <div><strong>Altitude Legend</strong></div>
                <div style={{ display: 'flex', alignItems: 'center', margin: '2px 0' }}>
                    <div style={{ 
                        width: '8px', height: '8px', backgroundColor: '#ff0000', 
                        border: '1px solid #000', borderRadius: '50%', marginRight: '5px' 
                    }}></div>
                    &gt; 30,000 ft
                </div>
                <div style={{ display: 'flex', alignItems: 'center', margin: '2px 0' }}>
                    <div style={{ 
                        width: '8px', height: '8px', backgroundColor: '#ffff00', 
                        border: '1px solid #000', borderRadius: '50%', marginRight: '5px' 
                    }}></div>
                    20,000 - 30,000 ft
                </div>
                <div style={{ display: 'flex', alignItems: 'center', margin: '2px 0' }}>
                    <div style={{ 
                        width: '8px', height: '8px', backgroundColor: '#00ff00', 
                        border: '1px solid #000', borderRadius: '50%', marginRight: '5px' 
                    }}></div>
                    10,000 - 20,000 ft
                </div>
                <div style={{ display: 'flex', alignItems: 'center', margin: '2px 0' }}>
                    <div style={{ 
                        width: '8px', height: '8px', backgroundColor: '#0000ff', 
                        border: '1px solid #000', borderRadius: '50%', marginRight: '5px' 
                    }}></div>
                    &lt; 10,000 ft
                </div>
            </div>
        </div>
    );
};

export default Radar;
