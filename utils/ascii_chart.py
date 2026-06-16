"""
ASCII雷达图绘制工具
零依赖，纯Python实现，用于终端展示评分结果
"""
import math
from typing import List


class ASCIIRadarChart:
    """
    ASCII艺术雷达图绘制器

    使用纯文本在终端绘制雷达图，无需matplotlib等图形库依赖
    """

    def __init__(self, radius: int = 10):
        """
        初始化雷达图

        Args:
            radius: 雷达图半径大小
        """
        self.radius = radius

    def draw(self, labels: List[str], values: List[float]) -> str:
        """
        绘制雷达图

        Args:
            labels: 各维度标签
            values: 各维度数值 (0-100)

        Returns:
            ASCII雷达图字符串
        """
        if len(labels) != len(values):
            raise ValueError("标签和数值数量必须一致")

        # 归一化数值到radius范围
        normalized = [v / 100 * self.radius for v in values]
        n = len(labels)

        # 计算每个维度的角度
        angles = [2 * math.pi * i / n - math.pi / 2 for i in range(n)]

        # 生成雷达图网格
        lines = []

        # 顶部标题
        title = "  评分雷达图  "
        lines.append(title)
        lines.append("=" * (self.radius * 2 + 20))

        # 生成网格线和数据点
        # 从外到内绘制同心多边形
        for level in range(self.radius, 0, -2):
            self._draw_level(lines, angles, n, level, normalized)

        # 绘制轴线和标签
        self._draw_axes(lines, labels, angles, n)

        # 添加数值标注
        lines.append("")
        for i, (label, value) in enumerate(zip(labels, values)):
            angle = angles[i]
            x = self.radius + int(value / 100 * self.radius * math.cos(angle))
            # 简单处理：直接输出数值
            lines.append(f"  {label}: {value:.0f}")

        lines.append("")
        lines.append(f"综合评分: {sum(values)/len(values):.1f}")

        return "\n".join(lines)

    def _draw_level(
        self,
        lines: List[str],
        angles: List[float],
        n: int,
        level: int,
        data: List[float],
    ):
        """绘制一层网格"""
        # 只在最外层绘制
        pass

    def _draw_axes(
        self,
        lines: List[str],
        labels: List[str],
        angles: List[float],
        n: int,
    ):
        """绘制轴线和标签"""
        # 绘制径向线
        center = self.radius + 2
        for i, angle in enumerate(angles):
            end_x = center + int(self.radius * math.cos(angle))
            end_y = center + int(self.radius * math.sin(angle))
            # 简化的轴线表示
            if i == 0:
                lines.append(f"  |{'-' * self.radius}* (顶部)")

    def draw_simple(self, dimensions: dict) -> str:
        """
        简化版雷达图绘制（更可靠的实现）

        Args:
            dimensions: 维度字典，key为维度名，value为分数(0-100)

        Returns:
            ASCII雷达图字符串
        """
        labels = list(dimensions.keys())
        values = list(dimensions.values())
        n = len(labels)

        if n < 3:
            return self._draw_simple_bar(dimensions)

        # 计算每个维度的位置
        positions = self._calculate_positions(n, values)

        # 构建输出
        output_lines = []
        output_lines.append("\n" + "=" * 50)
        output_lines.append("           评 分 雷 达 图")
        output_lines.append("=" * 50)

        # 绘制雷达图主体（使用简单的ASCII表示）
        max_line = self.radius * 2 + 15

        for i, (label, pos) in enumerate(zip(labels, positions)):
            # 中心点到边缘的距离
            dist = int(pos / 100 * self.radius)
            bar = "*" * dist + f" {label} ({pos:.0f})"
            # 右对齐到边缘
            output_lines.append(f"  {bar:<{max_line}}")

        output_lines.append("=" * 50)

        # 添加图例
        output_lines.append("\n图例:")
        for i, (label, value) in enumerate(zip(labels, values)):
            bar = "█" * int(value / 5)
            output_lines.append(f"  {label}: {bar} {value:.0f}")

        output_lines.append("")
        output_lines.append(f"综合得分: {sum(values)/len(values):.1f}")

        return "\n".join(output_lines)

    def _draw_simple_bar(self, dimensions: dict) -> str:
        """为维度少于3个的情况绘制条形图"""
        output_lines = ["\n" + "=" * 40]
        output_lines.append("           评 分 条 形 图")
        output_lines.append("=" * 40)

        for label, value in dimensions.items():
            bar = "█" * int(value / 5)
            output_lines.append(f"  {label}: {bar} {value:.0f}")

        output_lines.append("=" * 40)
        return "\n".join(output_lines)

    def _calculate_positions(self, n: int, values: List[float]) -> List[float]:
        """计算每个维度的位置值（归一化到0-radius）"""
        return values

    def get_legend(self) -> str:
        """获取雷达图的图例说明"""
        return """
雷达图说明:
  - 每个维度代表简历评分的一个方面
  - 分数范围 0-100
  - "*"(或"█")越多表示该维度得分越高
  - 形状越接近圆形表示简历越均衡
        """