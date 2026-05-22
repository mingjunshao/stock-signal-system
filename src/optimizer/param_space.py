"""参数空间定义：范围、网格点生成、编码/解码"""

import itertools
import random
from typing import Any, Dict, List, Tuple

from src.core.constants import StrategyType


class ParamSpace:
    """参数空间定义"""

    def __init__(self, strategy_type: StrategyType,
                 ranges: Dict[str, Tuple[float, float, float]]) -> None:
        self.strategy_type = strategy_type
        self.ranges = ranges  # {param_name: (min, max, step)}

    def get_grid_points(self) -> List[Dict[str, Any]]:
        """生成网格搜索的所有参数组合"""
        param_lists = {}
        for name, (min_val, max_val, step) in self.ranges.items():
            if step == 0:
                param_lists[name] = [min_val]
            else:
                count = int((max_val - min_val) / step) + 1
                param_lists[name] = [min_val + i * step for i in range(count)]

        keys = list(param_lists.keys())
        values = list(param_lists.values())
        combinations = list(itertools.product(*values))

        return [dict(zip(keys, combo)) for combo in combinations]

    def get_random_point(self) -> Dict[str, Any]:
        """随机生成一个参数点"""
        point = {}
        for name, (min_val, max_val, step) in self.ranges.items():
            if step == 0:
                point[name] = min_val
            else:
                raw = random.uniform(min_val, max_val)
                rounded = round(raw / step) * step
                point[name] = max(min_val, min(max_val, rounded))
        return point

    def get_size(self) -> int:
        """参数空间大小"""
        total = 1
        for name, (min_val, max_val, step) in self.ranges.items():
            if step == 0:
                continue
            count = int((max_val - min_val) / step) + 1
            total *= count
        return total

    def encode_point(self, params: Dict[str, Any]) -> List[float]:
        """编码参数为向量（遗传算法用）"""
        vector = []
        for name, (min_val, max_val, _) in self.ranges.items():
            val = params.get(name, min_val)
            normalized = (val - min_val) / (max_val - min_val) if max_val > min_val else 0
            vector.append(normalized)
        return vector

    def decode_vector(self, vector: List[float]) -> Dict[str, Any]:
        """解码向量为参数"""
        params = {}
        for i, (name, (min_val, max_val, step)) in enumerate(self.ranges.items()):
            if i < len(vector):
                raw = min_val + vector[i] * (max_val - min_val)
                if step > 0:
                    raw = round(raw / step) * step
                params[name] = max(min_val, min(max_val, raw))
            else:
                params[name] = min_val
        return params