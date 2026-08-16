import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import MarketTabs from './components/MarketTabs';
import AssetSelector from './components/AssetSelector';
import MarketOverview from './components/MarketOverview';
import PriceChart from './components/PriceChart';
import TradeSignal from './components/TradeSignal';
import TechnicalPanel from './components/TechnicalPanel';
import TimeframePanel from './components/TimeframePanel';
import StrategyExplanation from './components/StrategyExplanation';
import { fetchAssets, fetchMarket, fetchCandles, fetchAnalysis, fetchStrategy } from './api';

export default function App() {
    const [darkMode, setDarkMode] = useState(() => {
        const savedTheme = localStorage.getItem('theme');
        return savedTheme ? savedTheme === 'dark' : true;
    });
    const [activeTab, setActiveTab] = useState('INDIAN');
    const [assets, setAssets] = useState([]);
    const [activeAsset, setActiveAsset] = useState(null);
    const [activeTimeframe, setActiveTimeframe] = useState('15M');
    
    const [marketData, setMarketData] = useState(null);
    const [candleData, setCandleData] = useState(null);
    const [analysisData, setAnalysisData] = useState(null);
    const [strategyData, setStrategyData] = useState(null);

    useEffect(() => {
        if (darkMode) {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
    }, [darkMode]);

    useEffect(() => {
        loadAssets();
    }, []);

    const loadAssets = async () => {
        try {
            const data = await fetchAssets();
            setAssets(data);
        } catch (e) {
            console.error('Failed to load assets', e);
        }
    };

    const filteredAssets = assets.filter(a => a.category === activeTab);
    const currentAssetInfo = assets.find(a => a.id === activeAsset);

    useEffect(() => {
        if (filteredAssets.length > 0) {
            // Select first asset in tab if current is not in it or null
            if (!activeAsset || !filteredAssets.find(a => a.id === activeAsset)) {
                setActiveAsset(filteredAssets[0].id);
            }
        }
    }, [activeTab, filteredAssets]);

    useEffect(() => {
        if (!activeAsset) return;
        
        // Initial load
        setMarketData(null);
        setCandleData(null);
        setAnalysisData(null);
        setStrategyData(null);

        const loadMarket = async () => {
            try {
                const market = await fetchMarket(activeAsset);
                setMarketData(market);
            } catch (e) {
                setMarketData({ status: 'error', error: e });
            }
        };

        const loadStrategyAndAnalysis = async () => {
            try {
                const [analysis, strategy] = await Promise.all([
                    fetchAnalysis(activeAsset).catch(e => null),
                    fetchStrategy(activeAsset).catch(e => null)
                ]);
                setAnalysisData(analysis);
                setStrategyData(strategy);
            } catch (e) {
                console.error('Failed to load strategy', e);
            }
        };

        const loadCandles = async () => {
            if (!activeTimeframe) return;
            try {
                const data = await fetchCandles(activeAsset, activeTimeframe);
                setCandleData(data);
            } catch (e) {
                console.error('Failed to load candles', e);
                setCandleData({ status: 'error' });
            }
        };

        // Fetch immediately
        loadMarket();
        loadStrategyAndAnalysis();
        loadCandles();

        // Polling for live price every 5 seconds
        const priceInterval = setInterval(loadMarket, 5000);

        // Polling for strategy/analysis every 60 seconds
        const strategyInterval = setInterval(() => {
            loadStrategyAndAnalysis();
            loadCandles();
        }, 60000);

        return () => {
            clearInterval(priceInterval);
            clearInterval(strategyInterval);
        };
    }, [activeAsset, activeTimeframe]);

    return (
        <div className="min-h-screen">
            <Header darkMode={darkMode} setDarkMode={setDarkMode} />
            
            <main className="max-w-7xl mx-auto px-4 pb-12">
                <MarketTabs activeTab={activeTab} setActiveTab={setActiveTab} />
                
                <AssetSelector 
                    assets={filteredAssets} 
                    activeAsset={activeAsset} 
                    setActiveAsset={setActiveAsset} 
                />
                
                {activeAsset && currentAssetInfo && (
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        <div className="lg:col-span-2">
                            <MarketOverview marketData={marketData} assetInfo={currentAssetInfo} />
                            
                            <TimeframePanel 
                                timeframes={currentAssetInfo.supported_timeframes}
                                activeTimeframe={activeTimeframe}
                                setActiveTimeframe={setActiveTimeframe}
                            />
                            
                            <PriceChart candleData={candleData} strategyData={strategyData} />
                            
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <TechnicalPanel analysisData={analysisData} />
                                <StrategyExplanation strategyData={strategyData} />
                            </div>
                        </div>
                        
                        <div className="lg:col-span-1">
                            <TradeSignal strategyData={strategyData} />
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}
