import React, { useEffect } from 'react';
import { Moon, Sun } from 'lucide-react';

export default function Header({ darkMode, setDarkMode }) {
    // Persist theme using localStorage
    useEffect(() => {
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark') {
            setDarkMode(true);
        } else if (savedTheme === 'light') {
            setDarkMode(false);
        }
    }, [setDarkMode]);

    const toggleTheme = () => {
        const newTheme = !darkMode;
        setDarkMode(newTheme);
        localStorage.setItem('theme', newTheme ? 'dark' : 'light');
    };

    return (
        <header className="flex items-center justify-between p-4 border-b border-light-border dark:border-dark-border bg-light-card dark:bg-dark-card transition-colors duration-200">
            <div className="flex flex-col sm:flex-row sm:items-baseline gap-1 sm:gap-4">
                <h1 className="text-xl font-bold tracking-tight text-light-text dark:text-dark-text">MARKET AI</h1>
                <span className="text-xs sm:text-sm text-light-muted dark:text-dark-muted font-medium">Real-Time Market Intelligence</span>
            </div>
            <div className="flex items-center gap-4 sm:gap-6">
                <div className="flex items-center gap-2">
                    <span className="relative flex h-3 w-3">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
                    </span>
                    <span className="text-xs font-bold tracking-widest text-green-500 hidden sm:inline-block">LIVE</span>
                </div>
                <button 
                    onClick={toggleTheme}
                    className="p-2 rounded hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-light-text dark:text-dark-text"
                >
                    {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
                </button>
            </div>
        </header>
    );
}
