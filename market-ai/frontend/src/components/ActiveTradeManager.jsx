import React, { useState, useEffect } from 'react';
import { fetchTradeGuardian } from '../api';

export default function ActiveTradeManager({ marketData, strategyData }) {
    const [activeTrade, setActiveTrade] = useState(null);
    const [isFormOpen, setIsFormOpen] = useState(false);
    
    // Guardian State
    const [guardianData, setGuardianData] = useState(null);
    const [guardianLoading, setGuardianLoading] = useState(false);
    
    // Form state
    const [entryPrice, setEntryPrice] = useState('');
    const [direction, setDirection] = useState('LONG');

    // Load from local storage on mount
    useEffect(() => {
        const saved = localStorage.getItem('vantiq_active_trade');
        if (saved) {
            setActiveTrade(JSON.parse(saved));
        }
    }, []);

    // Save to local storage on change
    useEffect(() => {
        if (activeTrade) {
            localStorage.setItem('vantiq_active_trade', JSON.stringify(activeTrade));
        } else {
            localStorage.removeItem('vantiq_active_trade');
            setGuardianData(null);
        }
    }, [activeTrade]);

    // Poll Trade Guardian
    useEffect(() => {
        if (!activeTrade || !marketData?.asset) return;
        
        const fetchGuardian = async () => {
            try {
                const data = await fetchTradeGuardian(marketData.asset, {
                    direction: activeTrade.direction,
                    entry: activeTrade.entryPrice,
                    sl: activeTrade.stopLoss,
                    tp: activeTrade.takeProfit
                });
                setGuardianData(data);
            } catch (e) {
                console.error("Trade Guardian Error:", e);
            }
        };

        fetchGuardian();
        const interval = setInterval(fetchGuardian, 10000); // Poll every 10s
        return () => clearInterval(interval);
    }, [activeTrade, marketData?.asset, marketData?.price]); // Re-run when price updates slightly

    // Update form defaults when opening
    const handleOpenForm = () => {
        setEntryPrice(marketData?.price ? marketData.price.toString() : '');
        setDirection(strategyData?.direction === 'SHORT' ? 'SHORT' : 'LONG');
        setIsFormOpen(true);
    };

    const handleTakeTrade = (e) => {
        e.preventDefault();
        if (!entryPrice || isNaN(parseFloat(entryPrice))) return;

        // Automatically set initial Stop Loss and Take Profit based on ATR if available, else simple %
        const price = parseFloat(entryPrice);
        const atr = strategyData?.atr ? parseFloat(strategyData.atr) : price * 0.005; // Fallback 0.5%
        
        let sl, tp;
        if (direction === 'LONG') {
            sl = strategyData?.stop_loss || (price - (atr * 1.5));
            tp = strategyData?.target_1 || (price + (atr * 2.0));
        } else {
            sl = strategyData?.stop_loss || (price + (atr * 1.5));
            tp = strategyData?.target_1 || (price - (atr * 2.0));
        }

        const newTrade = {
            direction,
            entryPrice: price,
            stopLoss: sl,
            takeProfit: tp,
            timestamp: new Date().toISOString()
        };
        
        setActiveTrade(newTrade);
        setIsFormOpen(false);
    };

    const handleCloseTrade = () => {
        if (window.confirm("Are you sure you want to close the active trade?")) {
            setActiveTrade(null);
        }
    };

    // Calculate live PnL
    const currentPrice = marketData?.price;
    let pnl = 0;
    let pnlPercentage = 0;
    
    if (activeTrade && currentPrice) {
        if (activeTrade.direction === 'LONG') {
            pnl = currentPrice - activeTrade.entryPrice;
        } else {
            pnl = activeTrade.entryPrice - currentPrice;
        }
        pnlPercentage = (pnl / activeTrade.entryPrice) * 100;
    }

    const isProfit = pnl >= 0;
    const pnlColor = isProfit ? 'text-green-500' : 'text-red-500';

    if (!activeTrade && !isFormOpen) {
        return (
            <button 
                onClick={handleOpenForm}
                className="w-full py-2 mb-4 bg-transparent hover:bg-blue-600/10 dark:hover:bg-blue-900/30 text-blue-600 dark:text-blue-400 border-2 border-dashed border-blue-300 dark:border-blue-800 font-bold rounded transition-colors uppercase tracking-wider text-xs"
            >
                + Enter Active Trade
            </button>
        );
    }

    if (isFormOpen && !activeTrade) {
        return (
            <div className="card p-4 mb-4 shadow-sm border border-blue-200 dark:border-blue-900/50 relative">
                <h3 className="text-sm font-bold mb-3 border-b border-light-border dark:border-dark-border pb-2 tracking-wide uppercase">
                    New Active Trade
                </h3>
                <form onSubmit={handleTakeTrade} className="flex flex-col gap-3">
                    <div>
                        <label className="text-xs font-bold text-muted uppercase tracking-wider block mb-1">Direction</label>
                        <select 
                            value={direction} 
                            onChange={(e) => setDirection(e.target.value)}
                            className="w-full p-2 bg-gray-50 dark:bg-gray-800 border border-light-border dark:border-dark-border rounded text-sm font-bold"
                        >
                            <option value="LONG">LONG (Buy)</option>
                            <option value="SHORT">SHORT (Sell)</option>
                        </select>
                    </div>
                    <div>
                        <label className="text-xs font-bold text-muted uppercase tracking-wider block mb-1">Entry Price</label>
                        <input 
                            type="number" 
                            step="0.0001"
                            required
                            value={entryPrice} 
                            onChange={(e) => setEntryPrice(e.target.value)}
                            className="w-full p-2 bg-gray-50 dark:bg-gray-800 border border-light-border dark:border-dark-border rounded font-mono text-sm"
                        />
                    </div>
                    <div className="flex gap-2 mt-2">
                        <button type="submit" className="flex-1 py-2 bg-green-600 hover:bg-green-700 text-white font-bold rounded text-xs uppercase tracking-wide">
                            Start Tracking
                        </button>
                        <button type="button" onClick={() => setIsFormOpen(false)} className="flex-1 py-2 bg-gray-300 dark:bg-gray-700 hover:bg-gray-400 dark:hover:bg-gray-600 font-bold rounded text-xs uppercase tracking-wide">
                            Cancel
                        </button>
                    </div>
                </form>
            </div>
        );
    }

    return (
        <div className="card p-4 mb-4 shadow-sm border-2 border-blue-500 dark:border-blue-600 relative overflow-hidden bg-[#0a0a0c]">
            {/* Background Glow */}
            <div className={`absolute -top-10 -right-10 w-32 h-32 rounded-full blur-3xl opacity-20 ${isProfit ? 'bg-green-500' : 'bg-red-500'}`}></div>
            
            <div className="flex justify-between items-center mb-3 border-b border-light-border dark:border-gray-800 pb-2">
                <h3 className="text-xs font-bold tracking-wide uppercase flex items-center gap-2 text-white">
                    <span className="relative flex h-2 w-2">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
                    </span>
                    Trade Guardian AI
                </h3>
                <span className={`text-xs font-black px-2 py-0.5 rounded ${activeTrade.direction === 'LONG' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'}`}>
                    {activeTrade.direction}
                </span>
            </div>

            <div className="grid grid-cols-2 gap-3 mb-3">
                <div className="bg-[#111116] p-2 rounded border border-gray-800">
                    <div className="text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-0.5">Entry</div>
                    <div className="font-mono text-sm font-semibold text-white">{activeTrade.entryPrice.toFixed(3)}</div>
                </div>
                <div className="bg-[#111116] p-2 rounded border border-gray-800">
                    <div className="text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-0.5">Current</div>
                    <div className="font-mono text-sm font-semibold text-white">{currentPrice ? currentPrice.toFixed(3) : '---'}</div>
                </div>
            </div>

            <div className="mb-4">
                <div className="text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-1 text-center">Live P/L</div>
                <div className={`text-center font-mono text-2xl font-black tracking-tight ${pnlColor}`}>
                    {pnl >= 0 ? '+' : ''}{pnl.toFixed(2)} 
                    <span className="text-sm ml-1 opacity-80">({pnl >= 0 ? '+' : ''}{pnlPercentage.toFixed(2)}%)</span>
                </div>
            </div>

            {/* AI Trade Guardian Copilot UI */}
            {guardianData && (
                <div className="mb-4 bg-[#111116] border border-gray-800 p-3 rounded">
                    <div className="flex justify-between text-[10px] font-bold uppercase tracking-wider mb-2">
                        <span className="text-gray-400">Success Probability</span>
                        <span className={guardianData.probability > 60 ? 'text-green-400' : guardianData.probability < 40 ? 'text-red-400' : 'text-yellow-400'}>
                            {guardianData.probability}%
                        </span>
                    </div>
                    <div className="w-full bg-gray-800 rounded-full h-1.5 mb-3">
                        <div 
                            className={`h-1.5 rounded-full transition-all duration-1000 ${guardianData.probability > 60 ? 'bg-green-500' : guardianData.probability < 40 ? 'bg-red-500' : 'bg-yellow-500'}`} 
                            style={{ width: `${guardianData.probability}%` }}
                        ></div>
                    </div>
                    
                    <div className="text-[10px] font-mono space-y-1.5">
                        <div className="flex items-start gap-2">
                            <span className="text-blue-500 mt-0.5">🤖</span>
                            <span className="text-gray-300">
                                <strong className="text-blue-400 mr-1">[{guardianData.action}]</strong>
                                {guardianData.hints[0]}
                            </span>
                        </div>
                        {guardianData.hints.length > 1 && (
                            <div className="flex items-start gap-2">
                                <span className="text-yellow-500 mt-0.5">⚠️</span>
                                <span className="text-gray-400">{guardianData.hints[1]}</span>
                            </div>
                        )}
                    </div>
                </div>
            )}

            <div className="flex justify-between items-center text-xs font-mono border-t border-gray-800 pt-3 mb-3">
                <div className="text-red-500">
                    <span className="font-sans font-bold uppercase text-[9px] block text-gray-500">SL</span>
                    {activeTrade.stopLoss.toFixed(3)}
                </div>
                <div className="text-green-500 text-right">
                    <span className="font-sans font-bold uppercase text-[9px] block text-gray-500">TP</span>
                    {activeTrade.takeProfit.toFixed(3)}
                </div>
            </div>

            <button 
                onClick={handleCloseTrade}
                className="w-full py-2 border border-red-900/50 text-red-500 hover:bg-red-900/20 font-bold rounded text-xs uppercase tracking-wider transition-colors"
            >
                Close Position
            </button>
        </div>
    );
}
