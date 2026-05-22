"""SQLite数据库管理：连接池、建表、CRUD操作"""

import sqlite3
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.core.logger import setup_logger

logger = setup_logger("database")


class DatabaseManager:
    """SQLite数据库管理器"""
    
    # 合法表名白名单
    _VALID_TABLES = {
        "daily_kline", "stock_info", "strategy_params", "fusion_weights",
        "signal_records", "backtest_results", "optimization_results"
    }

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None
    
    def _validate_table(self, table: str) -> None:
        """验证表名是否在白名单中，防止SQL注入"""
        if table not in self._VALID_TABLES:
            raise ValueError(f"Invalid table name: {table}, valid tables are: {sorted(self._VALID_TABLES)}")

    def connect(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
        return self._conn

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def init_tables(self) -> None:
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_kline (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol      TEXT NOT NULL,
                date        TEXT NOT NULL,
                open        REAL NOT NULL,
                high        REAL NOT NULL,
                low         REAL NOT NULL,
                close       REAL NOT NULL,
                volume      REAL NOT NULL,
                amount      REAL,
                turnover    REAL,
                adj_close   REAL,
                created_at  TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, date)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_kline_symbol ON daily_kline(symbol)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_kline_date ON daily_kline(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_kline_symbol_date ON daily_kline(symbol, date)")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_info (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol      TEXT NOT NULL UNIQUE,
                name        TEXT NOT NULL,
                market      TEXT,
                industry    TEXT,
                list_date   TEXT,
                is_tracked  INTEGER DEFAULT 0,
                updated_at  TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS strategy_params (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_type   TEXT NOT NULL,
                symbol          TEXT,
                params_json     TEXT NOT NULL,
                is_optimized    INTEGER DEFAULT 0,
                optimization_id INTEGER,
                created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at      TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(strategy_type, symbol)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fusion_weights (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol          TEXT,
                tech_indicator  REAL DEFAULT 0.25,
                mean_reversion  REAL DEFAULT 0.25,
                volume_price    REAL DEFAULT 0.25,
                trend_following REAL DEFAULT 0.25,
                buy_threshold   REAL DEFAULT 0.6,
                sell_threshold  REAL DEFAULT -0.6,
                created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at      TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS signal_records (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol              TEXT NOT NULL,
                date                TEXT NOT NULL,
                signal_type         TEXT NOT NULL,
                strength            INTEGER NOT NULL,
                price               REAL NOT NULL,
                confidence          REAL NOT NULL,
                contributing_json   TEXT,
                weights_json        TEXT,
                description         TEXT,
                buy_price_target    REAL,
                sell_price_target   REAL,
                created_at          TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, date, signal_type)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_signal_symbol ON signal_records(symbol)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_signal_date ON signal_records(date)")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS backtest_results (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol          TEXT NOT NULL,
                strategy_type   TEXT NOT NULL,
                params_json     TEXT NOT NULL,
                start_date      TEXT NOT NULL,
                end_date        TEXT NOT NULL,
                initial_capital REAL DEFAULT 100000,
                total_trades    INTEGER,
                win_trades      INTEGER,
                loss_trades     INTEGER,
                win_rate        REAL,
                avg_profit_rate REAL,
                profit_loss_ratio REAL,
                max_drawdown    REAL,
                max_drawdown_duration INTEGER,
                total_return    REAL,
                annualized_return REAL,
                sharpe_ratio    REAL,
                equity_curve_json TEXT,
                trades_json     TEXT,
                status          TEXT DEFAULT 'completed',
                created_at      TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_backtest_symbol ON backtest_results(symbol)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_backtest_strategy ON backtest_results(strategy_type)")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS optimization_results (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol          TEXT NOT NULL,
                symbol_name     TEXT,
                strategy_type   TEXT NOT NULL,
                optimization_method TEXT NOT NULL,
                metric_name     TEXT NOT NULL,
                best_params_json TEXT NOT NULL,
                best_metric_value REAL,
                all_results_json TEXT,
                elapsed_time    REAL,
                created_at      TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_opt_symbol ON optimization_results(symbol)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_opt_strategy ON optimization_results(strategy_type)")
        
        # 数据库迁移：添加缺失的列
        self._migrate_database(cursor)

        conn.commit()
        logger.info("数据库表初始化完成")
    
    def _migrate_database(self, cursor) -> None:
        """执行数据库迁移"""
        try:
            # 检查 optimization_results 表是否有 symbol_name 列
            cursor.execute("PRAGMA table_info(optimization_results)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'symbol_name' not in columns:
                logger.info("正在添加 symbol_name 列到 optimization_results 表...")
                cursor.execute("ALTER TABLE optimization_results ADD COLUMN symbol_name TEXT")
                logger.info("symbol_name 列添加成功")
                
        except Exception as e:
            logger.warning(f"数据库迁移时出错: {e}")

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        return cursor

    def query(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def insert_batch(self, table: str, data: List[Dict[str, Any]]) -> int:
        self._validate_table(table)
        if not data:
            return 0
        conn = self.connect()
        columns = list(data[0].keys())
        placeholders = ",".join(["?"] * len(columns))
        sql = f"INSERT OR REPLACE INTO {table} ({','.join(columns)}) VALUES ({placeholders})"
        values = [tuple(row.get(col) for col in columns) for row in data]
        cursor = conn.cursor()
        cursor.executemany(sql, values)
        conn.commit()
        return cursor.rowcount

    def update(self, table: str, conditions: Dict[str, Any], updates: Dict[str, Any]) -> int:
        self._validate_table(table)
        conn = self.connect()
        where_clause = " AND ".join([f"{k}=?" for k in conditions.keys()])
        set_clause = ",".join([f"{k}=?" for k in updates.keys()])
        sql = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        params = tuple(updates.values()) + tuple(conditions.values())
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        return cursor.rowcount

    def delete(self, table: str, conditions: Dict[str, Any]) -> int:
        self._validate_table(table)
        conn = self.connect()
        where_clause = " AND ".join([f"{k}=?" for k in conditions.keys()])
        sql = f"DELETE FROM {table} WHERE {where_clause}"
        cursor = conn.cursor()
        cursor.execute(sql, tuple(conditions.values()))
        conn.commit()
        return cursor.rowcount

    def table_exists(self, table_name: str) -> bool:
        result = self.query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        return len(result) > 0

    def get_table_count(self, table_name: str) -> int:
        self._validate_table(table_name)
        result = self.query(f"SELECT COUNT(*) as cnt FROM {table_name}")
        return result[0]["cnt"] if result else 0