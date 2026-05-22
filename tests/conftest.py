"""
Pytest configuration and shared fixtures
"""
import sys
from pathlib import Path

# Add src directory to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import pytest
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any


@pytest.fixture(scope="session")
def sample_kline_data() -> pd.DataFrame:
    """
    生成测试用的K线数据
    
    Returns:
        pd.DataFrame: 包含基础OHLCV数据
    """
    dates = []
    base_date = datetime(2020, 1, 1)
    
    for i in range(100):
        dates.append((base_date + timedelta(days=i)).strftime("%Y-%m-%d"))
    
    data = {
        "symbol": ["688258"] * 100,
        "date": dates,
        "open": [100 + i * 0.1 for i in range(100)],
        "high": [100 + i * 0.1 + 2 for i in range(100)],
        "low": [100 + i * 0.1 - 1 for i in range(100)],
        "close": [100 + i * 0.1 for i in range(100)],
        "volume": [1000000 + i * 1000 for i in range(100)],
        "amount": [100000000 + i * 10000 for i in range(100)],
    }
    
    df = pd.DataFrame(data)
    return df


@pytest.fixture(scope="session")
def sample_trade_records() -> List[Dict[str, Any]]:
    """
    生成测试用的交易记录
    
    Returns:
        List[Dict]: 交易记录列表
    """
    return [
        {
            "entry_date": "2020-01-10",
            "entry_price": 105.0,
            "exit_date": "2020-01-20",
            "exit_price": 115.0,
            "profit": 950.0,
            "profit_rate": 0.095,
            "holding_days": 8,
        },
        {
            "entry_date": "2020-02-01",
            "entry_price": 120.0,
            "exit_date": "2020-02-15",
            "exit_price": 110.0,
            "profit": -1050.0,
            "profit_rate": -0.0875,
            "holding_days": 10,
        },
    ]


@pytest.fixture(scope="session")
def temp_db_path(tmp_path_factory) -> Path:
    """
    创建临时测试数据库路径
    
    Returns:
        Path: 数据库文件路径
    """
    return tmp_path_factory.mktemp("data") / "test.db"
