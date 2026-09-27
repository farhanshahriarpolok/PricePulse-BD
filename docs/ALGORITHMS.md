# Mathematical & Statistical Analytics Algorithms

## 1. Overview & Academic Rationale

PricePulse BD rejects black-box machine learning models in favor of deterministic, explainable statistical methods. In public commodity intelligence and agricultural economic monitoring, stakeholders require clear mathematical derivations and human-auditable decision rules to verify price shocks, hoarding signals, and spatial market dislocations.

Every metric in the analytics pipeline can be traced directly to foundational formulas in time-series statistics and spatial price dispersion.

---

## 2. Statistical Baseline & Anomaly Detection Formulation

### 2.1 Rolling Simple Moving Average (SMA)
To establish an adaptive baseline that absorbs day-to-day market volatility, the engine calculates Rolling Simple Moving Averages across three canonical temporal windows: short-term (7 days), medium-term (14 days), and baseline trend (30 days).

For an observation date $t$ and a temporal window $k \in \{7, 14, 30\}$:

$$\text{SMA}_k(t) = \frac{1}{k} \sum_{i=0}^{k-1} P_{t-i}$$

Where $P_{t-i}$ represents the daily normalized volume-weighted price on day $t-i$. In operational anomaly monitoring, the **14-day window ($\text{SMA}_{14}$)** serves as the primary benchmark, balancing responsiveness to structural seasonal shifts against resilience to transient micro-fluctuations.

---

### 2.2 Sample Standard Deviation ($\sigma$)
To measure historical price dispersion around the moving baseline, the engine computes the unbiased sample standard deviation over the corresponding 14-day history:

$$\sigma_{14}(t) = \sqrt{\frac{1}{k-1} \sum_{i=1}^{k} \left(P_{t-i} - \text{SMA}_{14}(t)\right)^2}, \quad k = 14$$

Using Bessel's correction ($k - 1$) ensures an unbiased estimator for finite-sample price windows.

---

### 2.3 Standard Score ($Z$-Score)
The $Z$-score measures how many standard deviations the current observed price $P_t$ deviates from the 14-day historical baseline:

$$Z(t) = \frac{P_t - \text{SMA}_{14}(t)}{\sigma_{14}(t)}$$

Properties:
- $Z = 0$: Price exactly matches historical mean.
- $Z > +1.5$: Price significantly higher than historical distribution.
- $Z < -1.5$: Price significantly lower than historical distribution.

---

### 2.4 Volatility Coefficient of Variation ($\text{CV}$)
To distinguish commodities that naturally exhibit wide trading spreads (such as perishable green chillies) from highly stable staples (such as bottled edible oils), the engine computes the relative volatility coefficient:

$$\text{CV}_{14}(t) = \left(\frac{\sigma_{14}(t)}{\text{SMA}_{14}(t)}\right) \times 100\%$$

A commodity with a baseline $\text{CV} \le 5\%$ is classified as low-volatility, whereas $\text{CV} \ge 15\%$ flags elevated intrinsic volatility.

---

### 2.5 Percentage Deviation ($\Delta\%$)
The relative percentage shift from the moving average baseline is computed as:

$$\Delta\%(t) = \left(\frac{P_t - \text{SMA}_{14}(t)}{\text{SMA}_{14}(t)}\right) \times 100\%$$

---

## 3. Compound Anomaly Decision Matrix

A common limitation of single-variable $Z$-score models in commodity markets is false positives during periods of extreme price stability (where $\sigma \to 0$, causing inflated $Z$-scores for trivial BDT fluctuations).

PricePulse BD implements a **Compound Anomaly Rule** requiring both statistical distance ($|Z| \ge 1.5$) **and** meaningful economic percentage deviation ($|\Delta\%| \ge 10.0\%$):

$$\text{IsAnomaly}(t) = \left(|Z(t)| \ge 1.5\right) \land \left(|\Delta\%(t)| \ge 10.0\%\right)$$

### Classification & Severity Matrix

| Severity Level | Mathematical Trigger Conditions | Direction | Market Interpretation |
| :--- | :--- | :--- | :--- |
| **Normal** | $|Z| < 1.5$ OR $|\Delta\%| < 10.0\%$ | N/A | Market in equilibrium; normal seasonal drift. |
| **Moderate** | $|Z| \ge 1.5$ AND $|\Delta\%| \ge 10.0\%$ | Spike / Drop | Noticeable deviation; early indicator of localized supply tightness. |
| **Severe** | $|Z| \ge 2.0$ AND $|\Delta\%| \ge 20.0\%$ | Spike / Drop | Significant market dislocation; cross-market arbitrage stress. |
| **Critical** | $|Z| \ge 2.5$ AND $|\Delta\%| \ge 30.0\%$ | Spike / Drop | Severe supply breakdown or speculation; immediate regulatory review threshold. |

---

## 4. Rule-Based Natural Language Explanation Generation

Rather than providing arbitrary confidence scores, the system synthesizes human-readable justifications following deterministic grammatical templates:

```python
Template:
"Anomalous market pressure detected: {commodity} experienced a {severity} {direction_label} "
"reaching {current_price} on {date}. This reflects a {delta_pct} {movement} over its "
"14-day baseline moving average of {baseline_sma}. The deviation is statistically "
"significant at Z = {z_score} (σ = {std_dev}), surpassing the commodity's historical "
"volatility envelope of {cv}%."
```

This guarantees complete traceability for university capstone presentations, researchers, and field consumers.

---

## 5. Spatial Price Dispersion & Inter-District Geo-Spread

To evaluate geographical market fragmentation across Bangladesh's administrative divisions, the spatial engine aggregates observations by market node $m$ and district $d$.

### Absolute Spatial Spread ($\Delta_{\text{spatial}}$)
Given the set of market average prices $\{P_{m_1}, P_{m_2}, \dots, P_{m_n}\}$ on calendar date $t$:

$$\Delta_{\text{spatial}}(t) = \max_{m}(P_m) - \min_{m}(P_m)$$

### Relative Percentage Geo-Spread ($S_{\text{geo}}$)
The spatial markup relative to the lowest available market benchmark:

$$S_{\text{geo}}(t) = \left(\frac{\max_{m}(P_m) - \min_{m}(P_m)}{\min_{m}(P_m)}\right) \times 100\%$$

### GeoJSON Enrichment
Calculated district-level metrics are mapped onto simplified Bangladesh administrative boundary centroids:
- `has_data`: Boolean flag indicating report presence.
- `avg_price`: Mean trading price within district.
- `market_count`: Number of reporting wholesale and retail centers.
- Leaflet map visualization colors districts dynamically using quantile or threshold chloropleth intervals.
