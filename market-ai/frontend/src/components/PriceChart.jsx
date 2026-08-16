import React from 'react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine } from 'recharts';

export default function PriceChart({ candleData, strategyData }) {
    if (!candleData || candleData.status === 'DATA_UNAVAILABLE') {
        return (
            <div className="card p-6 mb-6 h-80 flex items-center justify-center text-muted shadow-sm">
                {candleData?.status === 'DATA_UNAVAILABLE' ? 'Chart data unavailable' : 'Loading chart...'}
            </div>
        );
    }

    const data = candleData.candles || [];
    
    // Format timestamp for display depending on timeframe
    const formattedData = data.map(d => ({
        ...d,
        timeLabel: new Date(d.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }));

    // Trade Levels
    let entry, sl, tp1, tp2;
    let hasTrade = false;
    if (strategyData && strategyData.direction && strategyData.direction !== 'NO_TRADE') {
        entry = strategyData.entry_price;
        sl = strategyData.stop_loss;
        tp1 = strategyData.target_1;
        tp2 = strategyData.target_2;
        hasTrade = true;
    }

    return (
        <div className="card p-6 mb-6 shadow-sm">
            <div className="flex justify-between items-center mb-4 border-b border-light-border dark:border-dark-border pb-2">
                <h3 className="text-sm font-bold tracking-wide uppercase text-light-muted dark:text-dark-muted">Price Action</h3>
            </div>
            
            <div className="h-80 w-full">
                {formattedData.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={formattedData} margin={{ top: 10, right: 30, left: 10, bottom: 0 }}>
                            <defs>
                                <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2}/>
                                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.15} vertical={false} />
                            <XAxis 
                                dataKey="timeLabel" 
                                tick={{ fontSize: 11, fill: '#9ca3af' }} 
                                tickLine={false} 
                                axisLine={{ stroke: '#e5e7eb', strokeOpacity: 0.2 }}
                                minTickGap={40}
                            />
                            <YAxis 
                                domain={['auto', 'auto']} 
                                tick={{ fontSize: 11, fill: '#9ca3af' }} 
                                tickLine={false} 
                                axisLine={{ stroke: '#e5e7eb', strokeOpacity: 0.2 }}
                                tickFormatter={(val) => val.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 5 })}
                                orientation="right"
                            />
                            <Tooltip 
                                contentStyle={{ backgroundColor: 'var(--tw-bg-opacity, #ffffff)', borderColor: '#e2e8f0', borderRadius: '0.375rem', boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)' }}
                                itemStyle={{ color: '#0f172a', fontWeight: 600 }}
                                labelStyle={{ color: '#64748b' }}
                            />
                            <Area type="monotone" dataKey="close" stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill="url(#colorPrice)" />
                            
                            {hasTrade && entry && (
                                <ReferenceLine y={entry} stroke="#3b82f6" strokeDasharray="3 3" label={{ position: 'left', value: 'ENTRY', fill: '#3b82f6', fontSize: 10, fontWeight: 700 }} />
                            )}
                            {hasTrade && sl && (
                                <ReferenceLine y={sl} stroke="#ef4444" strokeDasharray="3 3" label={{ position: 'left', value: 'SL', fill: '#ef4444', fontSize: 10, fontWeight: 700 }} />
                            )}
                            {hasTrade && tp1 && (
                                <ReferenceLine y={tp1} stroke="#10b981" strokeDasharray="3 3" label={{ position: 'left', value: 'TP1', fill: '#10b981', fontSize: 10, fontWeight: 700 }} />
                            )}
                            {hasTrade && tp2 && tp2 !== 0 && (
                                <ReferenceLine y={tp2} stroke="#059669" strokeDasharray="3 3" label={{ position: 'left', value: 'TP2', fill: '#059669', fontSize: 10, fontWeight: 700 }} />
                            )}
                        </AreaChart>
                    </ResponsiveContainer>
                ) : (
                    <div className="h-full flex items-center justify-center text-muted">No candle data available</div>
                )}
            </div>
        </div>
    );
}
