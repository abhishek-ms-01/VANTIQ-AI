// Use local backend for development, and Render for production
const API_BASE_URL = import.meta.env.DEV 
    ? 'http://localhost:8000/api' 
    : 'https://vantiq-ai.onrender.com/api';

export const fetchHealth = async () => {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (!response.ok) throw new Error('Network error');
    return response.json();
};

export const fetchAssets = async () => {
    const response = await fetch(`${API_BASE_URL}/assets`);
    if (!response.ok) throw new Error('Network error');
    return response.json();
};

export const fetchMarket = async (asset) => {
    const response = await fetch(`${API_BASE_URL}/market/${asset}`);
    if (!response.ok) throw new Error('Network error');
    return response.json();
};

export const fetchCandles = async (asset, timeframe) => {
    const response = await fetch(`${API_BASE_URL}/candles/${asset}/${timeframe}`);
    if (!response.ok) throw new Error('Network error');
    return response.json();
};

export const fetchAnalysis = async (asset) => {
    const response = await fetch(`${API_BASE_URL}/analysis/${asset}`);
    if (!response.ok) throw new Error('Network error');
    return response.json();
};

export const fetchStrategy = async (asset) => {
    const response = await fetch(`${API_BASE_URL}/strategy/${asset}`);
    if (!response.ok) throw new Error('Network error');
    return response.json();
};
