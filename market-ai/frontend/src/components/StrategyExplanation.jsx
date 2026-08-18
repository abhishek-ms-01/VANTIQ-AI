import React, { useState, useEffect, useRef } from 'react';

export default function StrategyExplanation({ strategyData, marketData, analysisData }) {
    const [logs, setLogs] = useState([]);
    const containerRef = useRef(null);

    // Initial boot sequence
    useEffect(() => {
        setLogs([
            `[${new Date().toLocaleTimeString([], { hour12: false })}] 🟢 SYSTEM BOOT: VANTIQ ENGINE ONLINE`,
            `[${new Date().toLocaleTimeString([], { hour12: false })}] 📡 INITIALIZING WEBSOCKET STREAMS...`
        ]);
    }, []);

    useEffect(() => {
        if (!marketData || marketData.status === 'error' || marketData.status === 'DATA_UNAVAILABLE') return;
        const timeStr = new Date().toLocaleTimeString([], { hour12: false });
        const priceLog = `[${timeStr}] 📡 ${marketData.asset} TICK: $${marketData.price}`;
        
        setLogs(prev => {
            const newLogs = [...prev, priceLog];
            return newLogs.length > 50 ? newLogs.slice(newLogs.length - 50) : newLogs;
        });
    }, [marketData]);

    useEffect(() => {
        if (!analysisData || analysisData.status === 'error' || analysisData.status === 'DATA_UNAVAILABLE') return;
        const timeStr = new Date().toLocaleTimeString([], { hour12: false });
        const emaLog = `[${timeStr}] 📊 CALCULATING 15M EMA: ${analysisData.ema} | RSI: ${analysisData.rsi} | VWAP: ${analysisData.vwap}`;
        
        setLogs(prev => {
            const newLogs = [...prev, emaLog];
            return newLogs.length > 50 ? newLogs.slice(newLogs.length - 50) : newLogs;
        });
    }, [analysisData]);

    useEffect(() => {
        if (!strategyData || strategyData.status === 'error') return;
        const timeStr = new Date().toLocaleTimeString([], { hour12: false });
        const regimeLog = `[${timeStr}] ⚙️ REGIME LOCK: ${strategyData.market_regime || 'UNKNOWN'}`;
        const reason = strategyData.reasons ? strategyData.reasons[0] : 'Scanning...';
        const directionLog = `[${timeStr}] 🔴 STATUS: ${strategyData.direction || 'NO_TRADE'} - ${reason}`;
        
        setLogs(prev => {
            const newLogs = [...prev, regimeLog, directionLog];
            return newLogs.length > 50 ? newLogs.slice(newLogs.length - 50) : newLogs;
        });
    }, [strategyData]);

    // Fast ticking effect for realism (24/7 scanning)
    useEffect(() => {
        const interval = setInterval(() => {
            const now = new Date();
            const timeStr = now.toLocaleTimeString([], { hour12: false });
            const ms = Math.floor(Math.random() * 999).toString().padStart(3, '0');
            const items = [
                "Scanning Order Book Liquidity...", 
                "Cross-referencing multi-timeframe divergence...", 
                "Awaiting high-probability convergence...",
                "Monitoring institutional volume nodes..."
            ];
            const item = items[Math.floor(Math.random() * items.length)];
            
            setLogs(prev => {
                const newLogs = [...prev, `[${timeStr}.${ms}] ⚡ ${item}`];
                return newLogs.length > 50 ? newLogs.slice(newLogs.length - 50) : newLogs;
            });
        }, 1500); // 1.5 seconds tick
        return () => clearInterval(interval);
    }, []);

    // Auto-scroll to bottom safely
    useEffect(() => {
        if (containerRef.current) {
            const container = containerRef.current;
            // Only auto-scroll if user is near the bottom (within 100px) or on initial load
            const isNearBottom = container.scrollHeight - container.scrollTop <= container.clientHeight + 100;
            if (isNearBottom || logs.length < 10) {
                container.scrollTop = container.scrollHeight;
            }
        }
    }, [logs]);

    return (
        <div className="card p-0 mb-4 shadow-sm h-full overflow-hidden border border-gray-800 rounded bg-[#0a0a0c]">
            {/* Header */}
            <div className="bg-[#111116] border-b border-gray-800 p-3 flex justify-between items-center">
                <div className="flex items-center gap-2">
                    <span className="flex h-2 w-2 relative">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                    </span>
                    <h3 className="text-xs font-bold tracking-widest uppercase text-green-500">Live AI Terminal</h3>
                </div>
                <span className="text-blue-500 font-black text-xs">{strategyData?.strategy_name || 'GoldStrategy'}</span>
            </div>
            
            {/* Terminal Window */}
            <div 
                ref={containerRef}
                className="p-4 font-mono text-[11px] h-64 overflow-y-auto custom-scrollbar relative"
            >
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-green-500 via-transparent to-transparent opacity-20"></div>
                
                <div className="space-y-1">
                    {logs.map((log, index) => {
                        let colorClass = "text-gray-400";
                        if (log.includes("TICK")) colorClass = "text-blue-400";
                        if (log.includes("CALCULATING")) colorClass = "text-purple-400";
                        if (log.includes("REGIME")) colorClass = "text-yellow-400";
                        if (log.includes("STATUS: NO_TRADE")) colorClass = "text-red-400";
                        if (log.includes("STATUS: LONG") || log.includes("STATUS: SHORT")) colorClass = "text-green-400 font-bold";
                        if (log.includes("SYSTEM BOOT")) colorClass = "text-green-500 font-bold";
                        
                        return (
                            <div key={index} className={`break-words opacity-0 animate-fade-in ${colorClass}`}>
                                {log}
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}
