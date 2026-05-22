"""信号持久化：写入SQLite数据库"""

import json
from typing import Dict, List, Optional, Any

from src.core.constants import StrategyType
from src.core.database import DatabaseManager
from src.core.logger import setup_logger
from src.strategy_engine.signal import FusedSignal
from src.backtest_engine.backtest_result import BacktestResult, TradeRecord
from src.optimizer.optimization_result import OptimizationResult

logger = setup_logger("signal_persistence")


def _serialize_for_json(obj: Any) -> Any:
    """将对象序列化为JSON兼容格式，处理StrategyType等特殊类型"""
    if isinstance(obj, StrategyType):
        return obj.value
    elif isinstance(obj, dict):
        new_dict = {}
        for k, v in obj.items():
            if isinstance(k, StrategyType):
                new_k = k.value
            else:
                new_k = k
            new_dict[new_k] = _serialize_for_json(v)
        return new_dict
    elif isinstance(obj, list):
        return [_serialize_for_json(item) for item in obj]
    elif hasattr(obj, '__dict__'):
        # 处理简单对象
        return _serialize_for_json(obj.__dict__)
    else:
        return obj


class SignalPersistence:
    """信号/回测/优化结果持久化到SQLite"""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self._db = db_manager

    def save_signals(self, signals: List[FusedSignal]) -> int:
        if not signals:
            return 0
        records = []
        for sig in signals:
            records.append({
                "symbol": sig.symbol,
                "date": sig.date,
                "signal_type": sig.signal_type.value,
                "strength": sig.strength.value,
                "price": sig.price,
                "confidence": sig.confidence,
                "contributing_json": json.dumps([s.value for s in sig.contributing_strategies]),
                "weights_json": json.dumps({k.value: v for k, v in sig.weights.items()}),
                "description": sig.description,
                "buy_price_target": sig.buy_price_target,
                "sell_price_target": sig.sell_price_target,
            })
        return self._db.insert_batch("signal_records", records)

    def save_backtest_result(self, result: BacktestResult) -> int:
        trades_json = json.dumps([
            {
                "entry_date": t.entry_date, "entry_price": t.entry_price,
                "exit_date": t.exit_date, "exit_price": t.exit_price,
                "profit": t.profit, "profit_rate": t.profit_rate,
                "holding_days": t.holding_days,
            } for t in result.trades
        ])
        equity_json = json.dumps(result.equity_curve)
        # 序列化参数，处理StrategyType类型
        params_to_save = _serialize_for_json(result.params)
        
        record = {
            "symbol": result.symbol,
            "strategy_type": result.strategy_type.value,
            "params_json": json.dumps(params_to_save),
            "start_date": result.start_date,
            "end_date": result.end_date,
            "total_trades": result.total_trades,
            "win_trades": result.win_trades,
            "loss_trades": result.loss_trades,
            "win_rate": result.win_rate,
            "avg_profit_rate": result.avg_profit_rate,
            "profit_loss_ratio": result.profit_loss_ratio,
            "max_drawdown": result.max_drawdown,
            "max_drawdown_duration": result.max_drawdown_duration,
            "total_return": result.total_return,
            "annualized_return": result.annualized_return,
            "sharpe_ratio": result.sharpe_ratio,
            "equity_curve_json": equity_json,
            "trades_json": trades_json,
            "status": "completed",
        }
        return self._db.insert_batch("backtest_results", [record])

    def save_optimization_result(self, result: OptimizationResult, symbol_name: str = None) -> int:
        # 序列化参数，处理StrategyType类型
        best_params_to_save = _serialize_for_json(result.best_params)
        all_results_to_save = _serialize_for_json(result.all_results)
        
        # 构建基础记录
        record = {
            "symbol": result.symbol,
            "strategy_type": result.strategy_type.value,
            "optimization_method": result.optimization_method,
            "metric_name": result.metric_name,
            "best_params_json": json.dumps(best_params_to_save),
            "best_metric_value": result.best_metric_value,
            "all_results_json": json.dumps(all_results_to_save),
            "elapsed_time": result.elapsed_time,
        }
        
        # 检查数据库是否有 symbol_name 列
        try:
            columns = self._db.query("PRAGMA table_info(optimization_results)")
            column_names = [col['name'] for col in columns]
            
            if 'symbol_name' in column_names:
                record["symbol_name"] = symbol_name
        except Exception as e:
            logger.warning(f"检查数据库列时出错: {e}")
        
        return self._db.insert_batch("optimization_results", [record])
    
    def get_optimization_results(self, symbol: str = None, strategy_type: str = None) -> List[Dict[str, Any]]:
        """获取优化结果
        
        Args:
            symbol: 股票代码（可选）
            strategy_type: 策略类型（可选）
            
        Returns:
            优化结果列表
        """
        sql = "SELECT * FROM optimization_results WHERE 1=1"
        params = []
        if symbol:
            sql += " AND symbol = ?"
            params.append(symbol)
        if strategy_type:
            sql += " AND strategy_type = ?"
            params.append(strategy_type)
        sql += " ORDER BY created_at DESC"
        
        results = self._db.query(sql, tuple(params))
        for r in results:
            if r.get("best_params_json"):
                r["best_params"] = json.loads(r["best_params_json"])
        return results
    
    def get_latest_optimization(self, symbol: str, strategy_type: str) -> Optional[Dict[str, Any]]:
        """获取某只股票某策略的最新优化结果
        
        Args:
            symbol: 股票代码
            strategy_type: 策略类型
            
        Returns:
            最新优化结果，如果没有则返回None
        """
        sql = """
            SELECT * FROM optimization_results 
            WHERE symbol = ? AND strategy_type = ? 
            ORDER BY created_at DESC LIMIT 1
        """
        results = self._db.query(sql, (symbol, strategy_type))
        if results:
            r = results[0]
            if r.get("best_params_json"):
                r["best_params"] = json.loads(r["best_params_json"])
            return r
        return None

    def load_signals(self, symbol: str,
                     start_date: str, end_date: str) -> List[Dict]:
        return self._db.query(
            "SELECT * FROM signal_records WHERE symbol=? AND date BETWEEN ? AND ? ORDER BY date",
            (symbol, start_date, end_date),
        )
        
    def load_fused_signals(self, symbol: str,
                          start_date: str, end_date: str) -> List[FusedSignal]:
        """加载信号记录并转换为 FusedSignal 对象
        """
        from src.core.constants import SignalType, SignalStrength, StrategyType
        
        records = self.load_signals(symbol, start_date, end_date)
        signals = []
        
        for rec in records:
            try:
                signal = FusedSignal(
                    date=rec["date"],
                    symbol=rec["symbol"],
                    signal_type=SignalType(rec["signal_type"]),
                    strength=SignalStrength(rec["strength"]),
                    price=rec["price"],
                    confidence=rec["confidence"],
                    description=rec.get("description", ""),
                    buy_price_target=rec.get("buy_price_target"),
                    sell_price_target=rec.get("sell_price_target"),
                )
                signals.append(signal)
            except Exception as e:
                logger.warning(f"解析信号记录失败: {e}")
        
        return signals

    def load_backtest_results(self, symbol: str,
                              strategy_type: Optional[str] = None) -> List[Dict]:
        if strategy_type:
            return self._db.query(
                "SELECT * FROM backtest_results WHERE symbol=? AND strategy_type=? ORDER BY created_at DESC",
                (symbol, strategy_type),
            )
        return self._db.query(
            "SELECT * FROM backtest_results WHERE symbol=? ORDER BY created_at DESC",
            (symbol,),
        )
    
    def load_backtest_result_object(self, record: Dict) -> BacktestResult:
        """从数据库记录重建 BacktestResult 对象
        
        Args:
            record: 数据库记录字典
            
        Returns:
            BacktestResult 对象
        """
        import json
        
        # 重建交易记录
        trades = []
        if record.get("trades_json"):
            try:
                trades_data = json.loads(record["trades_json"])
                for t in trades_data:
                    trades.append(TradeRecord(
                        entry_date=t["entry_date"],
                        entry_price=t["entry_price"],
                        exit_date=t["exit_date"],
                        exit_price=t["exit_price"],
                        signal_type=SignalType.SELL,
                        profit=t["profit"],
                        profit_rate=t["profit_rate"],
                        holding_days=t["holding_days"],
                    ))
            except Exception as e:
                logger.warning(f"解析交易记录失败: {e}")
        
        # 重建权益曲线
        equity_curve = []
        if record.get("equity_curve_json"):
            try:
                equity_curve = json.loads(record["equity_curve_json"])
            except Exception as e:
                logger.warning(f"解析权益曲线失败: {e}")
        
        # 重建策略类型
        try:
            strategy_type = StrategyType(record["strategy_type"])
        except:
            strategy_type = StrategyType.TECHNICAL_INDICATOR
        
        # 重建参数
        params = {}
        if record.get("params_json"):
            try:
                params = json.loads(record["params_json"])
            except Exception as e:
                logger.warning(f"解析回测参数失败: {e}")
        
        return BacktestResult(
            symbol=record["symbol"],
            strategy_type=strategy_type,
            params=params,
            start_date=record["start_date"],
            end_date=record["end_date"],
            trades=trades,
            total_trades=record.get("total_trades", 0),
            win_trades=record.get("win_trades", 0),
            loss_trades=record.get("loss_trades", 0),
            win_rate=record.get("win_rate", 0.0),
            avg_profit_rate=record.get("avg_profit_rate", 0.0),
            profit_loss_ratio=record.get("profit_loss_ratio", 0.0),
            max_drawdown=record.get("max_drawdown", 0.0),
            max_drawdown_duration=record.get("max_drawdown_duration", 0),
            total_return=record.get("total_return", 0.0),
            annualized_return=record.get("annualized_return", 0.0),
            sharpe_ratio=record.get("sharpe_ratio", 0.0),
            equity_curve=equity_curve,
        )

    def load_optimization_results(self, symbol: str,
                                  strategy_type: Optional[str] = None) -> List[Dict]:
        if strategy_type:
            return self._db.query(
                "SELECT * FROM optimization_results WHERE symbol=? AND strategy_type=? ORDER BY created_at DESC",
                (symbol, strategy_type),
            )
        return self._db.query(
            "SELECT * FROM optimization_results WHERE symbol=? ORDER BY created_at DESC",
            (symbol,),
        )
    
    def save_strategy_config(self, config_dict: dict, symbol: Optional[str] = None) -> int:
        """保存策略配置到数据库
        
        Args:
            config_dict: 配置字典
            symbol: 股票代码（可选，特定股票的配置）
            
        Returns:
            保存的记录数
        """
        import json
        
        logger.info(f"开始保存策略配置，symbol={symbol}")
        
        # 构建保存的记录
        record = {
            "strategy_type": "all" if symbol is None else symbol,
            "symbol": symbol,
            "params_json": json.dumps(config_dict),
            "is_optimized": 0
        }
        
        logger.debug(f"要保存的配置: {record}")
        
        # 使用 INSERT OR REPLACE 直接保存，简化逻辑
        result = self._db.insert_batch("strategy_params", [record])
        
        logger.info(f"策略配置保存完成，影响行数: {result}")
        return result
    
    def load_strategy_config(self, symbol: Optional[str] = None) -> Optional[Dict]:
        """从数据库加载策略配置
        
        Args:
            symbol: 股票代码（可选，加载特定股票的配置）
            
        Returns:
            配置字典，如果不存在则返回None
        """
        import json
        
        logger.info(f"开始加载策略配置，symbol={symbol}")
        
        strategy_type = "all" if symbol is None else symbol
        
        if symbol is None:
            # 加载全局配置
            records = self._db.query(
                "SELECT * FROM strategy_params WHERE strategy_type=? AND symbol IS NULL ORDER BY created_at DESC LIMIT 1",
                (strategy_type,)
            )
        else:
            # 加载特定股票的配置
            records = self._db.query(
                "SELECT * FROM strategy_params WHERE strategy_type=? AND symbol=? ORDER BY created_at DESC LIMIT 1",
                (strategy_type, symbol)
            )
        
        logger.info(f"查询到 {len(records)} 条配置记录")
        
        if records:
            try:
                config_dict = json.loads(records[0]["params_json"])
                logger.info("配置加载成功")
                return config_dict
            except Exception as e:
                logger.error(f"解析配置失败: {e}")
                return None
        return None
    
    def delete_backtest_result(self, record_id: int) -> int:
        """删除回测结果
        
        Args:
            record_id: 回测记录ID
            
        Returns:
            删除的记录数
        """
        return self._db.delete("backtest_results", {"id": record_id})
    
    def delete_optimization_result(self, record_id: int) -> int:
        """删除优化结果
        
        Args:
            record_id: 优化记录ID
            
        Returns:
            删除的记录数
        """
        return self._db.delete("optimization_results", {"id": record_id})
    
    def delete_signals_by_symbol(self, symbol: str) -> int:
        """删除指定股票的所有信号
        
        Args:
            symbol: 股票代码
            
        Returns:
            删除的记录数
        """
        return self._db.delete("signal_records", {"symbol": symbol})