"""
知识查询工具
"""
from ..base import BaseTool, ToolParameter, ToolResult


class KnowledgeParams(ToolParameter):
    """知识查询参数"""
    subject: str  # 学科
    topic: str    # 知识点


class KnowledgeTool(BaseTool):
    """知识点查询工具"""
    
    name = "knowledge"
    description = "查询特定学科的知识点解释，支持数学、物理、化学、语文、英语等学科"
    parameters_schema = KnowledgeParams
    
    # 内置知识库（简化版，实际可接入外部知识库）
    KNOWLEDGE_BASE = {
        "数学": {
            "勾股定理": "在直角三角形中，斜边的平方等于两条直角边的平方之和。公式：a² + b² = c²，其中c为斜边。",
            "一元二次方程": "形如ax² + bx + c = 0（a≠0）的方程。求根公式：x = (-b ± √(b²-4ac)) / 2a",
            "等差数列": "相邻两项之差为常数的数列。通项公式：an = a1 + (n-1)d，求和公式：Sn = n(a1+an)/2",
            "等比数列": "相邻两项之比为常数的数列。通项公式：an = a1 × q^(n-1)，求和公式：Sn = a1(1-q^n)/(1-q)",
            "导数": "函数在某点的变化率。基本公式：(x^n)' = nx^(n-1), (e^x)' = e^x, (ln x)' = 1/x",
            "积分": "导数的逆运算。基本公式：∫x^n dx = x^(n+1)/(n+1) + C, ∫e^x dx = e^x + C",
        },
        "物理": {
            "牛顿第一定律": "物体在不受外力或所受合力为零时，保持静止或匀速直线运动状态。",
            "牛顿第二定律": "物体的加速度与所受合力成正比，与质量成反比。公式：F = ma",
            "牛顿第三定律": "作用力与反作用力大小相等、方向相反、作用在同一条直线上。",
            "动能定理": "合力做的功等于物体动能的变化。W = ΔEk = ½mv₂² - ½mv₁²",
            "机械能守恒": "只有重力或弹力做功时，物体的机械能守恒。Ek1 + Ep1 = Ek2 + Ep2",
            "欧姆定律": "导体中的电流与电压成正比，与电阻成反比。公式：I = U/R",
        },
        "化学": {
            "原子结构": "原子由原子核（质子+中子）和核外电子组成。质子数决定元素种类，电子数决定化学性质。",
            "化学键": "原子间的强相互作用。包括离子键（电子转移）、共价键（电子共用）、金属键。",
            "氧化还原": "电子转移的反应。失电子→氧化，得电子→还原。氧化剂得电子，还原剂失电子。",
            "化学平衡": "可逆反应达到平衡时，正逆反应速率相等，各物质浓度不再改变（动态平衡）。",
            "酸碱中和": "酸和碱反应生成盐和水。H⁺ + OH⁻ → H₂O",
        },
    }
    
    async def execute(self, params: KnowledgeParams) -> ToolResult:
        """查询知识点"""
        subject = params.subject.strip()
        topic = params.topic.strip()
        
        # 查找学科
        subject_data = None
        for key in self.KNOWLEDGE_BASE:
            if key in subject or subject in key:
                subject_data = self.KNOWLEDGE_BASE[key]
                break
        
        if not subject_data:
            return ToolResult(
                success=False,
                error=f"未找到学科'{subject}'的知识库，支持的学科：{list(self.KNOWLEDGE_BASE.keys())}"
            )
        
        # 查找知识点
        for key, value in subject_data.items():
            if topic in key or key in topic:
                return ToolResult(success=True, data={"topic": key, "content": value})
        
        # 返回该学科所有知识点列表
        return ToolResult(
            success=False,
            error=f"未找到知识点'{topic}'，该学科可查询的知识点：{list(subject_data.keys())}"
        )
