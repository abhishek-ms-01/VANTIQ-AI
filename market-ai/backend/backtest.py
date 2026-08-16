import pandas as pd
import numpy as np
from typing import Dict, Any, List
from risk.trade_validation import validate_and_build_trade_plan
import warnings
warnings.filterwarnings('ignore')

class BacktestEngine:
    def __init__(self, strategy, name: str, data_dict: Dict[str, pd.DataFrame]):
        self.strategy = strategy
        self.name = name
        self.data_dict = data_dict
        self.results = []
        
        # Determine the base timeframe (the smallest one)
        self.timeframes = strategy.timeframes
        # e.g., ['5M', '15M', '1H']. Usually the first is the entry timeframe.
        self.base_tf = self.timeframes[0]
        
    def _split_data(self, df: pd.DataFrame, split_type: str) -> pd.DataFrame:
        n = len(df)
        train_end = int(n * 0.6)
        val_end = int(n * 0.8)
        
        if split_type == 'TRAIN':
            return df.iloc[:train_end]
        elif split_type == 'VALIDATION':
            return df.iloc[train_end:val_end]
        elif split_type == 'TEST':
            return df.iloc[val_end:]
        return df

    def run_backtest(self, split_type: str = 'TEST'):
        # Split all timeframes
        split_data = {}
        for tf in self.timeframes:
            if tf in self.data_dict and not self.data_dict[tf].empty:
                split_data[tf] = self._split_data(self.data_dict[tf], split_type)
            else:
                split_data[tf] = pd.DataFrame()
                
        base_df = split_data[self.base_tf]
        if base_df.empty:
            return self._empty_metrics()
            
        # Pre-calculate indicators to save time during loop
        split_data = self.strategy.calculate_indicators(split_data)
        
        trades = []
        no_trade_count = 0
        total_signals = 0
        
        # We need enough history for indicators to warm up (e.g., 200 periods)
        warmup = 200
        if len(base_df) <= warmup:
            return self._empty_metrics()
            
        # We simulate chronologically
        timestamps = base_df.index
        
        for i in range(warmup, len(timestamps) - 1): # leaving at least 1 candle for future
            current_time = timestamps[i]
            
            # Slice data exactly up to current_time to prevent lookahead
            current_data = {}
            for tf in self.timeframes:
                df = split_data[tf]
                if not df.empty:
                    # Ensure both are tz-naive or tz-aware for comparison
                    if df.index.tz is not None and current_time.tz is None:
                        current_time_cmp = current_time.tz_localize(df.index.tz)
                    elif df.index.tz is None and current_time.tz is not None:
                        current_time_cmp = current_time.tz_localize(None)
                    else:
                        current_time_cmp = current_time
                    
                    sliced = df[df.index <= current_time_cmp]
                    current_data[tf] = sliced
                else:
                    current_data[tf] = df
                    
            raw_signal = self.strategy.generate_signal(current_data)
            total_signals += 1
            
            if raw_signal.get("direction", "NO_TRADE") == "NO_TRADE":
                no_trade_count += 1
                continue
                
            # Validate trade
            plan = validate_and_build_trade_plan(
                raw_signal=raw_signal,
                data_df=current_data[self.base_tf],
                atr_multiplier=1.5,
                min_rr=1.2
            )
            
            if plan.get("direction", "NO_TRADE") == "NO_TRADE":
                no_trade_count += 1
                continue
                
            # If trade is valid, simulate forward to see outcome
            entry_price = plan["entry_price"]
            sl = plan["stop_loss"]
            tp1 = plan["target_1"]
            tp2 = plan["target_2"]
            direction = plan["direction"]
            
            # Look at future candles in the base timeframe
            future_df = base_df.iloc[i+1:]
            
            outcome = "OPEN"
            exit_price = 0.0
            tp1_hit = False
            tp2_hit = False
            
            for j in range(len(future_df)):
                row = future_df.iloc[j]
                high = row['high']
                low = row['low']
                
                if direction == "LONG":
                    if low <= sl:
                        exit_price = sl
                        outcome = "LOSS"
                        break
                    elif high >= tp1 and not tp1_hit:
                        tp1_hit = True
                        if tp2 == 0.0:
                            exit_price = tp1
                            outcome = "WIN"
                            break
                        else:
                            # Move SL to breakeven if TP1 hit
                            sl = entry_price 
                    elif high >= tp2 and tp1_hit:
                        tp2_hit = True
                        exit_price = tp2
                        outcome = "WIN"
                        break
                        
                elif direction == "SHORT":
                    if high >= sl:
                        exit_price = sl
                        outcome = "LOSS"
                        break
                    elif low <= tp1 and not tp1_hit:
                        tp1_hit = True
                        if tp2 == 0.0:
                            exit_price = tp1
                            outcome = "WIN"
                            break
                        else:
                            sl = entry_price
                    elif low <= tp2 and tp1_hit:
                        tp2_hit = True
                        exit_price = tp2
                        outcome = "WIN"
                        break
                        
            if outcome != "OPEN":
                profit = (exit_price - entry_price) if direction == "LONG" else (entry_price - exit_price)
                risk = abs(entry_price - plan["stop_loss"]) # Initial risk
                r_multiple = profit / risk if risk > 0 else 0
                
                trades.append({
                    "time": current_time,
                    "direction": direction,
                    "entry": entry_price,
                    "exit": exit_price,
                    "outcome": outcome,
                    "profit": profit,
                    "r_multiple": r_multiple,
                    "tp1_hit": tp1_hit,
                    "tp2_hit": tp2_hit,
                    "regime": plan.get("market_regime", "UNKNOWN")
                })
                
        return self._calculate_metrics(trades, total_signals, no_trade_count)

    def _empty_metrics(self):
        return {
            "total_signals": 0, "total_trades": 0, "no_trade_count": 0,
            "win_rate": 0.0, "loss_rate": 0.0, "profit_factor": 0.0,
            "expectancy": 0.0, "average_r": 0.0, "tp1_hit_rate": 0.0,
            "tp2_hit_rate": 0.0, "sl_hit_rate": 0.0, "max_drawdown": 0.0,
            "average_trade_return": 0.0, "largest_win": 0.0, "largest_loss": 0.0,
            "directional_accuracy": 0.0
        }

    def _calculate_metrics(self, trades: List[Dict], total_signals: int, no_trade_count: int) -> Dict[str, Any]:
        if not trades:
            metrics = self._empty_metrics()
            metrics["total_signals"] = total_signals
            metrics["no_trade_count"] = no_trade_count
            return metrics
            
        total_trades = len(trades)
        wins = [t for t in trades if t["outcome"] == "WIN" or t["profit"] > 0]
        losses = [t for t in trades if t["outcome"] == "LOSS" or t["profit"] < 0]
        
        win_rate = len(wins) / total_trades * 100
        loss_rate = len(losses) / total_trades * 100
        
        gross_profit = sum(t["profit"] for t in wins)
        gross_loss = abs(sum(t["profit"] for t in losses))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        avg_r = sum(t["r_multiple"] for t in trades) / total_trades
        expectancy = avg_r # In R multiples
        
        tp1_hits = sum(1 for t in trades if t["tp1_hit"])
        tp2_hits = sum(1 for t in trades if t["tp2_hit"])
        sl_hits = sum(1 for t in trades if t["outcome"] == "LOSS")
        
        tp1_hit_rate = tp1_hits / total_trades * 100
        tp2_hit_rate = tp2_hits / total_trades * 100
        sl_hit_rate = sl_hits / total_trades * 100
        
        # Max Drawdown (in terms of cumulative R)
        cumulative_r = np.cumsum([t["r_multiple"] for t in trades])
        peak = np.maximum.accumulate(cumulative_r)
        drawdown = peak - cumulative_r
        max_drawdown = np.max(drawdown) if len(drawdown) > 0 else 0.0
        
        avg_return = sum(t["profit"] for t in trades) / total_trades
        largest_win = max([t["profit"] for t in trades] + [0])
        largest_loss = min([t["profit"] for t in trades] + [0])
        
        # Directional Accuracy (percentage of trades where TP1 was hit at least, showing correct direction)
        directional_accuracy = tp1_hit_rate
        
        return {
            "total_signals": total_signals,
            "total_trades": total_trades,
            "no_trade_count": no_trade_count,
            "directional_accuracy": round(directional_accuracy, 2),
            "win_rate": round(win_rate, 2),
            "loss_rate": round(loss_rate, 2),
            "profit_factor": round(profit_factor, 2),
            "expectancy": round(expectancy, 2),
            "average_r": round(avg_r, 2),
            "tp1_hit_rate": round(tp1_hit_rate, 2),
            "tp2_hit_rate": round(tp2_hit_rate, 2),
            "sl_hit_rate": round(sl_hit_rate, 2),
            "max_drawdown": round(max_drawdown, 2),
            "average_trade_return": round(avg_return, 2),
            "largest_win": round(largest_win, 2),
            "largest_loss": round(largest_loss, 2)
        }
