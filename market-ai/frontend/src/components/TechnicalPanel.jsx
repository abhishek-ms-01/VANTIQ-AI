import React from 'react';

export default function TechnicalPanel({ analysisData }) {
    if (!analysisData) return null;

    // Use dummy or actual values if they come from backend API in `analysisData`
    const indicators = [
        { name: 'EMA (20/50)', value: analysisData.ema || 'Bullish Cross' },
        { name: 'RSI (14)', value: analysisData.rsi || '54.20' },
        { name: 'MACD', value: analysisData.macd || '+12.4' },
        { name: 'ADX (14)', value: analysisData.adx || '28.5 (Strong)' },
        { name: 'ATR (14)', value: analysisData.atr || '120.5' },
        { name: 'VWAP', value: analysisData.vwap || '52,400' },
        { name: 'Volume', value: analysisData.volume || '120K' }
    ];

    return (
        <div className="card p-6 mb-6 shadow-sm">
            <h3 className="text-lg font-bold mb-4 border-b border-light-border dark:border-dark-border pb-2 tracking-wide uppercase text-sm text-light-muted dark:text-dark-muted">
                Technical Panel
            </h3>
            <div className="grid grid-cols-1 divide-y divide-light-border dark:divide-dark-border border border-light-border dark:border-dark-border rounded-lg bg-gray-50 dark:bg-gray-800/50">
                {indicators.map((ind, i) => (
                    <div key={i} className="flex justify-between items-center py-2 px-4 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
                        <span className="text-sm font-semibold tracking-wide text-light-muted dark:text-dark-muted uppercase">{ind.name}</span>
                        <span className="font-mono text-sm font-bold">{ind.value}</span>
                    </div>
                ))}
            </div>
        </div>
    );
}
