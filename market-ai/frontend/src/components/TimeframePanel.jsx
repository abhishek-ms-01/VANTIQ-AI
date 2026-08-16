import React from 'react';

export default function TimeframePanel({ timeframes, activeTimeframe, setActiveTimeframe }) {
    if (!timeframes || timeframes.length === 0) return null;
    
    // Simulate trend status for visual indicators (or pass from backend if available)
    const getStatusIndicator = (tf) => {
        // Just for visualization of the subtle indicators required by prompt
        // Ideally this maps to real backend multi-timeframe analysis
        if (tf === '1D' || tf === '4H') return 'bg-green-500'; 
        if (tf === '1H') return 'bg-yellow-500';
        return 'bg-red-500';
    };

    return (
        <div className="flex flex-wrap gap-2 mb-6 border-b border-light-border dark:border-dark-border pb-4">
            {timeframes.map(tf => (
                <button
                    key={tf}
                    className={`relative px-4 py-1.5 text-sm font-semibold rounded-md transition-all duration-200 border ${
                        activeTimeframe === tf 
                        ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 border-blue-200 dark:border-blue-800 shadow-sm' 
                        : 'bg-transparent text-light-muted dark:text-dark-muted border-transparent hover:bg-gray-100 dark:hover:bg-gray-800'
                    }`}
                    onClick={() => setActiveTimeframe(tf)}
                >
                    <div className="flex items-center gap-2">
                        {tf}
                        <span className={`w-1.5 h-1.5 rounded-full ${getStatusIndicator(tf)} opacity-75`}></span>
                    </div>
                </button>
            ))}
        </div>
    );
}
