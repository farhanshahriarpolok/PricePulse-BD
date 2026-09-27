# PricePulse BD — Live Demonstration Script (Viva Defense Walkthrough)
**Duration:** 5 to 7 Minutes  
**Target Audience:** Final Year CSE Examination Committee & External Examiners  
**Presenter:** Farhan Shahriar Polok (Student ID: 2021-CSE-048)  

---

## Pre-Demo Checklist (T-Minus 5 Minutes)
1. Ensure the Python virtual environment is ready:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
2. Verify seeded database and demo history are present:
   ```powershell
   python scripts/generate_demo_history.py
   ```
3. Launch the unified system orchestrator:
   ```powershell
   python run_system.py
   ```
   *(Access frontend dashboard at `http://localhost:3000` or single-port unified server at `http://localhost:8000`)*.
4. Have the browser open in full screen (F11) with zoom set to 100%.

---

## Step 1: System Launch & Macro Market Pulse (Time: 0:00 - 1:00)

### What to Click:
- Open the landing page (`http://localhost:3000`).
- Ensure the **Market Pulse** tab is active in the top navigation bar.

### Spoken Script:
> *"Respected committee members, this is PricePulse BD—a location-aware multi-source market price intelligence platform for essential commodities in Bangladesh.*
>
> *At the top of the interface, you can see our real-time system status indicator connected to our local-first FastAPI backend with SQLite Write-Ahead Logging. The top KPI cards summarize current market health across 4 core monitored staples: Coarse Rice, Local Onion, Potato, and Soybean Oil.*
>
> *Notice our macro market health index and retail spread: physical retail prices currently trade at a 15.4% average markup over primary wholesale terminal markets, while online grocery delivery averages an additional 4.2% markup. The system actively flags that 1 commodity currently exhibits a critical price anomaly."*

---

## Step 2: Bilingual Realtime Price Search (Time: 1:00 - 2:15)

### What to Click:
- In the search bar on the Market Pulse view, type: `পেঁয়াজ` (Bengali Unicode).
- Observe the instant price resolution card appear with channel breakdown.
- Next, clear and type: `onion` (English phonetic).
- Press the keyboard shortcut `Ctrl + K` to demonstrate quick keyboard-driven search navigation.

### Spoken Script:
> *"A primary obstacle in South Asian civic informatics is orthographic fragmentation. Consumers and market enumerators query products in both Bengali script and English phonetic transliterations.*
>
> *Watch as I search in standard Bengali script: `পেঁয়াজ`. The backend normalizer executes Unicode NFKC sanitization and alias dictionary resolution within 15 milliseconds, mapping it to the canonical 'Local Onion' entity.*
>
> *Now I type `onion` in English. The exact same canonical entity resolves seamlessly. The card immediately displays today's modal price of 98.0 BDT/kg, showing the channel breakdown: wholesale terminal price at 85 BDT/kg versus urban physical retail at 98 BDT/kg, marked with an active 'CRITICAL SPIKE' alert badge."*

---

## Step 3: Anomaly Monitor & Natural Language Explanation (Time: 2:15 - 3:30)

### What to Click:
- Click on the **Anomaly Monitor** tab in the navigation bar.
- Point to the active alert card for **Local Onion (দেশি পেঁয়াজ)**.
- Highlight the **Plain-Language Explanation** callout box at the bottom of the card.

### Spoken Script:
> *"Now we transition to our explainable statistical anomaly detection engine.*
>
> *Unlike opaque deep learning models or black-box neural networks where predictions cannot be legally audited, PricePulse BD uses a parametric Compound Anomaly Decision Rule: an alert triggers if and only if both the statistical Z-score threshold (|Z| >= 1.5) and the economic percentage departure (|Delta%| >= 10%) are breached simultaneously.*
>
> *Here, Local Onion is flagged under a 'CRITICAL SPIKE' tier. The current market price of 98.0 BDT/kg represents a +50.3% departure from its 14-day rolling moving average of 65.2 BDT/kg, yielding a statistical Z-score of +17.98.*
>
> *Crucially, our deterministic natural language engine automatically synthesizes an auditable sentence: 'ALERT: Local Onion has surged by 50.3% above its 14-day baseline of 65.2 BDT/kg... This sharp movement violates historically low volatility (CV: 2.8%), indicating artificial supply restriction or severe hoarding.' This enables non-technical market directors or regulatory inspectors to immediately take enforcement action."*

---

## Step 4: Commodity Explorer & 30-Day Historical Trend (Time: 3:30 - 4:30)

### What to Click:
- Click on the **Commodity Explorer** tab.
- Select **Local Onion** from the commodity dropdown.
- Toggle the historical chart view to examine the 30-day chronological curve against the 14-day SMA baseline.
- Hover over the data points between Day 25 and Day 30 to display interactive tooltip metrics.

### Spoken Script:
> *"Under the Commodity Explorer tab, we visualize the temporal price trajectory rendered via Recharts.*
>
> *The solid indigo curve represents daily observed market prices, while the dashed amber curve traces the dynamically smoothed 14-day Simple Moving Average baseline. Observe how the price remained stable between 64 and 66 BDT/kg during the first 25 days with negligible volatility.*
>
> *On Day 26, a simulated cross-border supply shock occurs: the price abruptly breaks out from the baseline corridor, indicated by red pulsating anomaly markers. The statistical summary panel below computes the live rolling metrics: standard deviation, Z-score, and historical minimum and maximum price points."*

---

## Step 5: Bangladesh Interactive Price Map & Spatial Spread (Time: 4:30 - 5:30)

### What to Click:
- Click on the **Bangladesh Map** tab.
- Select **Local Onion** as the commodity filter.
- Zoom in and pan across Bangladesh on the Leaflet map.
- Click on the district markers for **Pabna** (cheapest farm-gate hub) and **Dhaka** (highest consumption center).
- Point to the Spatial Spread KPI callout card on the left panel.

### Spoken Script:
> *"Market prices in Bangladesh are profoundly spatial. In this view, we render an interactive Leaflet geospatial map using zero-cost OpenStreetMap tiles and simplified Bangladesh district GeoJSON polygon boundaries.*
>
> *The system dynamically computes the spatial spread across regional wholesale hubs: Pabna is highlighted in green as the cheapest national market at 62.0 BDT/kg (near the producing farm gates), while Kawran Bazar in Dhaka is highlighted in red at 98.0 BDT/kg.*
>
> *The spatial analytics engine calculates an inter-district geographic markup of 58.1% (a 36.0 BDT/kg spread). When markups exceed our 35% threshold, the system flags a spatial transmission inefficiency, pointing directly to exorbitant transit extortion or localized intermediary hoarding."*

---

## Step 6: Data Provenance Verification & Viva Shield Mode (Time: 5:30 - 6:30)

### What to Click:
- Click on the **Data Provenance** tab (or click the 'Audit Provenance' button on any observation card).
- Inspect the four-factor confidence score breakdown (Source: 0.90, Alias: 0.90, Freshness: 1.00, Completeness: 1.00 -> Composite Score: 0.94).
- Open terminal and show that `pricepulse.db` operates in full local WAL mode without requiring any internet connection.

### Spoken Script:
> *"Finally, we address data integrity and audit provenance. In civic governance, an unverified number is worse than no number at all.*
>
> *Our Provenance Drawer displays the complete lineage of each quote: raw unparsed input, publisher authority rating, semantic match certainty, temporal freshness decay, and structural attribute completeness. Every observation carries a normalized confidence metric C in [0.0, 1.0].*
>
> *Furthermore, as demonstrated here, the entire system is 'local-first'—built on SQLite WAL concurrency, FastAPI, and React. If internet connectivity drops during an inspection or viva defense, PricePulse BD operates at 100% functionality from local storage with zero cloud latency.*
>
> *Thank you, respected examiners. I now welcome your questions."*
