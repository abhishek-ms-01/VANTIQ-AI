import React from 'react';

export default function PriceChart({ darkMode }) {
    // Dynamically match the TradingView theme to the App theme
    const theme = darkMode ? 'dark' : 'light';
    const bg = darkMode ? 'rgba(17,24,39,1)' : 'rgba(255,255,255,1)'; 
    const widgetUrl = `https://s.tradingview.com/widgetembed/?frameElementId=tradingview_vantiq&symbol=FX%3AXAUUSD&interval=15&hidesidetoolbar=0&symboledit=1&saveimage=0&toolbarbg=${encodeURIComponent(bg)}&studies=%5B%5D&theme=${theme}&style=1&timezone=Etc%2FUTC&locale=en`;

    return (
        <div className="card p-2 mb-6 shadow-sm border border-light-border dark:border-dark-border flex flex-col" style={{ height: '600px' }}>
            <iframe 
                id="tradingview_vantiq"
                src={widgetUrl}
                style={{ width: '100%', height: '100%', border: 'none' }}
                allowtransparency="true"
                scrolling="no"
                title="TradingView Chart"
            ></iframe>
            <div className="text-right mt-1 mr-2">
                <a 
                    href="https://www.tradingview.com/" 
                    rel="noopener noreferrer" 
                    target="_blank" 
                    className="text-[10px] text-gray-500 hover:text-gray-400 font-medium"
                >
                    Track all markets on TradingView
                </a>
            </div>
        </div>
    );
}
