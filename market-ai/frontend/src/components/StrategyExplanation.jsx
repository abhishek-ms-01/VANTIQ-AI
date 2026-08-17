import React from 'react';

export default function StrategyExplanation({ strategyData }) {
    if (!strategyData) return null;

    const {
        market_regime,
        reasons,
        warnings,
        invalidation_level,
        strategy_name = 'AlphaTrend Pro',
        ai_evaluation
    } = strategyData;

    return (
        <div className="card p-4 mb-4 shadow-sm h-full">
            <h3 className="text-xs font-bold mb-3 border-b border-light-border dark:border-dark-border pb-2 tracking-wide uppercase text-light-muted dark:text-dark-muted flex justify-between">
                <span>Strategy Analysis</span>
                <span className="text-blue-500 font-black">{strategy_name}</span>
            </h3>
            
            <div className="space-y-4 text-xs text-light-text dark:text-dark-text">
                
                {/* LIVE NEURAL ENGINE VIEW */}
                {ai_evaluation && Object.keys(ai_evaluation).length > 0 && (
                    <div className="bg-gray-900 rounded p-3 text-white shadow-inner font-mono relative overflow-hidden">
                        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 via-purple-500 to-blue-500 opacity-50"></div>
                        <div className="flex justify-between items-center mb-3">
                            <span className="font-bold text-[10px] uppercase tracking-widest text-blue-400">Live AI Evaluation</span>
                            <span className="flex h-2 w-2 relative">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
                            </span>
                        </div>

                        {/* Conviction Meters */}
                        <div className="space-y-2 mb-3">
                            <div>
                                <div className="flex justify-between text-[9px] mb-1 text-gray-400">
                                    <span>LONG CONVICTION</span>
                                    <span>{ai_evaluation.long_score}%</span>
                                </div>
                                <div className="w-full bg-gray-800 rounded-full h-1.5">
                                    <div className="bg-green-500 h-1.5 rounded-full transition-all duration-500" style={{ width: `${Math.min(ai_evaluation.long_score, 100)}%` }}></div>
                                </div>
                            </div>
                            <div>
                                <div className="flex justify-between text-[9px] mb-1 text-gray-400">
                                    <span>SHORT CONVICTION</span>
                                    <span>{ai_evaluation.short_score}%</span>
                                </div>
                                <div className="w-full bg-gray-800 rounded-full h-1.5">
                                    <div className="bg-red-500 h-1.5 rounded-full transition-all duration-500" style={{ width: `${Math.min(ai_evaluation.short_score, 100)}%` }}></div>
                                </div>
                            </div>
                        </div>

                        {/* Condition Matrix */}
                        <div className="grid grid-cols-2 gap-x-2 gap-y-1 mt-2 text-[9px] border-t border-gray-800 pt-2">
                            {Object.entries(ai_evaluation.long_cond || {}).slice(0, 4).map(([key, passed]) => (
                                <div key={`l_${key}`} className="flex items-center gap-1">
                                    <span className={`w-1.5 h-1.5 rounded-full ${passed ? 'bg-green-500' : 'bg-gray-700'}`}></span>
                                    <span className={`uppercase truncate ${passed ? 'text-gray-300' : 'text-gray-600'}`}>L: {key.replace('_', ' ')}</span>
                                </div>
                            ))}
                            {Object.entries(ai_evaluation.short_cond || {}).slice(0, 4).map(([key, passed]) => (
                                <div key={`s_${key}`} className="flex items-center gap-1">
                                    <span className={`w-1.5 h-1.5 rounded-full ${passed ? 'bg-red-500' : 'bg-gray-700'}`}></span>
                                    <span className={`uppercase truncate ${passed ? 'text-gray-300' : 'text-gray-600'}`}>S: {key.replace('_', ' ')}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                <div className="flex justify-between items-center bg-gray-50 dark:bg-gray-800/50 p-2 rounded border border-light-border dark:border-dark-border">
                    <span className="font-bold text-muted uppercase tracking-wider">Regime</span>
                    <span className="font-bold tracking-wide">{market_regime || 'UNKNOWN'}</span>
                </div>

                <div>
                    <div className="font-bold text-muted uppercase tracking-wider mb-1">Signal Output</div>
                    <ul className="list-disc pl-4 space-y-0.5 text-light-muted dark:text-dark-muted">
                        {reasons && reasons.length > 0 ? (
                            reasons.map((r, i) => <li key={i}>{r}</li>)
                        ) : (
                            <li>Waiting for threshold confirmation.</li>
                        )}
                    </ul>
                </div>

                {invalidation_level && (
                    <div>
                        <div className="font-bold text-muted uppercase tracking-wider mb-1">Invalidation</div>
                        <div className="text-red-700 dark:text-red-400 font-medium">
                            {invalidation_level}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
