"""YAML配置管理：加载、合并默认值、属性访问"""

import yaml
from pathlib import Path
from typing import Any, Dict, Optional


_DEFAULT_CONFIG = {
    "data": {
        "source": "akshare",
        "db_path": "data/stock_data.db",
        "cache_dir": "data/cache",
        "default_start_date": "2020-01-01",
        "fetch_timeout": 30,
    },
    "strategies": {
        "tech_indicator": {"enabled": True, "params": {
            "macd_fast": 12, "macd_slow": 26, "macd_signal": 9,
            "kdj_n": 9, "kdj_m1": 3, "kdj_m2": 3,
            "rsi_periods": [6, 12, 24], "rsi_buy_threshold": 30, "rsi_sell_threshold": 70,
            "boll_period": 20, "boll_std": 2,
        }},
        "mean_reversion": {"enabled": True, "params": {
            "ma_period": 20, "deviation_threshold": 2.0,
            "support_lookback": 20, "resistance_lookback": 20, "reversion_speed": 0.5,
        }},
        "volume_price": {"enabled": True, "params": {
            "volume_ratio_threshold": 2.0, "volume_ma_period": 5,
            "price_change_threshold": 0.03, "obv_trend_period": 10,
        }},
        "trend_following": {"enabled": True, "params": {
            "fast_ma": 5, "slow_ma": 20, "trend_ma": 60,
            "momentum_period": 10, "atr_period": 14,
        }},
    },
    "fusion": {
        "weights": {
            "tech_indicator": 0.25, "mean_reversion": 0.25,
            "volume_price": 0.25, "trend_following": 0.25,
        },
        "buy_threshold": 0.6, "sell_threshold": -0.6,
    },
    "backtest": {
        "initial_capital": 100000, "commission_rate": 0.0003,
        "stamp_tax_rate": 0.001, "min_commission": 5.0, "min_lot_size": 100,
    },
    "optimizer": {
        "grid_search": {"max_combinations": 500},
        "genetic": {
            "population_size": 50, "generations": 30,
            "crossover_rate": 0.7, "mutation_rate": 0.2, "tournament_size": 3,
        },
    },
    "ui": {
        "theme": "dark", "window_width": 1400, "window_height": 900,
        "sidebar_width": 200, "log_panel_height": 150,
    },
}


class Config:
    """全局配置管理器，YAML加载+默认值合并"""

    def __init__(self, config_path: Optional[str] = None) -> None:
        self._config_path = Path(config_path) if config_path else None
        self._data: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        self._data = _DEFAULT_CONFIG.copy()
        if self._config_path and self._config_path.exists():
            with open(self._config_path, "r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f)
            if loaded:
                self._merge_config(loaded)

    def _merge_config(self, loaded: Dict[str, Any]) -> None:
        for key, value in loaded.items():
            if key in self._data and isinstance(self._data[key], dict) and isinstance(value, dict):
                self._data[key] = self._deep_merge(self._data[key], value)
            else:
                self._data[key] = value

    @staticmethod
    def _deep_merge(base: Dict, override: Dict) -> Dict:
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = Config._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def reload(self) -> None:
        self._load_config()

    def save(self) -> None:
        if self._config_path:
            with open(self._config_path, "w", encoding="utf-8") as f:
                yaml.dump(self._data, f, default_flow_style=False, allow_unicode=True)

    @property
    def data(self) -> Dict[str, Any]:
        return self._data.get("data", {})

    @property
    def strategies(self) -> Dict[str, Any]:
        return self._data.get("strategies", {})

    @property
    def backtest(self) -> Dict[str, Any]:
        return self._data.get("backtest", {})

    @property
    def optimizer(self) -> Dict[str, Any]:
        return self._data.get("optimizer", {})

    @property
    def ui(self) -> Dict[str, Any]:
        return self._data.get("ui", {})

    @property
    def fusion(self) -> Dict[str, Any]:
        return self._data.get("fusion", {})

    def get_db_path(self) -> Path:
        project_root = self._config_path.parent if self._config_path else Path.cwd()
        return project_root / self.data.get("db_path", "data/stock_data.db")

    def get_cache_dir(self) -> Path:
        project_root = self._config_path.parent if self._config_path else Path.cwd()
        return project_root / self.data.get("cache_dir", "data/cache")

    def get_output_dir(self) -> Path:
        project_root = self._config_path.parent if self._config_path else Path.cwd()
        return project_root / "output"

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split(".")
        value = self._data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value