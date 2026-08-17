# 01_VPA_FORENSIC_DICTIONARY
## 4H + 1H QUANTITATIVE VPA MATHEMATICAL & LOGIC DICTIONARY

---

### 一、 核心物理量化特征定义 (FEATURE ENGINEERING)

1. **Spread (K 线真实价差)**: 
   `Spread = High - Low` (若 Spread == 0，则置为 0.0001 防止除零)
2. **Body (实体大小)**: 
   `Body = |Close - Open|`
3. **Upper Wick (上影线)**: 
   `Upper_Wick = High - max(Open, Close)`
4. **Lower Wick (下影线)**: 
   `Lower_Wick = min(Open, Close) - Low`
5. **Upper Wick Ratio (上影线比例)**: 
   `Upper_Wick_Ratio = Upper_Wick / Spread`
6. **Lower Wick Ratio (下影线比例)**: 
   `Lower_Wick_Ratio = Lower_Wick / Spread`
7. **Close Position (收盘分位)**: 
   `Close_Pos = (Close - Low) / Spread` (0.0 为最低点，1.0 为最高点)
8. **RVol (相对成交量倍数)**: 
   `RVol = Volume / 20周期均量(MA20_Vol)`

---

### 二、 5 大核心量价形态物理判据 (THE 5 VPA SIGNATURES)

#### 1. 底部多头吸收 (STOPPING VOLUME 📈)
- **触发条件**:
  - `RVol >= 1.8x` (天量或猎手巨量)
  - `Lower_Wick_Ratio >= 0.40` (显著下影线 $\ge 40\%$)
  - `Close_Pos >= 0.33` (收盘脱离最低点，处于 K 线中上部)
- **法医含义**: 机构主力在下跌途中挂出天量买单，完全吸收散户恐慌抛盘，构成铁底强支撑。

#### 2. 顶部见顶派发 (UPTHRUST / TOPPING OUT 🛑)
- **触发条件**:
  - `RVol >= 1.8x` (天量诱多)
  - `Upper_Wick_Ratio >= 0.45` (显著长上影 $\ge 45\%$)
  - `Close_Pos <= 0.35` (收盘被狠狠砸回底部)
- **法医含义**: 主力拉高吸引散户追多，随后疯狂倒垃圾出货。**触发此信号拥有一票否决权 (ULTIMATE VETO 🛑)，多头必须立即平仓离场！**

#### 3. 地量真空无量测试 (LOW VOLUME TEST / NO SUPPLY 🚀)
- **触发条件**:
  - `RVol <= 0.70x` (窒息地量)
  - `Spread <= 0.70x ATR` (极窄实体价差)
  - `Close_Pos >= 0.50` (收盘稳在上半区)
- **法医含义**: 关键支撑位上浮动筹码彻底枯竭，做市商测试无抛压，顺势拉升阻力最小。**最完美的低风险顺势开仓点！**

#### 4. 放量顺势突破 (VALID BREAKOUT 🚀)
- **触发条件**:
  - `RVol >= 1.6x`
  - `Body / Spread >= 0.60` (饱满大阳线)
  - `Close > Open` 且有效击穿 4H 阻力或 PMH
- **法医含义**: 真实机构大资金发起战役总攻。

#### 5. 顺势吸筹推进 (ABSORPTION 📈)
- **触发条件**:
  - `1.2x <= RVol <= 1.5x` (均匀温和放量)
  - `Close >= Open` 且 `Upper_Wick_Ratio <= 0.25`
- **法医含义**: 主力在阻力下方有节奏地消化获利盘，为突破蓄力。

---

### 三、 终极一票否决权 (ULTIMATE VETO RULE)

- 任何多头交易计划，一旦在 15m / 5m 关键防区（如 PMH / 4H Res）检测到 **UPTHRUST (TOPPING OUT)** 闭线确认，**多头预案瞬间归零，立即认错离场 (WRONG + STOP = SAFETY 🛑)**！
