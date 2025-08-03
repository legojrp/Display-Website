import React, { useState, useEffect } from 'react';

// Custom styles for full-screen display
const fullScreenStyle = {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: '#0a0a0a',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    padding: '40px',
    boxSizing: 'border-box',
    fontFamily: '"Segoe UI", Roboto, -apple-system, BlinkMacSystemFont, sans-serif',
};

const newsContainerStyle = {
    maxWidth: '1200px',
    width: '100%',
    textAlign: 'center',
    color: '#ffffff',
    transition: 'opacity 0.5s ease-in-out',
};

const titleStyle = {
    fontSize: 'clamp(2.5rem, 6vw, 4.5rem)',
    fontWeight: '700',
    lineHeight: '1.2',
    marginBottom: '20px',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    backgroundClip: 'text',
    textShadow: '0 2px 4px rgba(0,0,0,0.3)',
};

const descriptionStyle = {
    fontSize: 'clamp(1.2rem, 3vw, 2rem)',
    lineHeight: '1.4',
    marginBottom: '30px',
    color: '#e0e0e0',
    fontWeight: '300',
    maxWidth: '900px',
    margin: '0 auto 30px',
};

const metaInfoStyle = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '20px',
    fontSize: 'clamp(0.9rem, 2vw, 1.1rem)',
    color: '#888',
    flexWrap: 'wrap',
    gap: '10px',
};

const publishedDateStyle = {
    color: '#4CAF50',
    fontWeight: '500',
};

const rankingStyle = {
    color: '#FFA726',
    fontWeight: '600',
};

const reasoningStyle = {
    fontSize: 'clamp(0.8rem, 1.8vw, 1rem)',
    color: '#666',
    fontStyle: 'italic',
    lineHeight: '1.3',
    marginTop: '10px',
    padding: '15px',
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderRadius: '8px',
    border: '1px solid rgba(255,255,255,0.1)',
};

const statusStyle = {
    position: 'absolute',
    bottom: '30px',
    right: '30px',
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    color: '#e0e0e0',
    padding: '12px 20px',
    borderRadius: '12px',
    zIndex: 999,
    fontSize: '13px',
    fontWeight: '300',
    border: '1px solid rgba(255,255,255,0.1)',
    backdropFilter: 'blur(15px)',
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
    minWidth: '140px',
};

const progressBarStyle = {
    position: 'absolute',
    bottom: '0',
    left: '0',
    height: '3px',
    backgroundColor: '#667eea',
    transition: 'width 0.1s linear',
    borderRadius: '2px',
};

const loadingStyle = {
    color: '#667eea',
    fontSize: '24px',
    textAlign: 'center',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '15px',
};

const errorStyle = {
    color: '#ff6b6b',
    fontSize: '18px',
    textAlign: 'center',
    padding: '20px',
    backgroundColor: 'rgba(255, 107, 107, 0.1)',
    borderRadius: '8px',
    border: '1px solid rgba(255, 107, 107, 0.3)',
};

const retryButtonStyle = {
    marginTop: '15px',
    padding: '12px 24px',
    backgroundColor: '#667eea',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '16px',
    fontWeight: '500',
    transition: 'background-color 0.3s ease',
};

const News = ({ theme }) => {
    const [newsData, setNewsData] = useState([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [lastUpdate, setLastUpdate] = useState('');
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(true);
    const [progress, setProgress] = useState(0);
    const [isVisible, setIsVisible] = useState(true);
    
    // Function to fetch news data
    const fetchNewsData = async () => {
        try {
            setLoading(true);
            const response = await fetch(`${process.env.REACT_APP_SERVER_URL}/get_news`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (Array.isArray(data) && data.length > 0) {
                setNewsData(data);
                setCurrentIndex(0);
                setLastUpdate(new Date().toLocaleString());
                setError(null);
            } else {
                throw new Error('No news data received');
            }
        } catch (err) {
            console.error('Error fetching news data:', err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    // Format date for display
    const formatDate = (dateString) => {
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch {
            return dateString;
        }
    };

    // Fetch data on component mount
    useEffect(() => {
        fetchNewsData();
    }, []);

    // Set up interval to fetch data every 10 minutes
    useEffect(() => {
        const interval = setInterval(fetchNewsData, 10 * 60 * 1000);
        return () => clearInterval(interval);
    }, []);

    // Set up interval to cycle through headlines every 30 seconds
    useEffect(() => {
        if (newsData.length === 0) return;

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

            // Start fade out 500ms before switching articles
            fadeTimeout = setTimeout(() => {
                setIsVisible(false);
            }, 29500);

            // Move to next headline after 30 seconds
            cycleTimeout = setTimeout(() => {
                setCurrentIndex(prev => (prev + 1) % newsData.length);
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
    }, [newsData, currentIndex]);

    // Reset visibility when article changes
    useEffect(() => {
        setIsVisible(true);
    }, [currentIndex]);

    const currentNews = newsData[currentIndex];

    return (
        <div style={{ height: '100vh', width: '100vw', position: 'relative' }}>
            <style>
                {`
                    @keyframes fadeIn {
                        from { opacity: 0; transform: translateY(20px); }
                        to { opacity: 1; transform: translateY(0); }
                    }
                    
                    .loading-spinner {
                        animation: spin 2s linear infinite;
                        font-size: 2rem;
                    }
                    
                    @keyframes spin {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }
                `}
            </style>
            <div style={fullScreenStyle}>
                {loading && newsData.length === 0 && (
                    <div style={loadingStyle}>
                        <div className="loading-spinner">📰</div>
                        Loading Latest News...
                    </div>
                )}
                
                {error && newsData.length === 0 && (
                    <div style={errorStyle}>
                        <div><strong>Error loading news:</strong></div>
                        <div>{error}</div>
                        <button 
                            onClick={fetchNewsData}
                            style={retryButtonStyle}
                            onMouseOver={(e) => e.target.style.backgroundColor = '#5a67d8'}
                            onMouseOut={(e) => e.target.style.backgroundColor = '#667eea'}
                        >
                            Retry
                        </button>
                    </div>
                )}
                
                {currentNews && (
                    <div style={{
                        ...newsContainerStyle,
                        opacity: isVisible ? 1 : 0
                    }}>
                        <h1 style={titleStyle}>
                            {currentNews.title}
                        </h1>
                        
                        <p style={descriptionStyle}>
                            {currentNews.description}
                        </p>
                        
                        <div style={metaInfoStyle}>
                            <span style={publishedDateStyle}>
                                📅 {formatDate(currentNews.published_date)}
                            </span>
                            <span style={rankingStyle}>
                                ⭐ Score: {currentNews.ranking_score}/100
                            </span>
                        </div>
                        
                        {currentNews.ai_reasoning && (
                            <div style={reasoningStyle}>
                                <strong>AI Analysis:</strong> {currentNews.ai_reasoning}
                            </div>
                        )}
                        
                        {currentNews.author && (
                            <div style={{ 
                                marginTop: '20px', 
                                fontSize: '0.9rem', 
                                color: '#999',
                                fontStyle: 'italic'
                            }}>
                                By {currentNews.author}
                            </div>
                        )}
                    </div>
                )}
            </div>
            
            {/* Progress bar */}
            {newsData.length > 0 && (
                <div style={{
                    position: 'absolute',
                    bottom: '0',
                    left: '0',
                    right: '0',
                    height: '3px',
                    backgroundColor: 'rgba(255,255,255,0.1)',
                }}>
                    <div style={{
                        ...progressBarStyle,
                        width: `${progress}%`
                    }} />
                </div>
            )}
            
            {/* Status display */}
            <div style={statusStyle}>
                <div style={{ 
                    color: '#667eea', 
                    fontWeight: '500',
                    fontSize: '14px'
                }}>
                    {currentIndex + 1} of {newsData.length}
                </div>
                <div style={{ 
                    color: '#999',
                    fontSize: '12px'
                }}>
                    {lastUpdate}
                </div>
                {error && (
                    <div style={{ 
                        color: '#ff6b6b', 
                        fontSize: '11px',
                        marginTop: '2px'
                    }}>
                        ⚠️ Error
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

export default News;