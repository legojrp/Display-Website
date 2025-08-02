import React, {useState, useEffect} from 'react';
import WeatherRadar from "./WeatherRadar"
import Flights from './Flights';
import Radar from './Radar';
import Earth from './Earth';

function Display() {
    const [screen, setScreen] = useState(null);
    const [theme, setTheme] = useState(null);
    
    useEffect(() => {
        const urlParams = new URLSearchParams(window.location.search);
        const ipadValue = urlParams.get('ipad');
    
        // Define a function to fetch data with ipadValue in JSON body
        const fetchData = () => {
            const url = new URL(window.location.href);
            const path = url.pathname.split('/').pop();
            fetch(`${process.env.REACT_APP_SERVER_URL}/${path}`, {
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                method: 'POST',
                body: JSON.stringify({ ipad: ipadValue }) // Send ipadValue in JSON format
            })
            .then(res => res.json())
            .then(data => {
                setScreen(data.screen);
                setTheme(data.theme);
            })
            .catch(error => console.error('Error fetching data:', error));
        };
    
        // Initial fetch
        fetchData();
    
        // Set up interval to fetch data every 60 seconds
        const screenInterval = setInterval(fetchData, 60000);
    
        // Clear interval on component unmount
        return () => clearInterval(screenInterval);
    }, []);
    

    switch (screen) {
        case "weather":
            return (
                <div style={{background: theme === 'dark' ? 'black' : 'white'}}>
                    <WeatherRadar theme={theme}/>
                </div>
            );
        case "flights":
            return (
                <div style={{background: theme === 'dark' ? 'black' : 'white'}}>
                    <Flights theme={theme}/>
                </div>
            );
        case "radar":
            return (
                <div style={{background: theme === 'dark' ? 'black' : 'white'}}>
                    <Radar theme={theme}/>
                </div>
            );
        case "earth":
            return (
                <div style={{background: theme === 'dark' ? 'black' : 'white'}}>
                    <Earth theme={theme}/>
                </div>
            );
        case "display":
            return (
                <div style={{background: theme === 'dark' ? 'black' : 'white'}}>
                    <h1>Display</h1>
                </div>
            );
        default:
            return (
                <div style={{background: theme === 'dark' ? 'black' : 'white'}}>
                    <h1>Error</h1>
                </div>
            );
    }
}

export default Display;

