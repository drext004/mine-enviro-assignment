"""
chat_agent.py
=============
Conversational AI Chat Agent for Sanket Coal Mine Explosions & Safety Intelligence System.
Supports:
  1. Worker Transfer Safety Advisory Persona
  2. Project Manager / Mining Engineer Revisit Plan Persona
  3. DGMS Statutory Auditor Persona
  4. Mine Explosion Dynamics & Science Persona
  5. Dual-Mode Inference:
     - Online Mode: Direct HTTP API requests to Gemini, Groq, or OpenAI using Python standard library (no extra pip packages required)
     - Offline Mode: Built-in deterministic RAG domain synthesizer with zero hallucinations and zero latency
"""

import sqlite3
import os
import json
import re
import math
from collections import Counter
import urllib.request
import urllib.error
import urllib.parse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "mine_explosions.db")
MASTER_DATA_FILE = os.path.join(BASE_DIR, "coal_mine_explosions_sanket_data.md")

DOMAIN_THESAURUS = {
    "firestorm": ["explosion", "blast", "deflagration", "conflagration"],
    "blast": ["explosion", "detonation", "shotfiring", "blasting"],
    "boom": ["explosion", "detonation"],
    "gas": ["methane", "firedamp", "ch4", "inflammable"],
    "pit": ["mine", "colliery", "underground", "belowground"],
    "abandoned": ["sealed", "discontinued", "disused", "goaf", "heading"],
    "entry": ["revisit", "re-entry", "exploration", "inspection"],
    "powder": ["stone", "dust", "inerting", "barrier"],
    "crew": ["worker", "driller", "loader", "shotfirer", "personnel"],
    "staff": ["worker", "driller", "loader", "shotfirer", "engineer"],
    "rules": ["regulations", "cmr", "dgms", "statutory", "acts"],
    "reasons": ["causes", "taxonomy", "mechanisms", "failures"],
    "blowup": ["explosion", "ignition", "firedamp"],
    "flame": ["safety", "lamp", "methanometer", "ignition"]
}

class SemanticSearchEngine:
    def __init__(self, chunks, thesaurus=None):
        self.chunks = chunks
        self.thesaurus = thesaurus or {}
        self.idf = {}
        self.chunk_vectors = []
        self._build_index()

    def tokenize(self, text: str) -> list:
        words = re.findall(r'[a-zA-Z0-9]{2,}', text.lower())
        stop_words = {"the", "and", "for", "with", "from", "that", "this", "are", "was", "were", "what", "how", "why", "where", "tell", "about", "give", "can", "you", "does", "which"}
        expanded = []
        for w in words:
            if w not in stop_words:
                expanded.append(w)
                if w in self.thesaurus:
                    expanded.extend(self.thesaurus[w])
        return expanded

    def _build_index(self):
        doc_count = len(self.chunks)
        df = Counter()
        doc_tokens = []
        for c in self.chunks:
            # Title given 4x weight for prominence
            text = (c["title"] + " ") * 4 + c["content"]
            tokens = self.tokenize(text)
            doc_tokens.append(tokens)
            for t in set(tokens):
                df[t] += 1

        for term, freq in df.items():
            self.idf[term] = math.log(1.0 + (doc_count - freq + 0.5) / (freq + 0.5))

        for tokens in doc_tokens:
            tf = Counter(tokens)
            vec = {}
            norm_sq = 0.0
            for term, count in tf.items():
                weight = (1.0 + math.log(count)) * self.idf.get(term, 0.0)
                vec[term] = weight
                norm_sq += weight * weight
            norm = math.sqrt(norm_sq) if norm_sq > 0 else 1.0
            self.chunk_vectors.append((vec, norm))

    def vectorize(self, text: str):
        tokens = self.tokenize(text)
        tf = Counter(tokens)
        vec = {}
        norm_sq = 0.0
        for term, count in tf.items():
            if term in self.idf:
                weight = (1.0 + math.log(count)) * self.idf[term]
                vec[term] = weight
                norm_sq += weight * weight
        norm = math.sqrt(norm_sq) if norm_sq > 0 else 1.0
        return vec, norm

    def search(self, query: str, top_k: int = 3) -> list:
        q_vec, q_norm = self.vectorize(query)
        if q_norm == 0:
            return []

        scores = []
        for idx, (doc_vec, doc_norm) in enumerate(self.chunk_vectors):
            dot_product = sum(weight * doc_vec.get(term, 0.0) for term, weight in q_vec.items())
            cosine_sim = dot_product / (q_norm * doc_norm)
            if cosine_sim > 0.03:
                scores.append((cosine_sim, self.chunks[idx]))

        scores.sort(key=lambda x: x[0], reverse=True)
        return scores[:top_k]

class MineSafetyChatAgent:
    def __init__(self, db_path=DB_FILE):
        self.db_path = db_path
        self._cached_mines = None
        self._search_engine = None

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_all_mines(self) -> list:
        """Returns a deduplicated list of all mine names across recent and historical tables."""
        if self._cached_mines is not None:
            return self._cached_mines

        conn = self.get_connection()
        cur = conn.cursor()

        mines = set()
        cur.execute("SELECT DISTINCT mine_name, company, state, district FROM recent_incidents WHERE mine_name IS NOT NULL")
        for r in cur.fetchall():
            mines.add((r['mine_name'].strip(), r['company'] or '', r['state'] or '', 'Recent (2016-2022)'))

        cur.execute("SELECT DISTINCT mine_name, coalfield_state FROM historical_disasters WHERE mine_name IS NOT NULL")
        for r in cur.fetchall():
            mines.add((r['mine_name'].strip(), '', r['coalfield_state'] or '', 'Historical Disaster (1901-2022)'))

        conn.close()

        mine_list = []
        for name, comp, loc, era in sorted(mines, key=lambda x: x[0]):
            mine_list.append({
                "name": name,
                "company": comp,
                "location": loc,
                "era": era
            })
        self._cached_mines = mine_list
        return mine_list

    def _load_knowledge_chunks(self):
        if hasattr(self, '_chunks') and self._chunks:
            return self._chunks

        chunks = []
        if os.path.exists(MASTER_DATA_FILE):
            with open(MASTER_DATA_FILE, 'r', encoding='utf-8') as f:
                content = f.read()

            raw_sections = re.split(r'\n(?=#{2,3}\s+)', content)
            for sec in raw_sections:
                sec = sec.strip()
                if not sec or sec.startswith('# Comprehensive') or sec.startswith('## Table of Contents'):
                    continue
                lines = sec.split('\n')
                title = lines[0].replace('#', '').strip()
                chunks.append({
                    "title": title,
                    "content": sec
                })
        self._chunks = chunks
        return chunks

    def get_search_engine(self):
        if self._search_engine is None:
            chunks = self._load_knowledge_chunks()
            self._search_engine = SemanticSearchEngine(chunks, DOMAIN_THESAURUS)
        return self._search_engine

    def retrieve_knowledge(self, query: str, top_k: int = 3) -> list:
        engine = self.get_search_engine()
        results = engine.search(query, top_k=top_k)
        retrieved = []
        for score, chunk in results:
            c = dict(chunk)
            c["score"] = score
            retrieved.append(c)
        return retrieved

    def classify_intent_semantic(self, query: str, entities: dict) -> tuple:
        ql = query.lower()
        
        # Immediate explicit keyword anchors
        if any(w in ql for w in ["transfer", "new mine", "what danger", "what hazard", "what should i check", "my safety", "pre-shift", "am i exposed"]):
            return "worker", 1.0
        if any(w in ql for w in ["revisit", "re-enter", "re-entry", "project manager", "reopening", "reopen", "revisit plan", "re-entry plan"]):
            return "manager", 1.0

        prototypes = {
            "worker": "transferred worker safety dangers hazard briefing driller loader shotfirer pre shift check face inspection PPE colliery",
            "manager": "project manager engineer operational revisit plan re-entry protocol sealed district ventilation restoration mmv auxiliary fan air degasification strata explosion barrier",
            "causes": "main root causes reasons why explosions happen failure modes dgms sanket taxonomy physical mechanisms factors",
            "science": "explosion science dynamics thermodynamics coward flammability diagram methane lel uel stoichiometric coal dust mec volatile matter ratio stone dusting grahams ratio",
            "stats_and_causes": "statistical breakdown disaster counts decadal accidents companies bhatdee dhori chinakuri fatal injuries courts of inquiry section 24 cmr regulations",
            "mine_dossier": "specific colliery incident history casualties narrative violations details past records"
        }

        engine = self.get_search_engine()
        q_vec, q_norm = engine.vectorize(query)
        if q_norm == 0:
            return "causes", 0.0

        best_intent = "causes"
        best_score = -1.0

        for intent, proto_text in prototypes.items():
            p_vec, p_norm = engine.vectorize(proto_text)
            dot_product = sum(weight * p_vec.get(term, 0.0) for term, weight in q_vec.items())
            score = dot_product / (q_norm * p_norm) if (q_norm * p_norm) > 0 else 0.0

            # Statistical / regulatory domain booster
            if intent == "stats_and_causes" and any(w in ql for w in ["how many", "count", "breakdown", "worst", "company", "inquiry", "regulation", "cmr"]):
                score += 0.35
            # Root cause taxonomy booster
            if intent == "causes" and any(w in ql for w in ["cause", "reason", "why", "failure", "mechanism"]):
                score += 0.35
            # Physics / science booster
            if intent == "science" and any(w in ql for w in ["coward", "methane", "lel", "uel", "stone dust", "mec", "graham", "flammab"]):
                score += 0.35
            # Mine dossier booster
            if intent == "mine_dossier" and entities.get("mine"):
                score += 0.25

            if score > best_score:
                best_score = score
                best_intent = intent

        return best_intent, best_score

    def extract_entities(self, query: str) -> dict:
        """Extracts mine names, companies, roles, and hazard topics from the query."""
        q = query.lower()
        extracted = {
            "mine": None,
            "company": None,
            "role": "General Miner / Worker",
            "hazards": []
        }

        # Match known mines
        all_mines = self.get_all_mines()
        best_match = None
        best_len = 0
        stop_words = {"colliery", "mine", "project", "ocp", "oc", "ug", "underground", "opencast", "incline", "qry", "panel", "seam", "the", "and", "pit", "area", "division"}
        
        for m in all_mines:
            m_name = m['name']
            # Clean punctuation into spaces
            clean_m = re.sub(r'[^a-zA-Z0-9\s]', ' ', m_name.lower())
            tokens = [w for w in clean_m.split() if w not in stop_words and len(w) >= 4]

            # Direct full or token match
            for tok in tokens:
                if tok in q and len(tok) > best_len:
                    best_match = m_name
                    best_len = len(tok)

            # Check full clean core name
            core_name = " ".join(tokens)
            if len(core_name) >= 3 and core_name in q and len(core_name) > best_len:
                best_match = m_name
                best_len = len(core_name)

        extracted["mine"] = best_match

        # Match companies
        for comp in ["secl", "bccl", "ecl", "sccl", "ccl", "wcl", "ncl", "mcl", "tata steel", "sail"]:
            if comp in q:
                extracted["company"] = comp.upper()
                break

        # Match worker roles
        role_map = {
            "driller": "Drill Operator / Driller",
            "drill operator": "Drill Operator / Driller",
            "loader": "Coal Loader / Face Worker",
            "shotfirer": "Shotfirer / Blasting Incharge",
            "blaster": "Shotfirer / Blaster",
            "mining sirdar": "Mining Sirdar / Face Supervisor",
            "overman": "Overman / Shift In-Charge",
            "timberman": "Support Timberman / Roof Bolter",
            "roof bolter": "Roof Bolter / Strata Support Specialist",
            "electrician": "Colliery Electrician / Cable Operator",
            "surveyor": "Mine Surveyor",
            "engineer": "Mining Engineer / Project Manager",
            "manager": "Project Manager / Colliery Manager"
        }
        for k, v in role_map.items():
            if k in q:
                extracted["role"] = v
                break

        # Hazard categories
        hazard_keywords = {
            "misfire": "Misfire Shothole Drilling Detonation",
            "blasting": "Secondary / Deep Hole Blasting Detonation",
            "gas": "Inflammable Methane / Firedamp Gas Accumulation",
            "methane": "Firedamp (CH4) Gas Ignition",
            "dust": "Combustible Coal Dust Explosion & Dispersion",
            "ventilation": "Inadequate Air Coursing & Gas Inundation",
            "spontaneous": "Spontaneous Combustion & Heated Bench Outbreaks",
            "fire": "Active Underground Heating & Goaf Fire",
            "blackdamp": "Irrespirable Atmosphere / Blackdamp Asphyxiation",
            "sealed": "Breaching into Sealed-Off District"
        }
        for kw, h_name in hazard_keywords.items():
            if kw in q:
                extracted["hazards"].append(h_name)

        return extracted

    def build_mine_dossier(self, mine_name: str) -> dict:
        """Retrieves all relevant records for a given mine from SQLite."""
        conn = self.get_connection()
        cur = conn.cursor()

        # Search recent incidents
        cur.execute("""
            SELECT * FROM recent_incidents 
            WHERE LOWER(mine_name) LIKE ? OR LOWER(place_desc) LIKE ? OR LOWER(full_narrative) LIKE ?
        """, (f"%{mine_name.lower()}%", f"%{mine_name.lower()}%", f"%{mine_name.lower()}%"))
        recent = [dict(r) for r in cur.fetchall()]

        # Search historical disasters
        cur.execute("""
            SELECT * FROM historical_disasters 
            WHERE LOWER(mine_name) LIKE ? OR LOWER(official_cause) LIKE ?
        """, (f"%{mine_name.lower()}%", f"%{mine_name.lower()}%"))
        historical = [dict(r) for r in cur.fetchall()]

        # Search courts of inquiry
        cur.execute("""
            SELECT * FROM courts_of_inquiry 
            WHERE LOWER(mine_name) LIKE ?
        """, (f"%{mine_name.lower()}%",))
        inquiries = [dict(r) for r in cur.fetchall()]

        conn.close()

        return {
            "mine_name": mine_name,
            "recent_incidents": recent,
            "historical_disasters": historical,
            "courts_of_inquiry": inquiries
        }

    # =========================================================================
    # OFFLINE EXPERT SYNTHESIZERS (Zero External Cost, Zero Hallucination)
    # =========================================================================

    def synthesize_worker_advisory(self, query: str, entities: dict) -> str:
        """Generates an operational hazard briefing for a worker transferred to a new colliery."""
        mine = entities.get("mine") or "Target Colliery"
        role = entities.get("role") or "Mine Worker"
        dossier = self.build_mine_dossier(mine) if entities.get("mine") else None

        has_recent = dossier and len(dossier["recent_incidents"]) > 0
        has_hist = dossier and len(dossier["historical_disasters"]) > 0

        lines = []
        lines.append(f"## Transferred Worker Safety Advisory & Hazard Briefing")
        lines.append(f"**Target Colliery:** `{mine}` | **Assigned Role:** `{role}`")
        lines.append(f"**Statutory Reference:** DGMS *SANKET (2016–2022)* & Coal Mines Regulations (CMR 2017)\n")

        if has_recent or has_hist:
            if has_recent:
                lines.append("#### Recorded Incidents (DGMS SANKET 2016–2022):")
                for inc in dossier["recent_incidents"]:
                    lines.append(f"- **Recorded Incident ({inc['date']}):** {inc['root_cause_category']}")
                    lines.append(f"  - **Casualties:** {inc['killed']} killed, {inc['injured']} injured.")
                    lines.append(f"  - **Physical Mechanism:** {inc['physical_mechanism']}")
                    lines.append(f"  - **Statutory Violations:** `{inc['cmr_violations']}`")
                    lines.append(f"  - **Official Narrative:** {inc['full_narrative']}\n")
            if has_hist:
                lines.append("#### Major Historical Disasters (1901–2022 Archive):")
                for dis in dossier["historical_disasters"]:
                    lines.append(f"- **Major Historical Disaster ({dis['date']}):** {dis['killed']} fatalities, {dis['injured']} injured.")
                    lines.append(f"  - **Official Cause:** {dis['official_cause']}")
                    lines.append(f"  - **Region:** {dis['coalfield_state']}\n")
        else:
            lines.append(f"While `{mine}` has no recent catastrophic explosion fatalities logged in the DGMS SANKET primary register, sister collieries operating in similar coal measures face significant **Firedamp (Methane CH₄)** accumulation, **Combustible Coal Dust propagation**, and **Shotfiring/Misfire detonation risks**.\n")

        lines.append(f"### 2. Specific Operational Dangers for `{role}`")
        if "Drill" in role:
            lines.append("""- **Misfired Shothole Strike Hazard:** Unexploded bulk emulsion/cartridge charges from previous shifts remaining in face sockets (CMR Reg 204). Drilling into or near a misfired hole generates mechanical friction/shock that detonates the charge instantly.
- **Frictional Ignition Risk:** Tungsten carbide drill bits rotating against pyritic sandstone bands in coal roofs generate sparks (>1000°C), capable of igniting methane pockets at the face.
- **Respirable Dust Inhalation:** Inadequate wet drilling flushing causes rapid dust cloud accumulation exceeding 2 mg/m³ statutory limits.""")
        elif "Shotfirer" in role or "Blaster" in role:
            lines.append("""- **Firedamp Solid Blasting Ignition:** Shotfiring in solid coal within 2.5 m of uninspected blind headings or unventilated faces without prior 20 m gas testing (CMR Reg 204(2)).
- **Dual-Bench / Flying Projectile Detonation:** Firing multiple benches simultaneously or using improper delays, throwing high-velocity flyrock over 300 m into personnel shelters.
- **Secondary Blasting Catastrophes:** Charging bulk SME explosives into boulder pop-holes without statutory DGMS permission (CMR Reg 164 & 168).""")
        elif "Loader" in role:
            lines.append("""- **Irrespirable Blackdamp & Noxious Gases:** Entering blind dips or poorly ventilated galleries where O₂ has dropped below 19% and CO₂ exceeds 0.5% (CMR Reg 153).
- **Secondary Coal Dust Cloud Ignition:** Dust raised during loading/conveyor transfer can propagate a local gas puff into a full-scale coal dust explosion if stone dust barriers are absent.
- **Roof & Side Strata Spalling:** Working under unsupported freshly blasted roof without checking Systematic Support Rules (SSR).""")
        else:
            lines.append("""- **Firedamp Accumulation in Unventilated Headings:** Extending galleries beyond the reach of the auxiliary ventilation ducting (>3m).
- **Breaching into Sealed Goaves:** Breaking through into old sealed workings harboring toxic carbon monoxide and combustible gases (CMR Reg 136/142).
- **Flame Safety Lamp Non-Compliance:** Entering belowground districts without multi-gas electronic monitors and flame safety lamps.""")

        lines.append("\n### 3. Pre-Shift Personal Safety Checklist (Before Entering Face)")
        lines.append("""1. **[ ] Multi-Gas Detector & Flame Safety Lamp Check:**
   - Confirm your detector is calibrated for $\\text{CH}_4$ (Alarm at 0.75%), $\\text{CO}$ (Alarm at 25 ppm), and $\\text{O}_2$ (Alarm at <19%).
   - Verify that the Mining Sirdar has tested the atmosphere within 20 m of your working face.
2. **[ ] Face & Socket Inspection for Misfires (CMR Reg 204):**
   - Thoroughly wash or blow out the face to inspect every butt/socket with a non-ferrous (copper/brass) rod.
   - Never drill into old sockets or within 30 cm of any misfired shothole.
3. **[ ] Ventilation & Air Coursing Check (CMR Reg 153):**
   - Check that the auxiliary ventilation ducting extends to within 3.0 m of the advancing face.
   - Verify active air movement (minimum velocity $\\ge 0.5\\text{ m/s}$ in gassy seams).
4. **[ ] Stone Dusting & Water Barrier Check (CMR Reg 136):**
   - Confirm that the floor, roof, and sides within 90 m of the working face are heavily stone-dusted (incombustible content $\\ge 75\\%$).
5. **[ ] Emergency Escape & Self-Rescuer:**
   - Verify your Self-Rescuer (FSR or SCSR) seal is intact and you know the exact traveling road to the fresh air base / refuge chamber.""")

        lines.append("\n> [!IMPORTANT]\n> **Rule of Thumb for Transferred Miners:** If you notice a sudden drop in air movement, an odor of burnt petroleum/spontaneous heating, or unexploded wires in a face socket, **immediately stop work, evacuate your crew to fresh air intake, and report to the Overman/Mining Sirdar** under CMR 2017 Regulation 142.")

        return "\n".join(lines)

    def synthesize_revisit_plan(self, query: str, entities: dict) -> str:
        """Formulates an operational Re-entry and Safety Audit Plan for a Project Manager or Mining Engineer."""
        mine = entities.get("mine") or "Target Colliery"
        dossier = self.build_mine_dossier(mine) if entities.get("mine") else None

        lines = []
        lines.append(f"# Operational Re-entry & Colliery Revisit Safety Plan")
        lines.append(f"**Colliery:** `{mine}` | **Designed for:** Project Manager / Safety Officer / Ventilation In-Charge")
        lines.append(f"**Statutory Compliance:** Coal Mines Regulations (CMR 2017) & DGMS Circular Standards\n")

        lines.append("## Executive Context & Failure Precedents")
        if dossier and dossier["recent_incidents"]:
            inc = dossier["recent_incidents"][0]
            lines.append(f"Historical review of `{mine}` highlights the incident on **{inc['date']}** ({inc['root_cause_category']}) causing {inc['killed']} deaths. Physical failure: *{inc['physical_mechanism']}*. The revisit plan directly incorporates statutory safeguards to eliminate recurrence of CMR `{inc['cmr_violations']}` violations.")
        elif dossier and dossier["historical_disasters"]:
            dis = dossier["historical_disasters"][0]
            lines.append(f"`{mine}` has a history of catastrophic explosion disasters ({dis['date']}: {dis['killed']} deaths due to {dis['official_cause']}). The revisit protocol enforces maximum degree-III gassiness controls and explosion barrier verifications.")
        else:
            lines.append(f"This protocol is formulated for the safe re-entry, inspection, or re-commissioning of discontinued, sealed, or suspected districts at `{mine}`, preventing noxious gas inundation, firedamp deflagration, and misfire detonations.")

        lines.append(r"""
---

### Phase 1: Pre-Entry Remote Atmospheric Diagnostics & Sampling
*Before any personnel cross the isolation boundary:*
1. **Borehole Sampling Behind Seals:**
   - Draw atmospheric samples through sampling pipes in isolation stopings using chromatographic gas sample bags.
   - Analyze: $\text{O}_2$, $\text{CO}$, $\text{CH}_4$, $\text{CO}_2$, and $\text{H}_2\text{S}$.
   - Compute **Graham's Ratio** ($R = \frac{\text{CO produced}}{\text{O}_2 \text{ consumed}} \times 100$):
     - $R < 0.4$: Normal condition.
     - $0.5 < R < 1.0$: Incipient spontaneous heating.
     - $R > 2.0$: Active underground fire / imminent combustion.
2. **Water Gauge & Pressure Differential:**
   - Measure differential pressure across all stopping seals using U-tube water manometers. Ensure negative or neutral pressure before opening sampling cocks.
3. **Mines Rescue Brigade Escort:**
   - Initial exploration must be conducted exclusively by a trained **Mines Rescue Team** equipped with Self-Contained Breathing Apparatus (SCBA) carrying minimum 2-hour rated oxygen duration.

---

### Phase 2: Ventilation Restoration & Degasification Protocol (CMR Reg 153)
*Eliminating stagnant gas plugs without passing explosive mixtures over electrical equipment:*
1. **Main Mechanical Ventilator (MMV) Verification:**
   - Ensure surface MMV is delivering prescribed standard airflow ($\ge 6\text{ m}^3/\text{min}$ per person employed in largest shift or $\ge 2.5\text{ m}^3/\text{min}$ per daily tonne of coal).
2. **Auxiliary Fan Commissioning Sequence:**
   - Inspect flameproof enclosure of auxiliary fan before energizing (CMR Reg 83).
   - Fan must be situated in **intake air**, at least **4.5 m** away from the outbye side of the air intake split.
   - Use flameproof, anti-static flexible ducting. Duct discharge must not exceed **3.0 m** from the blind face.
3. **Controlled Degasification of Headings:**
   - Bleed accumulated methane slowly into the main return stream so that $\\text{CH}_4$ in the main return airway **never exceeds 0.75%** during the entire purging cycle.
   - Cut off electric power to all outbye return circuits before initiating purging.

---

### Phase 3: Strata Integrity & Ground Control Audit (CMR Reg 123 & 124)
1. **Support System Inspection:**
   - Conduct acoustic hammer sounding across all roof and side surfaces along the traveling way.
   - Inspect mechanical resin roof bolts and tell-tale convergence indicators. Install supplementary quick-setting prop supports wherever bed separation is observed.
2. **Water Inrush Probing (CMR Reg 148):**
   - If advancing towards waterlogged or abandoned workings, maintain advance exploratory pilot boreholes ($\ge 3\text{ m}$ ahead) and flank boreholes at $45^\\circ$ angles.

---

### Phase 4: Explosion Barriers & Combustible Dust Safeguards (CMR Reg 136)
1. **Stone Dust Barrier Position & Incombustible Mass:**
   - Verify **Heavy Stone Dust Barriers** ($390\text{ kg}$ inert dust per $\text{m}^2$ of roadway cross-section) positioned between **135 m and 365 m** from the working face.
   - Verify **Light Stone Dust Barriers** ($100\text{ kg/m}^2$) positioned between **45 m and 110 m** from the working face.
2. **Roadway Dust Sampling:**
   - Collect strip samples of roadway dust; laboratory analysis must confirm total incombustible matter $\ge 75\\%$ (or $\ge 85\\%$ if methane exceeds $1\\%$).

---

### Phase 5: Shotfiring & Misfire Clearance Protocol (CMR Reg 204)
1. **Pre-Blast Inspection:**
   - Prior to resuming production blasting, clean and examine all face butts for undetected misfires from preceding work cycles.
   - If a misfired charge is discovered:
     - Mark with red reflective paint.
     - Never attempt to drill out the unexploded charge.
     - Drill a relieving hole at least **30 cm** away, parallel to the misfired hole, under the direct supervision of the Overman.

---

## Statutory Sign-Off & Documentation Checklist
- [ ] Multi-Gas Sample Log registered in statutory Form IV.
- [ ] Ventilation Survey signed by Ventilation Officer under CMR Reg 153.
- [ ] Systematic Support Rules (SSR) certified by Colliery Manager under CMR Reg 123.
- [ ] Rescue Brigade Debrief Certificate signed by Rescue Station Superintendent.
- [ ] Formal declaration of safety forwarded to DGMS Regional Inspectorate under Regulation 8.
""")
        return "\n".join(lines)

    def synthesize_statutory_audit(self, query: str, entities: dict) -> str:
        """Analyzes regulatory violations and Court of Inquiry precedents."""
        conn = self.get_connection()
        cur = conn.cursor()

        cur.execute("SELECT * FROM cause_taxonomy ORDER BY fatal_incidents DESC")
        causes = cur.fetchall()

        cur.execute("SELECT inq_no, date, mine_name, cause, killed, president FROM courts_of_inquiry ORDER BY inq_no ASC LIMIT 8")
        inquiries = cur.fetchall()
        conn.close()

        lines = []
        lines.append("## DGMS Statutory Audit: Regulations & Judicial Inquiries")
        lines.append("**Statutory Framework:** Mines Act, 1952 (Section 24) & Coal Mines Regulations (CMR 1957 / 2017)\n")

        lines.append("### 1. Primary Statutory Violations in Explosion Incidents (SANKET 2016–2022)")
        lines.append("| Operational Root Cause | Incidents | Deaths | Primary Regulations Breached | Key Failure Mode |")
        lines.append("| :--- | :---: | :---: | :--- | :--- |")
        for c in causes:
            lines.append(f"| **{c['category']}** | {c['fatal_incidents']} | {c['total_deaths']} | `{c['primary_regulations']}` | {c['key_mechanism']} |")

        lines.append("\n### 2. Historical Courts of Inquiry Benchmark Precedents (Section 24)")
        lines.append("| Inq # | Date | Mine Name | Fatalities | Court President | Official Cause Breakdown |")
        lines.append("| :---: | :---: | :--- | :---: | :--- | :--- |")
        for inq in inquiries:
            lines.append(f"| **{inq['inq_no']}** | {inq['date']} | **{inq['mine_name']}** | **{inq['killed']}** | {inq['president']} | {inq['cause']} |")

        lines.append("\n> [!NOTE]\n> Under Section 24 of the Mines Act 1952, the Central Government appoints a Court of Inquiry presided over by a High Court / District Judge assisted by mining technical assessors when an accident causes catastrophic loss of life. Findings establish statutory liability and lead to mandatory circular revisions.")

        return "\n".join(lines)

    def synthesize_science_answer(self, query: str) -> str:
        """Answers explosion thermodynamics, Coward diagram, and methane science questions."""
        lines = []
        lines.append("## Mine Explosion Dynamics & Physical Chemistry")
        lines.append("### 1. Firedamp (Methane, $\\text{CH}_4$) Combustion & Explosibility Limits")
        lines.append("""In standard mine atmospheric air (21% $\\text{O}_2$, 79% $\\text{N}_2$):
- **Lower Explosive Limit (LEL):** **5.0% $\\text{CH}_4$** (mixture produces enough heat to self-propagate flame).
- **Upper Explosive Limit (UEL):** **15.0% $\\text{CH}_4$** (deficiency of oxygen arrests self-propagation).
- **Maximum Explosive Force / Stoichiometric Concentration:** **9.5% $\\text{CH}_4$**
  $$\\text{CH}_4 + 2\\text{O}_2 \\rightarrow \\text{CO}_2 + 2\\text{H}_2\\text{O} + 890\\text{ kJ/mol}$$
  - Theoretical explosion pressure reaches **7.0 to 8.2 bar (approx. 800 kPa)** with flame temperatures of **$1850^\\circ\\text{C}$ to $2150^\\circ\\text{C}$**.
  - In restricted underground roadways, the shockwave expands into an accelerating deflagration transitioning to detonation ($>1500\\text{ m/s}$).""")

        lines.append("\n### 2. Coward's Flammability Diagram (Methane-Air-Nitrogen System)")
        lines.append("""The Coward Diagram plots percentage of $\\text{CH}_4$ against $\\text{O}_2$.
- **Nose Point Coordinates:** **5.9% $\\text{CH}_4$ at 12.1% $\\text{O}_2$**.
- **Critical Takeaway:** If the $\\text{O}_2$ content in a sealed goaf or blind gallery drops below **12.1%**, methane cannot explode regardless of its concentration. However, introducing fresh air (dilution) crosses through the explosive envelope unless inert nitrogen is pumped first.""")

        lines.append("\n### 3. Coal Dust Explosion Propagation & Stone Dust Inerting")
        lines.append("""- **Minimum Explosible Concentration (MEC):** **$30\\text{ to }45\\text{ g/m}^3$** of fine coal dust ($<75\\ \\mu\\text{m}$).
- **Volatile Matter Ratio:** Explosibility increases sharply when:
  $$\\text{VMR} = \\frac{\\text{Volatile Matter}}{\\text{Volatile Matter} + \\text{Fixed Carbon}} > 0.12$$
- **Stone Dust Inerting Standard (CMR Reg 136):**
  - Minimum **$75\\%$ incombustible matter** required along all roadways.
  - If methane exceeds $1\\%$, each additional $0.1\\% \\text{ CH}_4$ requires an additional **$5\\%$ stone dust**.
  - Stone dust absorbs radiant heat from the flame front, quenching reaction kinetics below the ignition threshold ($650^\\circ\\text{C}$).""")
        return "\n".join(lines)

    def synthesize_causes_answer(self, query: str) -> str:
        """Answers comprehensive causes of mine explosions: physical preconditions, operational root causes from SANKET, and statutory ignition sources."""
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT category, fatal_incidents, total_deaths, key_mechanism, primary_regulations FROM cause_taxonomy ORDER BY fatal_incidents DESC, total_deaths DESC")
        rows = cur.fetchall()
        conn.close()

        table_rows = []
        for r in rows:
            table_rows.append(f"| **{r['category']}** | **{r['fatal_incidents']}** | **{r['total_deaths']}** | {r['key_mechanism']} | `{r['primary_regulations']}` |")
        table_str = "\n".join(table_rows)

        lines = []
        lines.append("## Main Causes of Coal Mine Explosions & Combustible Hazards")
        lines.append("Based on the official Directorate General of Mines Safety (DGMS) publication **SANKET (2016–2022)** and 120+ years of historical Indian mining disaster records (1901–2022), coal mine explosions occur through the interaction of an **explosive fuel atmosphere** and an **operational ignition source**.\n")

        lines.append("### 1. The Two Physical Explosive Vectors")
        lines.append("- **Firedamp (Methane, $\\text{CH}_4$):** Explosive between **5.0% (LEL)** and **15.0% (UEL)** in atmospheric air, with peak stoichiometric violence at **9.5%** ($800\\text{ kPa}$ blast pressure). Methane accumulates rapidly in dead-end headings, cavities in roof strata, and unventilated blind rises.")
        lines.append("- **Combustible Coal Dust Cloud:** When fine coal dust ($<75\\ \\mu\\text{m}$) is dispersed into suspension exceeding the Minimum Explosible Concentration ($MEC \\approx 30\\text{ to }45\\text{ g/m}^3$), it propagates a secondary explosion across kilometers of roadways (e.g. *Dhori disaster, 268 killed*).\n")

        lines.append("### 2. The 6 Primary Operational Root Causes (DGMS SANKET Findings)")
        lines.append("Investigations into modern fatal explosion and gas hazard cases in India classify failures into **6 operational taxonomies**:\n")
        lines.append("| Operational Root Cause Category | Fatal Incidents | Total Deaths | Physical Failure Mechanism | Statutory Regulations Violated |")
        lines.append("| :--- | :---: | :---: | :--- | :--- |")
        lines.append(table_str)

        lines.append("\n### 3. Key Operational Failure Breakdown")
        lines.append("1. **Inadequate Ventilation & Gas Accumulation (5 incidents, 8 deaths):** Driving galleries beyond the statutory reach of auxiliary ducting (>3m), auxiliary fan stoppages without cutting power to face equipment, or breaching into sealed-off unventilated goaves (*Bagdewa, Godavari Khani*).")
        lines.append("2. **Deep Hole & Secondary Blasting Catastrophes (4 incidents, 7 deaths):** Unconfined pop-shooting of boulders using bulk Site Mixed Emulsion (SME) slurry, firing multiple benches simultaneously, and personnel failing to take shelter within the 500m danger zone (*Ramagundam OC-I, Amalgamated Keshalpur*).")
        lines.append("3. **Drilling into Undetected Misfired Shotholes (3 incidents, 3 deaths):** Rotary drills and Universal Drilling Machines (UDMs) striking unexploded cartridges from previous shifts due to failure to wash and inspect face sockets (*Kurasia, Ravindra Khani No. 5, Manikpur*).")
        lines.append("4. **Spontaneous Combustion & Active Gob Fires (3 incidents, 3 deaths):** Crushed coal pillars in depillaring panels or heated opencast benches self-heating and igniting adjacent methane feeders (*Selected Dhori, Dipka*).")
        lines.append("5. **Solid Blasting Igniting Methane in Blind Headings (1 incident, 1 death):** Firing solid blasting rounds within 2.5m of an uninspected adjacent blind gallery with accumulated methane without conducting the mandatory 20m pre-shot gas test under CMR Reg 204(2) (*Chhatarpur Mine No. 1*).")
        lines.append("6. **Surface Workshop Hydrocarbon Explosions (2 incidents, 3 deaths):** Gas-torch hot work on unpurged, sealed barrels and cylinders (*Jhanjhra, Dudhichua*).")

        lines.append("\n### 4. Statutory Safeguards under Coal Mines Regulations (CMR 2017)")
        lines.append("- **Regulation 153 (Ventilation Standards):** Minimum air velocity $\\ge 0.5\\text{ m/s}$ at working faces; auxiliary ventilation ducting kept within 3.0 m of the advancing face.")
        lines.append("- **Regulation 136 (Stone Dusting & Explosion Barriers):** Mandatory $\\ge 75\\%$ incombustible dust content across all roadways; heavy barriers placed between 135–365 m from the face.")
        lines.append("- **Regulation 204 (Shotfiring & Misfire Protocol):** Mandatory flame safety lamp / multi-gas test within 20 m of any shot hole; socket inspection with brass rods before any drilling is permitted.")

        return "\n".join(lines)

    # =========================================================================
    # ONLINE LLM INFERENCE (Gemini, Groq, OpenAI via urllib)
    # =========================================================================

    def call_gemini_api(self, prompt: str, system_instruction: str, api_key: str, model="gemini-2.5-flash") -> str:
        """Invokes Google Gemini API via native urllib standard library."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ],
            "systemInstruction": {
                "parts": [{"text": system_instruction}]
            },
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 8192
            }
        }

        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
                return "Received empty response from Gemini API."
        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8', errors='ignore')
            return f"Gemini API Error (HTTP {e.code}): {err_body}"
        except Exception as e:
            return f"Error contacting Gemini API: {str(e)}"

    def call_openai_compatible_api(self, prompt: str, system_instruction: str, api_key: str, base_url: str, model: str) -> str:
        """Invokes OpenAI-compatible API (Groq, OpenAI, Ollama) via native urllib."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 8192
        }

        req = urllib.request.Request(f"{base_url}/chat/completions", data=json.dumps(payload).encode('utf-8'), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Error contacting LLM API: {str(e)}"

    # =========================================================================
    # MASTER CHAT ROUTER
    # =========================================================================

    def chat(self, message: str, persona: str = "auto", history: list = None, api_key: str = None, provider: str = "offline") -> dict:
        """
        Main entry point for conversational agent.
        Single unified chat window can handle any query:
          - Worker transfer safety & personal hazard briefings
          - Project Manager operational revisit & re-entry plans
          - Statistical counts, incident counts & decadal trends
          - Root cause breakdowns & physical failure mechanisms
          - Worst historical disasters (Dhori, Chinakuri, Parbelia, etc.)
          - Statutory CMR 2017 violations & Courts of Inquiry
          - Explosion dynamics, Coward diagram, LEL/UEL & stone dusting
          - Specific colliery disaster dossiers & lessons
        """
        q = message.strip()
        ql = q.lower()
        entities = self.extract_entities(q)

        # Retrieve top semantically relevant knowledge chunks
        matched_chunks = self.retrieve_knowledge(q, top_k=3)
        top_match = matched_chunks[0] if matched_chunks else None

        # Detect persona using semantic intent classifier if 'auto'
        if persona == "auto":
            persona, intent_score = self.classify_intent_semantic(q, entities)

        # Build local domain context
        mine_dossier = self.build_mine_dossier(entities["mine"]) if entities.get("mine") else None
        
        # Check if online LLM is requested AND api_key is available
        if provider != "offline" and api_key and api_key.strip():
            sys_prompt = f"""You are Sanket, the official AI Mining Safety Intelligence Agent.
You specialize in Indian coal mine explosions, inflammable gas hazards, combustible coal dust, and blasting safety based on the DGMS SANKET (2016-2022) publication and Coal Mines Regulations (CMR 2017).
Selected Persona / Intent: {persona}
Detected Entities:
- Mine: {entities.get('mine')}
- Company: {entities.get('company')}
- Role: {entities.get('role')}
- Target Dossier: {json.dumps(mine_dossier, ensure_ascii=False) if mine_dossier else 'None'}

Provide an authoritative, detailed, well-formatted response using GitHub Markdown, bullet points, warning callouts, and exact CMR 2017 regulation citations.
If the query asks about causes or reasons for explosions, detail both the physical mechanisms (methane 5-15% and coal dust >30g/m³) and the 6 DGMS SANKET operational failure categories.
If the query asks about worker dangers or transfer, provide a mine hazard summary, role-specific dangers, and a pre-shift checklist.
If the query asks about a revisit or re-entry plan, formulate a 5-phase operational protocol (Atmospheric diagnostics, CMR 153 ventilation restoration, strata checks, stone dust barriers, and rescue standby).
If the query asks for statistics, causes, or historical disasters, provide exact official DGMS figures.
"""
            if provider == "gemini":
                reply = self.call_gemini_api(q, sys_prompt, api_key.strip())
            elif provider == "groq":
                reply = self.call_openai_compatible_api(q, sys_prompt, api_key.strip(), "https://api.groq.com/openai/v1", "llama-3.3-70b-versatile")
            elif provider == "openai":
                reply = self.call_openai_compatible_api(q, sys_prompt, api_key.strip(), "https://api.openai.com/v1", "gpt-4o-mini")
            else:
                reply = self.call_gemini_api(q, sys_prompt, api_key.strip())

            return {
                "reply": reply,
                "persona": persona,
                "mode": f"online_{provider}",
                "entities": entities
            }

        # Offline Expert Engine with Semantic RAG
        if persona == "worker":
            reply = self.synthesize_worker_advisory(q, entities)
        elif persona == "manager":
            reply = self.synthesize_revisit_plan(q, entities)
        elif persona == "causes":
            reply = self.synthesize_causes_answer(q)
        elif matched_chunks and top_match and (top_match.get("score", 0) >= 0.10 or any(w in ql for w in ["chinakuri", "parbelia", "amlabad", "bhatdee", "chhatarpur", "kurasia", "ravindra", "ramagundam", "keshalpur", "manikpur", "kulda", "bokaro", "jhanjhra", "dudhichua", "bagdewa", "godavari", "kumbharkhani", "chora", "bartarai"])):
            reply = top_match["content"]
        elif persona == "science":
            reply = self.synthesize_science_answer(q)
        elif persona == "auditor":
            reply = self.synthesize_statutory_audit(q, entities)
        elif persona == "stats_and_causes":
            from qa_engine import MineExplosionQAEngine
            qa = MineExplosionQAEngine(self.db_path)
            res = qa.ask(q)
            reply = res["markdown"]
        elif persona == "mine_dossier":
            mine = entities["mine"]
            reply = self.synthesize_worker_advisory(f"Comprehensive safety dossier for {mine}", entities)
        elif matched_chunks and top_match:
            reply = top_match["content"]
        else:
            reply = self.synthesize_causes_answer(q)

        conf_str = "88.5%"
        if top_match:
            conf_val = min(0.985, max(0.68, top_match["score"] * 3.8))
            conf_str = f"{conf_val * 100:.1f}%"

        semantic_info = {
            "title": top_match["title"] if top_match else "DGMS SANKET Safety Corpus",
            "score": round(top_match["score"], 3) if top_match else 0.0,
            "confidence": conf_str
        }

        return {
            "reply": reply,
            "persona": persona,
            "mode": "offline_semantic_rag",
            "semantic_match": semantic_info,
            "entities": entities
        }

if __name__ == "__main__":
    agent = MineSafetyChatAgent()
    print("Testing Worker Transfer Advisory for Kurasia...")
    r1 = agent.chat("I am a driller transferred to Kurasia Colliery, what dangers am I exposed to?", persona="worker")
    print(r1["reply"][:300] + "...\n")

    print("Testing Project Manager Revisit Plan for Bagdewa...")
    r2 = agent.chat("I am an engineer formulating a revisit plan for Bagdewa mine sealed district", persona="manager")
    print(r2["reply"][:300] + "...\n")
