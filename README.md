# 💥 Coal Mine Explosions & Safety Intelligence System

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Database](https://img.shields.io/badge/Database-SQLite3-003B57.svg)](https://www.sqlite.org/)
[![Data Source](https://img.shields.io/badge/Data%20Source-DGMS%20SANKET-orange.svg)](https://dgms.gov.in/)
[![Zero External Dependencies](https://img.shields.io/badge/Dependencies-Standard%20Library-brightgreen.svg)]()

An interactive safety intelligence dashboard, relational database, and deterministic Q&A engine analyzing **Coal Mine Explosions, Combustible Coal Dust, and Inflammable Gas Disasters** in India. Built for the 4th-Year B.Tech Mining Environmental Engineering curriculum.

Based on the official 316-page publication by the **Directorate General of Mines Safety (DGMS)**: *SANKET (2016–2022)* and historical Indian mining disaster archives (1901–2022).

---

## 📌 Project Highlights

- **Zero-Hallucination Query Engine:** Uses deterministic SQL lookups and domain physics retrieval instead of unpredictable LLM inferences.
- **120+ Years of Official Mining Data:**
  - **48 Major Explosion Disasters (1901–2022, $\ge 4$ deaths):** Documenting **1,361 miners killed**.
  - **19 In-Depth Investigative Cases (2016–2022):** Documenting **23 fatalities**, 12 serious injuries, physical failure mechanisms, and Coal Mines Regulations (CMR) statutory violations.
  - **19 Statutory Courts of Inquiry:** Inquiries instituted under Section 24 of the Mines Act, 1952.
- **6 Operational Root Cause Taxonomies:** Classifies real-world failures into actionable engineering categories.
- **Zero External Dependencies:** Built entirely with Python's standard library (`sqlite3`, `http.server`, `socketserver`, `json`, `urllib`). No complex setup required.

---

## 🚀 Quick Start

### 1. Launch the Interactive Web Dashboard
Clone the repository and run the built-in server:
```bash
python server.py
```
Open your browser and navigate to:
```
http://localhost:8000
```
- **Live KPI Counters:** Historical fatalities, recent cases, and inquiry counts.
- **Clickable Question Chips:** One-click queries for common professor questions.
- **Interactive Visualizations:** Chart.js bar and doughnut charts.
- **Instant Search:** Real-time client-side filtering across all 4 data registers.

### 2. Run the Command-Line Interface (CLI)
For a terminal-based presentation:
```bash
python query_tool.py
```
Select any numbered option (`1` to `9`) or type a custom query.

---

## 📊 Key Statistics at a Glance

| Category | Count | Key Takeaway |
| :--- | :---: | :--- |
| **Historical Major Disasters (1901–2022)** | **48** | **1,361 miners killed** in incidents involving $\ge 4$ deaths. |
| **Deadliest Indian Explosion Disaster** | **1** | **Dhori Colliery (28.05.1965)**: **268 killed** (Coal Dust Explosion). |
| **Decadal Accidents: Dust & Gas (Code 0700)** | **10 Fatal** | 1.9% share of all fatal accidents in Indian coal mines (2013–2022). |
| **Decadal Accidents: Explosives (Code 0500)** | **12 Fatal** | 2.3% share of all fatal accidents in Indian coal mines (2013–2022). |
| **Recent Investigated Cases (2016–2022)** | **19** | **23 killed**, 12 seriously injured across 6 root causes. |
| **Courts of Inquiry Instituted** | **19** | Inquiries under Section 24 of the Mines Act, 1952 (1,093 fatalities). |

---

## 🔍 Root Cause Breakdown (2016–2022 Cases)

| Operational Root Cause | Incidents | Deaths | Primary Regulations Violated | Example Collieries |
| :--- | :---: | :---: | :--- | :--- |
| **Inadequate Ventilation & Gas Inundation** | **5** | **8** | CMR 2017 Reg 153(2) / CMR 1957 Reg 130 | Bagdewa, Godavari Khani No. 1, Chora |
| **Deep Hole & Secondary Blasting** | **4** | **7** | CMR 2017 Reg 164, 168 & 204 | Ramagundam OC-I (4 killed), Keshalpur |
| **Drilling into Misfired Shotholes** | **3** | **3** | CMR 2017 Reg 203 & 204 | Kurasia, Ravindra Khani No. 5, Manikpur |
| **Spontaneous Combustion & Active Fires** | **3** | **3** | CMR 2017 Reg 136 & 142 | Selected Dhori, Dipka OC, Salanpur |
| **Surface Workshop Gas Explosions** | **2** | **3** | CMR 2017 Reg 83 / Factories Act | Jhanjhra Workshop, Dudhichua OC |
| **Solid Blasting Igniting Methane** | **1** | **1** | CMR 2017 Reg 204(2) / CMR 1957 Reg 175(2) | Chhatarpur Mine No. 1 |

---

## 📁 Repository Structure

```text
├── README.md                            # Project overview & documentation
├── PROJECT_HANDOVER_AND_METHODOLOGY.md  # Detailed technical methodology & handover notes
├── viva_cheat_sheet.md                  # High-yield exam scripts, formulas, and CMR rules
├── server.py                            # Native Python HTTP server & REST API
├── index.html                           # Modern safety intelligence web dashboard
├── qa_engine.py                         # Dual SQL analytics & domain science Q&A engine
├── query_tool.py                        # Interactive terminal query tool
├── build_database.py                    # SQLite database generation script
├── mine_explosions.db                   # Populated SQLite database (5 relational tables)
├── parse_sanket_full.py                 # PyMuPDF data extraction pipeline from SANKET
├── coal_mine_explosions_sanket_data.md  # 850-line master text dataset
├── sanket0404_2024.pdf                  # Official DGMS publication (2016–2022)
├── explo.docx                           # Mine explosion thermodynamics notes
├── requirements.txt                     # Minimal dependencies (PyMuPDF for extraction)
└── .gitignore                           # Standard Python gitignore
```

---

## 🧪 Engineering Science & Statutory Standards

- **Methane Flammability Envelope:** LEL = **5.0%**, UEL = **15.0%**, Stoichiometric Optimum = **9.5% $\text{CH}_4$** (produces peak pressure of 7–8 bar).
- **Coward Diagram Threshold:** Methane cannot explode if atmospheric oxygen is below **12.1%**, regardless of methane percentage.
- **Coal Dust Explosibility:** Minimum Explosive Concentration (MEC) = **30 to 50 $\text{g/m}^3$** for particles $< 75\ \mu\text{m}$ when volatile matter $\ge 14\%$.
- **Hybrid Mixture Multiplier:** The presence of just **1.0% $\text{CH}_4$** reduces the Lower Explosive Limit of coal dust by more than **50%**.
- **Statutory Stone Dusting (CMR 2017 Reg 144):** Minimum **75% incombustible matter** in all roadway dust samples ($\ge 85\%$ in gassy seams).

---

## 📖 Key Documentation

- For step-by-step documentation from raw PDF extraction to system architecture: see [`PROJECT_HANDOVER_AND_METHODOLOGY.md`](PROJECT_HANDOVER_AND_METHODOLOGY.md).
- For rapid viva preparation and spoken defense scripts: see [`viva_cheat_sheet.md`](viva_cheat_sheet.md).

---

## ⚖️ License & Attribution
Academic research project developed for the Mining Environmental Engineering course. Data sourced from official publications of the **Directorate General of Mines Safety (DGMS)**, Ministry of Labour & Employment, Government of India.
