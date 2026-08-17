import React, { useState, useEffect } from 'react';

export default function SessionTracker() {
    const [sessions, setSessions] = useState({ current: [], previous: null, next: null });
    const [currentTime, setCurrentTime] = useState(new Date());

    useEffect(() => {
        const calculateSessions = () => {
            const now = new Date();
            setCurrentTime(now);
            
            const currentHourUTC = now.getUTCHours();
            
            const allSessions = [
                { name: 'Sydney', startUTC: 22, endUTC: 7 },
                { name: 'Tokyo', startUTC: 0, endUTC: 9 },
                { name: 'London', startUTC: 8, endUTC: 17 },
                { name: 'New York', startUTC: 13, endUTC: 22 }
            ];
            
            // Format time helper (local timezone)
            const getLocalTime = (utcHour) => {
                const d = new Date();
                d.setUTCHours(utcHour, 0, 0, 0);
                return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            };

            const enriched = allSessions.map(s => {
                let isActive = false;
                if (s.startUTC > s.endUTC) { // Crosses midnight
                    isActive = currentHourUTC >= s.startUTC || currentHourUTC < s.endUTC;
                } else {
                    isActive = currentHourUTC >= s.startUTC && currentHourUTC < s.endUTC;
                }
                
                // Calculate hours until start/end
                let hoursToStart = s.startUTC - currentHourUTC;
                if (hoursToStart < 0) hoursToStart += 24;
                
                let hoursSinceEnd = currentHourUTC - s.endUTC;
                if (hoursSinceEnd < 0) hoursSinceEnd += 24;
                
                return {
                    ...s,
                    isActive,
                    hoursToStart,
                    hoursSinceEnd,
                    localStart: getLocalTime(s.startUTC),
                    localEnd: getLocalTime(s.endUTC)
                };
            });
            
            const current = enriched.filter(s => s.isActive);
            const inactive = enriched.filter(s => !s.isActive);
            
            // Previous is the one that ended most recently (lowest hoursSinceEnd)
            inactive.sort((a, b) => a.hoursSinceEnd - b.hoursSinceEnd);
            const previous = inactive.length > 0 ? inactive[0] : null;
            
            // Next is the one that starts soonest (lowest hoursToStart)
            inactive.sort((a, b) => a.hoursToStart - b.hoursToStart);
            const next = inactive.length > 0 ? inactive[0] : null;
            
            setSessions({ current, previous, next });
        };

        calculateSessions();
        const interval = setInterval(calculateSessions, 60000); // Update every minute
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="card p-4 mb-6 shadow-sm">
            <div className="flex justify-between items-center mb-3 border-b border-light-border dark:border-dark-border pb-2">
                <h3 className="text-xs font-bold tracking-wide uppercase text-light-muted dark:text-dark-muted">Forex Sessions</h3>
                <span className="text-[10px] font-mono bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 px-1.5 py-0.5 rounded">
                    {currentTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
            </div>
            
            <div className="flex flex-col gap-2">
                {/* Current */}
                <div className="p-2.5 rounded bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 shadow-inner flex justify-between items-center">
                    <div>
                        <div className="text-[10px] font-bold text-blue-600 dark:text-blue-400 uppercase tracking-wider flex items-center gap-1.5">
                            <span className="relative flex h-1.5 w-1.5">
                              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                              <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-blue-500"></span>
                            </span>
                            Active Now
                        </div>
                        {sessions.current.length > 0 ? (
                            sessions.current.map(s => (
                                <div key={s.name} className="flex items-baseline gap-2">
                                    <span className="text-sm font-black text-blue-700 dark:text-blue-300">{s.name}</span>
                                    <span className="text-xs font-mono text-blue-600/70 dark:text-blue-400/70">{s.localStart}-{s.localEnd}</span>
                                </div>
                            ))
                        ) : (
                            <div className="text-xs text-gray-500 mt-0.5">Between Sessions</div>
                        )}
                    </div>
                </div>

                {/* Next */}
                <div className="p-2.5 rounded bg-gray-50 dark:bg-gray-800/30 border border-gray-100 dark:border-gray-800 flex justify-between items-center">
                    <div>
                        <div className="text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-0.5">Coming Next</div>
                        {sessions.next ? (
                            <div className="flex items-baseline gap-2">
                                <span className="text-sm font-bold">{sessions.next.name}</span>
                                <span className="text-xs font-mono text-gray-500">{sessions.next.localStart}</span>
                            </div>
                        ) : (
                            <div className="text-xs text-gray-500">None</div>
                        )}
                    </div>
                </div>

                {/* Previous */}
                <div className="p-2.5 rounded bg-gray-50 dark:bg-gray-800/30 border border-gray-100 dark:border-gray-800 opacity-60 flex justify-between items-center">
                    <div>
                        <div className="text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-0.5">Previous</div>
                        {sessions.previous ? (
                            <div className="flex items-baseline gap-2">
                                <span className="text-sm font-bold">{sessions.previous.name}</span>
                                <span className="text-xs font-mono text-gray-500">closed {sessions.previous.localEnd}</span>
                            </div>
                        ) : (
                            <div className="text-xs text-gray-500">None</div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
