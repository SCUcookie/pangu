"""
公式查询工具
"""
from ..base import BaseTool, ToolParameter, ToolResult


class FormulaParams(ToolParameter):
    """公式查询参数"""
    subject: str  # 学科
    keyword: str  # 关键词


class FormulaLookupTool(BaseTool):
    """公式查询工具"""
    
    name = "formula_lookup"
    description = "查询数学、物理、化学公式，输入学科和关键词即可"
    parameters_schema = FormulaParams
    
    # 公式库
    FORMULA_DB = {
        "数学": {
            "求根公式": "x = (-b ± √(b²-4ac)) / 2a （一元二次方程ax²+bx+c=0的解）",
            "韦达定理": "x₁ + x₂ = -b/a, x₁ × x₂ = c/a",
            "等差数列求和": "Sn = n(a₁+aₙ)/2 = na₁ + n(n-1)d/2",
            "等比数列求和": "Sn = a₁(1-qⁿ)/(1-q) (q≠1)",
            "三角函数": "sin²θ + cos²θ = 1, tanθ = sinθ/cosθ",
            "二倍角公式": "sin2α = 2sinαcosα, cos2α = cos²α - sin²α",
            "面积公式": "三角形: S = ½ah, 圆: S = πr², 梯形: S = ½(a+b)h",
            "体积公式": "球: V = 4πr³/3, 圆柱: V = πr²h, 圆锥: V = πr²h/3",
            "排列组合": "Aₙᵐ = n!/(n-m)!, Cₙᵐ = n!/[m!(n-m)!]",
            "对数运算": "log(ab) = loga + logb, log(a/b) = loga - logb, log(aⁿ) = nloga",
        },
        "物理": {
            "运动学": "v = v₀ + at, s = v₀t + ½at², v² - v₀² = 2as",
            "牛顿定律": "F = ma, G = Gm₁m₂/r²",
            "动能": "Ek = ½mv²",
            "势能": "Ep = mgh（重力势能）, Ep = ½kx²（弹性势能）",
            "动量": "p = mv, Ft = Δmv（动量定理）",
            "功率": "P = W/t = Fv",
            "欧姆定律": "I = U/R, P = UI = I²R = U²/R",
            "电容": "C = Q/U, E = ½CU² = ½QU",
            "波动": "v = fλ, T = 1/f",
            "热力学": "Q = cmΔT, W = pΔV, ΔU = Q + W",
        },
        "化学": {
            "摩尔": "n = m/M = N/NA, NA = 6.02×10²³",
            "气体": "pV = nRT, R = 8.314 J/(mol·K)",
            "浓度": "c = n/V (mol/L), 质量分数w = m溶质/m溶液 × 100%",
            "稀释": "c₁V₁ = c₂V₂",
            "反应热": "ΔH = 生成物能量 - 反应物能量",
            "平衡常数": "K = [C]^c[D]^d / [A]^a[B]^b （aA+bB⇌cC+dD）",
            "pH": "pH = -lg[H⁺], pOH = -lg[OH⁻], pH + pOH = 14",
            "电解": "m = MIt/(nF), F = 96500 C/mol",
        },
    }
    
    async def execute(self, params: FormulaParams) -> ToolResult:
        """查询公式"""
        subject = params.subject.strip()
        keyword = params.keyword.strip().lower()
        
        # 查找学科
        subject_formulas = None
        matched_subject = None
        for key in self.FORMULA_DB:
            if key in subject or subject in key:
                subject_formulas = self.FORMULA_DB[key]
                matched_subject = key
                break
        
        if not subject_formulas:
            return ToolResult(
                success=False,
                error=f"未找到学科'{subject}'，支持的学科：{list(self.FORMULA_DB.keys())}"
            )
        
        # 搜索匹配的公式
        results = []
        for name, formula in subject_formulas.items():
            if keyword in name.lower() or keyword in formula.lower():
                results.append({"name": name, "formula": formula})
        
        if results:
            return ToolResult(success=True, data={"subject": matched_subject, "formulas": results})
        
        # 返回所有公式
        return ToolResult(
            success=False,
            error=f"未找到包含'{keyword}'的公式，该学科可用公式：{list(subject_formulas.keys())}"
        )
