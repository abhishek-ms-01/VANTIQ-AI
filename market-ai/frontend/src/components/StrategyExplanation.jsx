import React from 'react';

export default function StrategyExplanation({ strategyData }) {
    if (!strategyData) return null;

    const {
        market_regime,
        reasons,
        warnings,
        invalidation_level,
        strategy_name = 'AlphaTrend Pro' // default or passed from backend
    } = strategyData;

    return (
        <div className="card p-6 mb-6 shadow-sm">
            <h3 className="text-lg font-bold mb-4 border-b border-light-border dark:border-dark-border pb-2 tracking-wide uppercase text-sm text-light-muted dark:text-dark-muted flex justify-between">
                <span>Strategy Analysis</span>
                <span className="text-blue-500 font-black">{strategy_name}</span>
            </h3>
            
            <div className="space-y-4 text-sm text-light-text dark:text-dark-text">
                <div>
                    <div className="text-xs font-bold text-muted uppercase tracking-wider mb-1">Market Regime</div>
                    <div className="font-semibold bg-gray-100 dark:bg-gray-800 inline-block px-3 py-1 rounded tracking-wide">{market_regime || 'UNKNOWN'}</div>
                </div>

                <div>
                    <div className="text-xs font-bold text-muted uppercase tracking-wider mb-1">Why the signal exists</div>
                    <ul className="list-disc pl-5 space-y-1">
                        {reasons && reasons.length > 0 ? (
                            reasons.map((r, i) => <li key={i}>{r}</li>)
                        ) : (
                            <li>No active signal reasons.</li>
                        )}
                    </ul>
                </div>

                <div>
                    <div className="text-xs font-bold text-muted uppercase tracking-wider mb-1">Invalidation</div>
                    <div className="text-red-700 dark:text-red-400 font-medium">
                        {invalidation_level || 'No invalidation parameters active.'}
                    </div>
                </div>

                {warnings && warnings.length > 0 && (
                    <div className="bg-yellow-50 dark:bg-yellow-900/10 p-3 rounded border border-yellow-200 dark:border-yellow-900/30">
                        <div className="text-xs font-bold text-yellow-700 dark:text-yellow-500 uppercase tracking-wider mb-1">Warnings</div>
                        <ul className="list-disc pl-5 space-y-1 text-yellow-800 dark:text-yellow-400">
                            {warnings.map((w, i) => <li key={i}>{w}</li>)}
                        </ul>
                    </div>
                )}
                
                <div className="mt-4 pt-4 border-t border-light-border dark:border-dark-border">
                    <span className="text-xs text-muted block mb-1 uppercase tracking-wider">AI Insight</span>
                    <p className="text-xs italic text-light-muted dark:text-dark-muted">
                        This purely explains backend calculation outcomes deterministically to prevent hallucination.
                    </p>
                </div>
            </div>
        </div>
    );
}
