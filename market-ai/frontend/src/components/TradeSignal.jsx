import React from 'react';

export default function TradeSignal({ strategyData }) {
    if (!strategyData) return null;

    const {
        direction,
        signal_strength,
        trade_quality,
        entry_price,
        stop_loss,
        target_1,
        target_2,
        risk_reward_target_1,
        invalidation_level,
        reasons,
        warnings
    } = strategyData;

    const isNoTrade = direction === 'NO_TRADE' || !direction;

    const getDirectionStyles = (dir) => {
        if (dir === 'LONG') return 'text-market-up border-market-up bg-green-50 dark:bg-green-900/20';
        if (dir === 'SHORT') return 'text-market-down border-market-down bg-red-50 dark:bg-red-900/20';
        return 'text-market-warn border-market-warn bg-yellow-50 dark:bg-yellow-900/20';
    };

    return (
        <div className="card p-6 mb-6 shadow-sm">
            <h3 className="text-lg font-bold mb-4 border-b border-light-border dark:border-dark-border pb-2 tracking-wide uppercase text-sm text-light-muted dark:text-dark-muted">
                Trade Decision
            </h3>
            
            <div className="flex flex-col gap-6">
                <div className="flex items-center justify-between">
                    <div className={`text-2xl font-black px-4 py-2 rounded border-2 ${getDirectionStyles(direction)} tracking-wider`}>
                        {direction || 'NO_TRADE'}
                    </div>
                    {!isNoTrade && (
                        <div className="flex gap-4 text-right">
                            <div>
                                <div className="text-xs text-muted uppercase tracking-wider mb-1">Signal</div>
                                <div className="text-lg font-bold">{signal_strength}/100</div>
                            </div>
                            <div>
                                <div className="text-xs text-muted uppercase tracking-wider mb-1">Quality</div>
                                <div className="text-lg font-bold text-blue-500">{trade_quality}/100</div>
                            </div>
                        </div>
                    )}
                    {isNoTrade && (
                        <div className="text-right">
                            <div className="text-xs text-muted uppercase tracking-wider mb-1">Quality</div>
                            <div className="text-lg font-bold text-blue-500">{trade_quality || 0}/100</div>
                        </div>
                    )}
                </div>

                {!isNoTrade ? (
                    <>
                        <div className="grid grid-cols-2 gap-4 bg-gray-50 dark:bg-gray-800/50 p-4 rounded-lg border border-light-border dark:border-dark-border">
                            <div>
                                <div className="text-xs text-muted mb-1 uppercase tracking-wider">Entry</div>
                                <div className="font-mono text-lg font-semibold">{entry_price?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 5 })}</div>
                            </div>
                            <div>
                                <div className="text-xs text-muted mb-1 uppercase tracking-wider">Stop Loss</div>
                                <div className="font-mono text-lg font-semibold text-market-down">{stop_loss?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 5 })}</div>
                            </div>
                            <div>
                                <div className="text-xs text-muted mb-1 uppercase tracking-wider">Target 1</div>
                                <div className="font-mono text-lg font-semibold text-market-up">{target_1?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 5 })}</div>
                            </div>
                            <div>
                                <div className="text-xs text-muted mb-1 uppercase tracking-wider">Target 2</div>
                                <div className="font-mono text-lg font-semibold text-market-up">{target_2 ? target_2.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 5 }) : '-'}</div>
                            </div>
                        </div>

                        <div className="flex justify-between items-center py-2 border-b border-light-border dark:border-dark-border">
                            <span className="text-sm font-medium text-muted uppercase tracking-wider">Risk/Reward (TP1)</span>
                            <span className="font-mono font-bold">1:{risk_reward_target_1}</span>
                        </div>

                        {invalidation_level && (
                            <div className="bg-red-50 dark:bg-red-900/10 p-3 rounded border border-red-100 dark:border-red-900/30">
                                <span className="text-xs font-bold text-red-600 dark:text-red-400 uppercase tracking-wider block mb-1">Invalidation</span>
                                <span className="text-sm text-red-800 dark:text-red-300">{invalidation_level}</span>
                            </div>
                        )}
                    </>
                ) : (
                    <div className="bg-gray-50 dark:bg-gray-800/50 p-4 rounded-lg border border-light-border dark:border-dark-border">
                        <div className="mb-4">
                            <span className="text-xs font-bold text-muted uppercase tracking-wider block mb-2">Reasons</span>
                            <ul className="list-disc pl-5 text-sm space-y-1 text-light-text dark:text-dark-text">
                                {reasons && reasons.length > 0 ? (
                                    reasons.map((r, i) => <li key={i}>{r}</li>)
                                ) : (
                                    <li>Conditions not met</li>
                                )}
                            </ul>
                        </div>
                        
                        {warnings && warnings.length > 0 && (
                            <div>
                                <span className="text-xs font-bold text-market-warn uppercase tracking-wider block mb-2">Wait for</span>
                                <ul className="list-disc pl-5 text-sm space-y-1 text-light-text dark:text-dark-text">
                                    {warnings.map((w, i) => <li key={i}>{w}</li>)}
                                </ul>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
