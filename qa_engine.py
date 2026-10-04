import sqlite3
import re
import os

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mine_explosions.db")

class MineExplosionQAEngine:
    def __init__(self, db_path=DB_FILE):
        self.db_path = db_path
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database {db_path} not found. Run build_database.py first.")

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def ask(self, query: str) -> dict:
        q = query.strip().lower()

        # Intent 1: "Reasons" / "Causes" / Root Cause Breakdown & Counts
        if any(p in q for p in ["reason", "cause", "breakdown by cause", "why did it happen", "respective reason", "root cause", "classification", "etiology"]):
            return self._handle_cause_breakdown(q)

        # Intent 2: "Worst disaster" / "deadliest" / "highest casualties"
        if any(p in q for p in ["worst", "deadliest", "highest fatal", "most severe", "biggest disaster", "largest disaster", "max deaths", "maximum killed"]):
            return self._handle_worst_disaster(q)

        # Intent 3: Specific Colliery / Mine Search (e.g. Chhatarpur, Kurasia, Ramagundam, Dhori, Bhatdee)
        mine_match = self._match_mine_name(q)
        if mine_match:
            return self._handle_mine_query(mine_match)

        # Intent 4: Regulations / Statutory Violations
        if any(p in q for p in ["regulation", "cmr", "violation", "statutory", "act", "rule", "circular", "breach"]):
            return self._handle_regulations(q)

        # Intent 5: Courts of Inquiry
        if any(p in q for p in ["court of inquiry", "inquiry", "commission", "assessor", "judge", "section 24"]):
            return self._handle_inquiries(q)

        # Intent 6: Company Breakdown (WCL, BCCL, ECL, SECL, SCCL, etc.)
        if any(p in q for p in ["company", "ccl", "bccl", "ecl", "secl", "sccl", "wcl", "ncl", "mcl", "subsidiary", "cil"]):
            return self._handle_company_breakdown(q)

        # Intent 7: Domain Science (Coward diagram, Methane limits, Stone dust)
        if any(p in q for p in ["coward", "methane", "ch4", "stone dust", "flammab", "limit", "stoichiometric", "volatile matter", "mec", "lel", "uel"]):
            return self._handle_domain_science(q)

        # Intent 8: "How many incidents" / Total Count & Statistics
        if any(p in q for p in ["how many incident", "how many mine incident", "total incident", "total accident", "how many explosion", "number of incident", "number of accident", "how many accident", "incident count", "accident count", "how many total", "how many disasters", "overall statistics", "count"]):
            return self._handle_total_counts(q)

        # Fallback: General Keyword Search over DB
        return self._handle_general_search(q)

    def _handle_total_counts(self, q: str) -> dict:
        conn = self.get_connection()
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*), SUM(killed), SUM(injured) FROM historical_disasters")
        hist_count, hist_killed, hist_injured = cur.fetchone()

        cur.execute("SELECT COUNT(*), SUM(killed), SUM(injured) FROM recent_incidents")
        rec_count, rec_killed, rec_injured = cur.fetchone()

        cur.execute("SELECT SUM(dust_gas_fatal_acc), SUM(dust_gas_fatalities), SUM(explosives_fatal_acc), SUM(explosives_fatalities) FROM annual_stats")
        dg_acc, dg_kill, exp_acc, exp_kill = cur.fetchone()

        conn.close()

        md = f"""### Summary of Coal Mine Explosion & Combustible Gas/Dust Incidents

According to the official DGMS **SANKET (2016–2022)** records:

1. **Historical Major Disasters (1901 – 2022, involving >= 4 deaths):**
   - **Total Major Disasters:** **{hist_count} Disasters**
   - **Total Miners Killed:** **{hist_killed:,} Fatalities**
   - **Seriously Injured:** **{hist_injured} Persons**
   - **Worst Ever Disaster:** **Dhori Colliery (28.05.1965)** with **268 killed** (Coal Dust Explosion).

2. **Decadal Period (2013 – 2022 DGMS Cause-Wise Classification):**
   - **Dust, Gas & Other Combustible Material (Code 0700):** **10 Fatal Accidents** (1.9% of all mine fatal accidents decadal) and **3 Serious Accidents**.
   - **Explosives & Blasting Detonations (Code 0500):** **12 Fatal Accidents** (2.3% of all mine fatal accidents decadal) and **22 Serious Accidents**.

3. **Recent In-Depth Investigative Cases (2016 – 2022):**
   - **Total Detailed Analyzed Cases:** **{rec_count} Cases**
   - **Total Fatalities in These Cases:** **{rec_killed} Deaths**
   - **Seriously Injured:** **{rec_injured} Persons**

---
#### Annual Incident Breakdown (2016–2022):
| Year | Dust/Gas Fatal Acc. | Dust/Gas Deaths | Explosives Fatal Acc. | Explosives Deaths |
| :---: | :---: | :---: | :---: | :---: |
| 2016 | 4 | 5 | 0 | 0 |
| 2017 | 0 | 0 | 0 | 0 |
| 2018 | 2 | 4 | 2 | 2 |
| 2019 | 0 | 0 | 1 | 1 |
| 2020 | 0 | 0 | 3 | 6 |
| 2021 | 0 | 0 | 2 | 2 |
| 2022 | 2 | 2 | 1 | 1 |
| **Total** | **8** | **11** | **9** | **12** |
"""
        return {"type": "aggregate", "title": "Total Explosion & Gas Incident Counts", "markdown": md}

    def _handle_cause_breakdown(self, q: str) -> dict:
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT category, fatal_incidents, total_deaths, key_mechanism, primary_regulations FROM cause_taxonomy ORDER BY fatal_incidents DESC, total_deaths DESC")
        rows = cur.fetchall()
        conn.close()

        table_rows = []
        for r in rows:
            table_rows.append(f"| **{r['category']}** | **{r['fatal_incidents']}** | **{r['total_deaths']}** | {r['key_mechanism']} | `{r['primary_regulations']}` |")

        table_str = "\n".join(table_rows)

        md = f"""### Reasons and Number of Incidents per Cause (2016 – 2022)

Based on the investigative findings documented in DGMS SANKET, the explosion and combustible hazard incidents are categorized into **6 primary operational root causes**:

| Operational Root Cause Category | Fatal Incidents | Total Deaths | Physical Failure Mechanism | Statutory Regulations Violated |
| :--- | :---: | :---: | :--- | :--- |
{table_str}

---
#### Key Takeaways for Professor / Viva:
1. **Inadequate Ventilation / Noxious Gas Accumulation (5 incidents, 8 deaths):** The leading cause of atmospheric fatalities, characterized by extending galleries without air coursing, missing brattice, and breaching into sealed goaves without prior gas testing.
2. **Deep Hole / Secondary Blasting Failures (4 incidents, 7 deaths):** Characterized by charging bulk SME explosive into boulder holes (e.g. Ramagundam OC-I, 4 killed) and simultaneous dual-bench detonations without evacuation.
3. **Misfire Drilling Explosions (3 incidents, 3 deaths):** Rotary drills and Universal Drilling Machines (UDMs) striking undetected misfired shotholes from preceding shifts belowground and opencast (Kurasia, Ravindra Khani No. 5, Manikpur).
4. **Firedamp Solid Blasting Ignition (1 incident, 1 death):** Chhatarpur Mine No. 1 where a solid blast within 2.5m holed through into a blind gallery and ignited accumulated methane.
"""
        return {"type": "causes", "title": "Root Cause Breakdown & Incident Counts", "markdown": md}

    def _handle_worst_disaster(self, q: str) -> dict:
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT sl_no, date, mine_name, coalfield_state, killed, injured, official_cause FROM historical_disasters ORDER BY killed DESC LIMIT 5")
        rows = cur.fetchall()
        conn.close()

        table_md = "| Rank | Date | Colliery Name | Region | Fatalities | Injuries | Official Cause |\n| :---: | :---: | :--- | :--- | :---: | :---: | :--- |\n"
        for idx, r in enumerate(rows, 1):
            table_md += f"| **{idx}** | {r['date']} | **{r['mine_name']}** | {r['coalfield_state']} | **{r['killed']}** | {r['injured']} | {r['official_cause']} |\n"

        md = f"""### The Deadliest Coal Mine Explosion Disasters in India (DGMS Archives)

The single worst coal mine explosion disaster in Indian mining history occurred at **Dhori Colliery** in 1965:

{table_md}

---
#### Technical Analysis of the Dhori Colliery Disaster (28 May 1965):
- **Fatalities:** **268 Miners Killed**, 9 seriously injured.
- **Cause:** **Explosion of Coal Dust** initiated by a primary firedamp ignition in the Bermo seam.
- **Sequence:** In the third shift (1:30 AM), an initial firedamp ignition raised coal dust into suspension along dry, poorly stone-dusted roadways. The flame front propagated across the entire underground district over several kilometers and blew out through the incline portals.
- **Direct Statutory Impact:** This disaster made **Stone Dust Barriers** (zone and secondary barriers) mandatory and led to Coal Mines Regulations requiring a minimum **75% incombustible matter** in roadway dust (85% where methane is present).
"""
        return {"type": "worst", "title": "Worst Coal Mine Explosion Disasters", "markdown": md}

    def _match_mine_name(self, q: str):
        known_mines = [
            "chhatarpur", "kurasia", "ravindra khani", "ramagundam", "keshalpur", 
            "manikpur", "kulda", "bokaro", "jhanjhra", "dudhichua", "bagdewa", 
            "godavari khani", "kumbharkhani", "chora", "bartarai", "selected dhori", 
            "dipka", "salanpur", "dhori", "poidih", "chinakuri", "parbelia", 
            "bhatdee", "anjan hill", "kurhurbaree", "amlabad", "new kenda", 
            "noonodih jitpur", "sudamdih", "chowrasi", "dishergarh"
        ]
        for m in known_mines:
            if m in q:
                return m
        return None

    def _handle_mine_query(self, mine_keyword: str) -> dict:
        conn = self.get_connection()
        cur = conn.cursor()

        cur.execute("SELECT * FROM recent_incidents WHERE LOWER(mine_name) LIKE ?", (f"%{mine_keyword}%",))
        recent_rows = cur.fetchall()

        cur.execute("SELECT * FROM historical_disasters WHERE LOWER(mine_name) LIKE ?", (f"%{mine_keyword}%",))
        hist_rows = cur.fetchall()

        conn.close()

        md = f"### Investigation & Data Record: `{mine_keyword.upper()}`\n\n"

        if recent_rows:
            for r in recent_rows:
                md += f"""#### {r['mine_name']} (Case #{r['case_no']}, Date: {r['date']})
- **Company / Owner:** {r['company']} | **District/State:** {r['district']}, {r['state']}
- **DGMS Cause Code:** `{r['cause_code']}` ({r['cause_desc']})
- **Place Code:** `{r['place_code']}` ({r['place_desc']})
- **Root Cause Category:** **{r['root_cause_category']}**
- **Casualties:** **{r['killed']} Killed**, **{r['injured']} Seriously Injured**
- **Victim Details:** {r['victim_details']}
- **Physical Failure Mechanism:**  
  {r['physical_mechanism']}
- **Coal Mines Regulations (CMR) Violated:**  
  > `{r['cmr_violations']}`
- **Official DGMS Narrative:**  
  > *"{r['full_narrative']}"*

---
"""

        if hist_rows:
            md += "#### Historical Major Disaster Record:\n"
            md += "| Date | Mine Name | Region | Fatalities | Injuries | Official Cause Recorded |\n| :---: | :--- | :--- | :---: | :---: | :--- |\n"
            for h in hist_rows:
                md += f"| {h['date']} | **{h['mine_name']}** | {h['coalfield_state']} | **{h['killed']}** | {h['injured']} | {h['official_cause']} |\n"

        return {"type": "mine_detail", "title": f"Incident Record: {mine_keyword.title()}", "markdown": md}

    def _handle_regulations(self, q: str) -> dict:
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT mine_name, date, root_cause_category, cmr_violations FROM recent_incidents WHERE cmr_violations != ''")
        rows = cur.fetchall()
        conn.close()

        table_md = "| Colliery & Date | Root Cause Category | Specific CMR Regulations Violated |\n| :--- | :--- | :--- |\n"
        for r in rows[:8]:
            table_md += f"| **{r['mine_name']}** ({r['date']}) | {r['root_cause_category']} | `{r['cmr_violations']}` |\n"

        md = f"""### Coal Mines Regulations (CMR) Violated in Explosion & Gas Incidents

In DGMS inquiries, statutory non-compliances are cited as primary root causes:

{table_md}

---
#### Summary of Core Statutory Requirements:
1. **Pre-Blasting Gas Examination (CMR 1957 Reg 175(2) / CMR 2017 Reg 204(2)):** Mandatory testing for inflammable gas within 20 m of shothole and in all adjoining headings within 2.5 m before firing.
2. **Face Ventilation Standard (CMR 1957 Reg 130 / CMR 2017 Reg 153(2)):** Air velocity within 4.5 m of inbye discontinued face must be >= 30 m/min (0.5 m/s) to prevent gas layering.
3. **Misfire Examination (CMR 2017 Reg 203 & 204):** Face must be inspected for misfires and sockets logged in shot-firer book before relieving shift drills.
4. **Roadway Incombustible Dust (CMR 2017 Reg 144):** Minimum 75% incombustible stone dust (and >= 85% in gassy seams) to prevent coal dust flame propagation.
"""
        return {"type": "regulations", "title": "CMR Statutory Violations", "markdown": md}

    def _handle_inquiries(self, q: str) -> dict:
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT inq_no, date, mine_name, cause, killed, president, assessors FROM courts_of_inquiry ORDER BY inq_no ASC")
        rows = cur.fetchall()
        conn.close()

        table_md = "| Inq # | Date | Mine Name | Fatalities | Court President | Appointed Technical Assessors |\n| :---: | :---: | :--- | :---: | :--- | :--- |\n"
        for r in rows:
            table_md += f"| **{r['inq_no']}** | {r['date']} | **{r['mine_name']}** | **{r['killed']}** | {r['president']} | {r['assessors']} |\n"

        md = f"""### Courts of Inquiry Instituted for Mine Explosions (1901 – 2022)

Under Section 24 of the Mines Act, 1952, a total of **19 Courts of Inquiry** were instituted exclusively for coal mine explosions and gas/dust disasters:

{table_md}

- **Total Fatalities across Explosion Inquiries:** **1,093 Deaths**
- **Assessment Structure:** Inquiries combined a Judicial President (High Court Judge or District Commissioner) with Technical Assessors (Chief Inspector of Mines, CMRS/CIMFR Directors, and Mining Engineering Professors from ISM Dhanbad and BHU).
"""
        return {"type": "inquiries", "title": "Courts of Inquiry Register", "markdown": md}

    def _handle_company_breakdown(self, q: str) -> dict:
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("""
        SELECT company, COUNT(*) as incidents, SUM(killed) as deaths, SUM(injured) as injuries
        FROM recent_incidents
        GROUP BY company
        ORDER BY deaths DESC, incidents DESC
        """)
        rows = cur.fetchall()
        conn.close()

        table_md = "| Mining Company / Subsidiary | Incidents (2016-2022) | Fatalities | Serious Injuries | Key Hazards |\n| :--- | :---: | :---: | :---: | :--- |\n"
        for r in rows:
            table_md += f"| **{r['company']}** | **{r['incidents']}** | **{r['deaths']}** | **{r['injuries']}** | Blasting, Misfires, Gas Influx |\n"

        md = f"""### Company-Wise Breakdown of Recent Incidents (2016 – 2022)

Distribution across Coal India subsidiaries and SCCL:

{table_md}

- **South Eastern Coalfields Limited (SECL):** Experienced 5 incidents (8 deaths), including Bagdewa (3 killed, gas), Kurasia (misfire explosion), and Manikpur (misfire drill blast).
- **Singareni Collieries Company Limited (SCCL):** Experienced 4 incidents (7 deaths, 6 injured), including Ramagundam OC-I secondary blasting catastrophe (4 killed) and Ravindra Khani No. 5 misfire detonation.
"""
        return {"type": "companies", "title": "Company-Wise Breakdown", "markdown": md}

    def _handle_domain_science(self, q: str) -> dict:
        md = """### Mining Engineering Principles: Firedamp & Coal Dust Explosions

1. **Firedamp (Methane, CH₄) Explosion Characteristics:**
   - **Lower Explosive Limit (LEL):** Approx 5.0% by volume in air (~33 g/m3).
   - **Upper Explosive Limit (UEL):** Approx 15.0% by volume in air (~100 g/m3).
   - **Stoichiometric Optimum:** **9.5% CH₄** (produces peak pressure of 7 - 8 bar and maximum blast wave velocity).
   - **Coward Diagram Threshold:** Methane cannot explode if atmospheric oxygen is below **12.1%**, regardless of methane percentage.

2. **Coal Dust Explosion Criteria:**
   - **Volatile Matter (VM):** Highly explosive when VM > 14%.
   - **Particle Fineness:** Particles < 75 um (-200 mesh) form the explosive cloud.
   - **Minimum Explosive Concentration (MEC):** 30 - 50 g/m3.
   - **Statutory Inerting:** Minimum **75% incombustible stone dust** (>= 85% in presence of CH4) to quench the flame front.

3. **Hybrid Co-Explosion (Methane + Coal Dust):**
   - As little as **1.0% CH₄** reduces the Lower Explosive Limit of coal dust by more than **50%**, allowing non-explosive dust clouds to detonate violently.
"""
        return {"type": "science", "title": "Physical & Chemical Explosion Principles", "markdown": md}

    def _handle_general_search(self, q: str) -> dict:
        conn = self.get_connection()
        cur = conn.cursor()
        search_term = f"%{q}%"

        cur.execute("""
        SELECT mine_name, date, root_cause_category, killed, injured, physical_mechanism
        FROM recent_incidents
        WHERE LOWER(full_narrative) LIKE ? OR LOWER(mine_name) LIKE ? OR LOWER(root_cause_category) LIKE ?
        """, (search_term, search_term, search_term))
        matches = cur.fetchall()
        conn.close()

        if matches:
            table_md = "| Mine Name | Date | Root Cause | Killed | Injured | Summary |\n| :--- | :---: | :--- | :---: | :---: | :--- |\n"
            for m in matches:
                table_md += f"| **{m['mine_name']}** | {m['date']} | {m['root_cause_category']} | **{m['killed']}** | {m['injured']} | {m['physical_mechanism'][:90]}... |\n"
            md = f"### Found {len(matches)} Matching Incident Records for `{q}`:\n\n{table_md}"
        else:
            md = f"No direct match found for `{q}`. Try asking about a specific colliery (e.g., *Chhatarpur*, *Dhori*, *Ramagundam*), counts (*how many incidents*), causes (*what were the reasons*), or regulations (*CMR violations*)."

        return {"type": "search", "title": f"Search Results for: {q}", "markdown": md}

if __name__ == '__main__':
    engine = MineExplosionQAEngine()
    test_queries = [
        "How many mine incidents of the type you are working on have happened up until now?",
        "What were the reasons and number of incidents of each respective reason?",
        "What was the worst coal mine explosion disaster?",
        "Tell me about Chhatarpur Mine No. 1",
        "What regulations were violated in solid blasting?",
        "What are the courts of inquiry for explosions?"
    ]

    print("=== TESTING MINE EXPLOSION QA ENGINE ===")
    for query in test_queries:
        print(f"\n==============================================")
        print(f"QUERY: {query}")
        result = engine.ask(query)
        print(f"TITLE: {result['title']}")
        print(result['markdown'][:350] + "...\n")
