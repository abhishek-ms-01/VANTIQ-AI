import React from 'react';

export default function MarketTabs({ activeTab, setActiveTab }) {
    const tabs = ['FOREX'];
    return (
        <div className="flex border-b border-light-border dark:border-dark-border mb-6 overflow-x-auto">
            {tabs.map(tab => (
                <button
                    key={tab}
                    className={`px-6 py-3 text-sm font-bold tracking-widest transition-colors border-b-2 whitespace-nowrap ${
                        activeTab === tab 
                        ? 'border-blue-500 text-blue-600 dark:border-blue-400 dark:text-blue-400' 
                        : 'border-transparent text-light-muted dark:text-dark-muted hover:text-light-text dark:hover:text-dark-text'
                    }`}
                    onClick={() => setActiveTab(tab)}
                >
                    {tab}
                </button>
            ))}
        </div>
    );
}
