import React from 'react';

export default function AssetSelector({ assets, activeAsset, setActiveAsset }) {
    return (
        <div className="flex flex-wrap gap-3 mb-8">
            {assets.map(asset => (
                <button
                    key={asset.id}
                    className={`px-4 py-2 text-sm font-bold tracking-wide rounded-md transition-all duration-200 border shadow-sm ${
                        activeAsset === asset.id 
                        ? 'bg-light-text text-light-bg dark:bg-dark-text dark:text-dark-bg border-transparent' 
                        : 'bg-light-card text-light-text dark:bg-dark-card dark:text-dark-text border-light-border dark:border-dark-border hover:bg-gray-100 dark:hover:bg-gray-800'
                    }`}
                    onClick={() => setActiveAsset(asset.id)}
                >
                    {asset.display_name}
                </button>
            ))}
            {assets.length === 0 && <span className="text-sm text-muted py-2">No assets found for this market</span>}
        </div>
    );
}
