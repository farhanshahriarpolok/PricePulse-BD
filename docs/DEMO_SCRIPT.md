# PricePulse BD — Commercial Live Demonstration Script
**Duration:** 6 to 8 Minutes  
**Audience:** Technical Evaluation Committee, Enterprise Observers, and Civic Tech Stakeholders  
**Presenter:** Farhan Shahriar Polok (Lead Researcher & Engineer)  
**System Version:** `v2.0.0` (National Production Release)

---

## Pre-Demo Checklist (T-Minus 5 Minutes)
1. Ensure the Python virtual environment is active:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
2. Run automated environment validation:
   ```powershell
   python run_system.py --test
   ```
   *(Confirm 4/4 checks pass: Python Runtime, SQLite WAL, Data Fixtures, REST API)*.
3. Launch the unified platform runner:
   ```powershell
   python run_system.py
   ```
   *(Frontend live at `http://localhost:3000`, FastAPI gateway at `http://localhost:8000`)*.
4. Have the web browser set to full screen (`F11`) with zoom set to 100%.
5. (Optional) Launch Android Studio emulator or connect physical Android device running `android/` debug build.

---

## Step 1: Market Pulse & 7d Sparkline Cards (Top Mover Hero Card)
**Time: 0:00 - 1:15**

### What to Click & Show:
- Navigate to the **Market Pulse** landing page (`http://localhost:3000`).
- Point to the **Top Mover Hero Card** displaying the staple experiencing the highest 24h / 7d relative volatility.
- Hover over the 7-day sparkline curve to reveal the dynamic tooltip displaying daily modal price deviations.
- Demonstrate bilingual search in the top search bar:
  1. Type Bengali Unicode: `পেঁয়াজ` $\to$ instant modal resolution to **Local Onion (দেশি পেঁয়াজ)** in $< 15\text{ ms}$.
  2. Clear and type English phonetic: `onion` $\to$ identical canonical entity resolution.
  3. Press `Ctrl + K` to demonstrate keyboard navigation.

### Spoken Script:
> *"Good day, everyone. This is PricePulse BD—a sovereign, local-first commodity market intelligence and anomaly detection platform for Bangladesh.
>
> On our landing dashboard, you see real-time market telemetry monitoring 21 canonical essential staples across 64 administrative districts and 78 verified markets. At the top, our Top Mover Hero Card immediately identifies which staple is under severe price pressure today, complete with a 7-day sparkline price trajectory.
>
> South Asian agricultural data is notoriously fragmented across languages and scripts. Watch as I query in Bengali Unicode: 'পেঁয়াজ'—the system performs NFKC normalization and canonical alias resolution in under 15 milliseconds. If I switch to phonetic English 'onion', the exact same canonical record resolves instantly, displaying wholesale, wet-market retail, and online channels with zero ambiguity."*

---

## Step 2: Consumer Bazaar Basket (3-Channel Savings & 30d CPI Trend)
**Time: 1:15 - 2:30**

### What to Click & Show:
- Click on the **Bazaar Basket** tab in the navigation bar.
- Add staple commodities to the interactive shopping basket:
  - Coarse Rice: `10 kg`
  - Local Onion: `2 kg`
  - Soybean Oil: `2 liters`
  - Broiler Chicken: `2 kg`
- Highlight the **3-Channel Cost Comparison Matrix**:
  - Wholesale Terminal Hub (Kawran / Khatunganj)
  - Wet Market Retail
  - Online Super-shop (Chaldal)
- Point to the **Smart Savings Card**: highlights total household savings (e.g., ৳140–৳220 saved vs retail baseline).
- Click **"আমার বাজার সংরক্ষণ করুন" (Save Basket)** to save the customized basket.
- Click on **"ব্যক্তিগত মূল্যস্ফীতি ট্রেন্ড" (30-Day Personal CPI Trend)** to view the personal inflation graph and volatility index ($CV\%$).

### Spoken Script:
> *"Next, we look at the Consumer Bazaar Basket engine. Traditional government price indices report aggregate macro inflation, which does not reflect the actual out-of-pocket reality for a family purchasing their weekly staples.
>
> In the Bazaar Basket view, consumers configure their family's typical grocery items. Our calculus engine instantaneously runs a multi-channel price comparison: wholesale hubs, wet-market retail, and online grocery delivery.
>
> For this representative 4-person weekly basket, the system calculates a direct ৳185 saving if staples are sourced through wholesale cooperatives rather than local corner shops. Consumers can save their customized baskets permanently. Our personal CPI trend tracker computes a tailored 30-day inflation rate and Coefficient of Variation for this exact household diet, delivering clear, actionable consumer advocacy."*

---

## Step 3: Market Stress Test Sandbox (Dynamic Shock Slider without DB Mutation)
**Time: 2:30 - 3:45**

### What to Click & Show:
- Click on the **Market Stress Test** tab in the navigation bar.
- Select **Local Onion (দেশি পেঁয়াজ)** from the commodity dropdown.
- Point out the current equilibrium baseline ($65.2\text{ BDT/kg}$, $14$-day SMA, historical $CV = 2.8\%$).
- Drag the **Simulated Shock Slider** from `0%` to `+50%`:
  - Observe the simulated price immediately jump from $65\text{ BDT/kg}$ to $98\text{ BDT/kg}$.
  - The calculated Z-score surges dynamically to $+17.98$.
  - The status badge transitions from `NORMAL` $\to$ `CRITICAL SPIKE`.
  - The deterministic natural language engine generates an auditable justification sentence in real time.
- Emphasize that `pricepulse.db` is **not modified**—the simulation operates strictly in ephemeral sandbox memory.

### Spoken Script:
> *"A hallmark of PricePulse BD's analytical robustness is our Market Stress Test Sandbox. Policy makers and market analysts frequently need to evaluate: 'What happens to consumer prices if an export tariff or fuel price hike increases landed costs by 40%?'
>
> Watch as I drag this shock slider to +50% for Local Onion. The interface instantly recomputes the 14-day rolling moving average, standard deviation, and Z-score in-memory. The Z-score surges to +17.98, breaching our compound threshold (|Z| >= 2.5 and |Delta%| >= 10%), triggering a Critical Spike alert.
>
> Crucially, our architecture enforces strict sandbox isolation: this simulation runs entirely on ephemeral memory. The SQLite ground-truth database remains pristine. Furthermore, the explanation text is generated through deterministic mathematical synthesis, completely free of cloud LLMs or non-auditable hallucinations."*

---

## Step 4: 64-District Leaflet Map with Highway Transit Corridors
**Time: 3:45 - 5:00**

### What to Click & Show:
- Click on the **Bangladesh Map** tab.
- Select **Local Onion** or **Potato** as the commodity filter.
- Observe the nationwide 64-district choropleth colored by average market price.
- Toggle the **"Highway Transit Corridors" (হাইওয়ে ট্রানজিট করিডোর)** switch on the map toolbar.
- Point to the animated highway polylines connecting northern farm gates to metropolitan consumption centers:
  1. **N5 Jamuna Corridor (Bogura/Rangpur $\to$ Dhaka):** Click polyline to open the glassmorphic Arbitrage Drawer.
     - Waypoints through Sirajganj, Bangabandhu Jamuna Bridge, Tangail, Gazipur.
     - Distance: $228\text{ km}$, Transit Duration: $6.3\text{ h}$ (at $45\text{ km/h}$ cruise + $1.2\text{ h}$ bridge buffer).
     - Freight Breakdown: Base loading ৳1.50 + Mileage ৳4.10 + Jamuna Toll Buffer ৳0.50 = ৳6.10/kg.
     - Feasibility Badge: **Highly Feasible** (Net Margin $\ge 6.00\text{ BDT/kg}$).
  2. **N8 Padma Corridor (Jashore $\to$ Dhaka):** Click polyline to show Mawa Expressway & Padma Bridge waypoints, $0.8\text{ h}$ buffer, ৳0.60 toll buffer.

### Spoken Script:
> *"Agricultural prices in Bangladesh are inherently spatial. Under the Bangladesh Map tab, we render a complete 64-district Leaflet choropleth using vector boundaries and 78 market nodes.
>
> Notice our interactive Highway Transit Corridor layer. Instead of assuming naive straight-line flight paths, PricePulse BD models actual national highway topography with empirical circuity (kappa = 1.25).
>
> When I click the N5 Jamuna Corridor from Bogura to Dhaka, the drawer displays the exact route: distance of 228 kilometers, estimated 6.3 hours transit time at 45 km/h commercial cruising speed, and a freight cost breakdown including fixed loading fees, mileage wear, and the Bangabandhu Jamuna Bridge toll buffer of ৳0.50/kg.
>
> Because the wholesale price difference between Bogura and Dhaka exceeds total freight by over ৳8.00/kg, the corridor is classified as 'Highly Feasible' with an estimated commercial ROI of 32%. This enables fair supply chain routing and uncovers localized middleman arbitrage."*

---

## Step 5: Upstream Source Health Telemetry & Zero-Downtime Fallback
**Time: 5:00 - 6:00**

### What to Click & Show:
- Click on the **System Health** indicator in the navbar or open `/api/v1/health` and `/api/v1/sources/health`.
- Show the 4 upstream data source telemetry cards:
  1. **TCB Daily Bulletins** (Trading Corporation of Bangladesh)
  2. **DAM Live Market Sheet** (Department of Agricultural Marketing)
  3. **Press Field Spot Reports** (Prothom Alo & Daily Star field roundups)
  4. **Chaldal Online Catalog** (Digital e-grocery)
- Highlight the **Zero-Downtime Resilience Fallback**: demonstrate that when upstream network connections are unavailable, collectors gracefully fall back to verified cached bulletins and offline fixtures without crashing or blocking the event loop.

### Spoken Script:
> *"A persistent issue with civic scrapers is upstream volatility: government web portals frequently encounter downtime, DOM layout restructuring, or network drops.
>
> In our Source Health telemetry panel, PricePulse BD continuously monitors all four ingestion channels. Our collectors feature adaptive DOM selectors, regex pattern transliteration matrices, and exponential retry backoff with randomized jitter.
>
> If a source endpoint becomes temporarily unreachable, the pipeline falls back seamlessly to immutable cached bulletins and local fixtures. The user-facing dashboard never experiences a white-screen crash or unhandled 500 error. Every single price quote carries a four-factor confidence score rating authority, freshness, and match certainty."*

---

## Step 6: Native Android Client Offline Mirroring & Audit Lineage
**Time: 6:00 - 7:00**

### What to Click & Show:
- Showcase the **Native Android Client** (`android/`):
  - Launch the app in offline mode (airplane mode enabled).
  - Open the **Bazaar Basket** screen in Jetpack Compose: demonstrates instantaneous loading from local Room SQLite database in $< 15\text{ ms}$.
  - Demonstrate the custom Compose Canvas bezier trend chart with smooth 120 FPS touch-drag crosshairs.
- On the web dashboard, open the **Data Provenance Drawer** on any observation card to display the complete mathematical confidence score breakdown:
  $$C = 0.40 \cdot C_{\text{src}} + 0.25 \cdot C_{\text{alias}} + 0.20 \cdot C_{\text{fresh}} + 0.15 \cdot C_{\text{comp}}$$

### Spoken Script:
> *"To conclude our demonstration, we highlight our zero-latency offline client and cryptographic data lineage.
>
> For mobile field officers and consumers in areas with intermittent cellular coverage, our Native Android Client is written entirely in modern Kotlin with Jetpack Compose and Room SQLite. Because data is synchronized locally, cold-start queries execute in under 15 milliseconds, and our custom Compose Canvas chart delivers a silky 120 frames per second without third-party chart bloat.
>
> Finally, every number in PricePulse BD is fully traceable. In our Data Provenance drawer, inspectors can audit the source authority, alias match confidence, temporal freshness decay, and field completeness score. 
>
> PricePulse BD is fully built, backed by 236 passing automated tests, completely local-first, and ready for deployment. Thank you, and I look forward to your questions."*

