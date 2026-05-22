"""
测试数据库管理模块
"""
import sys
import sqlite3
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import pytest
from src.core.database import DatabaseManager


def test_database_initialization(temp_db_path):
    """测试数据库初始化"""
    db = DatabaseManager(temp_db_path)
    
    # 初始化表
    db.init_tables()
    
    # 验证表已创建
    conn = db.connect()
    cursor = conn.cursor()
    
    # 查询表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    expected_tables = [
        "daily_kline",
        "stock_info",
        "strategy_params",
        "fusion_weights",
        "signal_records",
        "backtest_results",
        "optimization_results",
    ]
    
    for table in expected_tables:
        assert table in tables, f"表 {table} 应该存在"
    
    db.close()


def test_sql_injection_protection(temp_db_path):
    """测试SQL注入防护"""
    db = DatabaseManager(temp_db_path)
    db.init_tables()
    
    # 测试白名单验证
    with pytest.raises(ValueError, match="Invalid table name"):
        db.insert_batch("malicious_table", [])
    
    # 测试合法表名正常工作
    valid_data = [{
        "symbol": "000001",
        "name": "平安银行",
        "market": "SZ",
    }]
    
    # 应该正常执行（我们用insert_batch验证）
    try:
        # 这个方法内部会验证表名
        db.insert_batch("stock_info", valid_data)
    except Exception as e:
        pytest.fail(f"不应该抛出异常，但抛出了: {e}")
    
    db.close()


def test_table_exists(temp_db_path):
    """测试表存在检查"""
    db = DatabaseManager(temp_db_path)
    db.init_tables()
    
    assert db.table_exists("daily_kline") is True
    assert db.table_exists("nonexistent_table") is False
    
    db.close()


def test_valid_tables_constant():
    """测试合法表名常量"""
    from src.core.database import DatabaseManager
    # 验证内部有VALID_TABLES常量
    # 由于是私有属性，我们间接测试
    db = DatabaseManager(":memory:")
    
    # 应该拒绝不存在的表
    with pytest.raises(ValueError):
        db.delete("invalid_table", {})
    
    db.close()


if __name__ == "__main__":
    import tempfile
    
    # 创建临时数据库
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        print("测试数据库初始化...")
        test_database_initialization(temp_path)
        
        print("测试SQL注入防护...")
        test_sql_injection_protection(temp_path)
        
        print("测试表存在检查...")
        test_table_exists(temp_path)
        
        print("测试合法表名常量...")
        test_valid_tables_constant()
        
        print("✓ 所有数据库测试通过！")
    finally:
        try:
            temp_path.unlink()
        except:
            pass
