import React from 'react';

export default function MarketOverview({ marketData, assetInfo }) {
    if (!marketData) return <div className="card p-6 mb-6">Loading market data...</div>;
    
    if (marketData.status === 'DATA_UNAVAILABLE') {
        return (
            <div className="card p-6 mb-6 border-red-500 bg-red-50 dark:bg-red-900/10">
                <h2 className="text-xl font-bold text-red-600 dark:text-red-400 mb-2">Market Data Unavailable</h2>
                <p className="text-red-800 dark:text-red-200">Configure market data API for {assetInfo?.display_name || 'this asset'}</p>
            </div>
        );
    }

    const priceChange = marketData.change_percent || 0;
    const isUp = priceChange > 0;
    const isDown = priceChange < 0;

    const changeClass = isUp ? 'text-market-up' : isDown ? 'text-market-down' : 'text-light-muted dark:text-dark-muted';
    const sign = isUp ? '+' : '';

    return (
        <div className="card p-6 mb-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-6 shadow-sm">
            <div>
                <h2 className="text-3xl font-black tracking-tight">{assetInfo?.display_name}</h2>
                <div className="flex items-center gap-4 mt-2">
                    <div className="text-3xl font-mono font-semibold">
                        {marketData.price ? marketData.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: assetInfo?.category === 'FOREX' ? 4 : 2 }) : '---'}
                    </div>
                    <div className={`text-lg font-bold font-mono ${changeClass}`}>
                        {marketData.price ? `${sign}${priceChange.toFixed(2)}%` : ''}
                    </div>
                </div>
            </div>
            
            <div className="flex flex-row md:flex-col items-center md:items-end gap-4 md:gap-1 text-sm text-light-muted dark:text-dark-muted font-medium">
                <div className="flex items-center gap-2">
                    <span className="relative flex h-2.5 w-2.5">
                      {marketData.market_status === 'OPEN' ? (
                          <>
                              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-green-500"></span>
                          </>
                      ) : (
                          <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-gray-400"></span>
                      )}
                    </span>
                    <span className="uppercase tracking-wider font-bold">
                        {marketData.market_status === 'OPEN' ? 'LIVE' : marketData.market_status || 'CLOSED'}
                    </span>
                </div>
                <div>Updated: {new Date(marketData.timestamp || Date.now()).toLocaleTimeString()}</div>
                <div>Source: {marketData.provider || 'System'}</div>
            </div>
        </div>
    );
}
