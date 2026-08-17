# 04_FUTU_INDICATOR_ENGINE
## MOOMOO & FUTU BULL VPA QUANTITATIVE INDICATOR STANDARD

---

### 一、 核心变量与每日参数规范 (IMMUTABLE PARAMETERS)

Gem 在生成每日富途指标代码或向用户提供参数时，必须严格使用以下 5 大变量命名：

1. **`RES_4H`**  : 4H 宏观阻力天花板 (4H Major Res)
2. **`PMH_VAL`** : 盘前最高价 (PMH)
3. **`POC_VAL`** : 盘前主力公允成本重心 (Premarket POC 🎯)
4. **`PML_VAL`** : 盘前多头生命线 (PML)
5. **`SUP_4H`**  : 4H 宏观铁底支撑 (4H Major Sup)

---

### 二、 信号去重与降噪机制 (ANTI-CLUTTER FILTER)

为了防止连续多根 5m K 线重复触发导致图表文字挤压重叠，指标内置 **`FILTER(Signal, 3)`** 降噪机制：

- **防重叠规则**: 同一类型信号在 3 根 K 线周期内仅允许打印 1 次最高优先级标签。
- **关键防区容差 (`ZONE_TOL := 0.003`)**: 仅在距离 5 大关键线 $\pm 0.3\%$ 范围内触发信号，无人区杂音一律物理过滤。

---

### 三、 盘面视觉标签体系 (VISUAL HIERARCHY)

| 标签文本 | 触发逻辑 | 颜色与位置 | 含义 |
|---|---|---|---|
| **`🚀TEST`** | 地量缩量回踩 POC / PML (`VOL_06X`) | 金色 / K 线下方 | 极佳低风险顺势做多买点 |
| **`🛑TEST`** | 地量缩量测试 4H Res / PMH | 灰色 / K 线上方 | 阻力位无需求测试 |
| **`▲CALL`** | 关键位放量吸收或突破 (`VOL_14X`) | 青色 / K 线下方 | 猎手异动，多头推进 |
| **`▼PUT`** | 阻力位放量派发或破位 (`VOL_14X`) | 红色 / K 线上方 | 空头异动，破位警戒 |
| **`★BUY_APEX`** | 天量吸收或放量战役总攻 (`VOL_20X`) | 绿色 / K 线下方 | 刺客决战总攻做多 |
| **`★VETO_EXIT`** | 天量长上影派发 (UPTHRUST, `VOL_20X`)| 红色 / K 线上方 | **终极一票否决，多头清仓离场 🛑** |

---

### 四、 主图画线标准定义 (DRAWING STANDARDS)

- **`RES_LINE`** : 红色实线 (`COLORRED, LINETHICK2`)
- **`PMH_LINE`** : 粉色虚线 (`COLORMAGENTA, DOTLINE`)
- **`POC_LINE`** : 金色实线 (`COLORYELLOW, LINETHICK2`) ➔ 今日核心做多中枢 🎯
- **`PML_LINE`** : 青色虚线 (`COLORCYAN, DOTLINE`) ➔ 多头生命线
- **`SUP_LINE`** : 绿色实线 (`COLORGREEN, LINETHICK2`)
