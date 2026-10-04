import sys
import fitz
import re
import json

sys.stdout.reconfigure(encoding='utf-8')

pdf_path = 'sanket0404_2024.pdf'
doc = fitz.open(pdf_path)
print(f"Loaded {pdf_path} with {len(doc)} pages.")

# ==========================================
# 1. PARSE SECTION 10: MAJOR ACCIDENTS (1901-2022)
# Pages 299 to 306 (0-indexed: 298 to 305)
# ==========================================
sec10_text = ""
for p in range(298, 306):
    sec10_text += f"\n--- PAGE {p+1} ---\n" + doc[p].get_text()

lines10 = [l.strip() for l in sec10_text.split('\n') if l.strip()]

major_accidents = []
i = 0
while i < len(lines10):
    line = lines10[i]
    if line.isdigit() and i + 5 < len(lines10):
        if re.match(r'^\d{2}-\d{2}-\d{4}$', lines10[i+1]):
            sl = int(lines10[i])
            date = lines10[i+1]
            mine = lines10[i+2]
            killed = lines10[i+3]
            injured = lines10[i+4]
            cause = lines10[i+5]
            if killed.isdigit() and injured.isdigit():
                cause_parts = [cause]
                curr = i + 6
                while curr < len(lines10):
                    next_l = lines10[curr]
                    if next_l.isdigit() and curr + 1 < len(lines10) and re.match(r'^\d{2}-\d{2}-\d{4}$', lines10[curr+1]):
                        break
                    if 'PAGE' in next_l or 'MAJOR ACCIDENT' in next_l or next_l in ['Sl.', 'Date of', 'Accident', 'Name of Mine', 'Number of', 'Persons', 'Cause of Accident', 'Killed', 'S/Injured']:
                        curr += 1
                        continue
                    if next_l.isdigit() and 280 <= int(next_l) <= 315:
                        curr += 1
                        continue
                    cause_parts.append(next_l)
                    curr += 1
                full_cause = ' '.join(cause_parts)
                major_accidents.append({
                    'sl_no': sl,
                    'date': date,
                    'mine_name': mine,
                    'killed': int(killed),
                    'injured': int(injured),
                    'cause': full_cause
                })
                i = curr
                continue
    i += 1

print(f"Parsed {len(major_accidents)} major accidents.")

# Filter explosion, gas, dust, firedamp, explosives
explosion_major = []
for acc in major_accidents:
    c = acc['cause'].lower()
    if any(k in c for k in ['explos', 'gas', 'damp', 'dust', 'ignit', 'suffocat']):
        explosion_major.append(acc)

print(f"Found {len(explosion_major)} explosion/gas/dust/explosive major accidents.")

# ==========================================
# 2. PARSE SECTION 11: COURTS OF INQUIRY (1901-2022)
# Pages 307 to 310 (0-indexed: 306 to 309)
# ==========================================
sec11_text = ""
for p in range(306, 310):
    sec11_text += doc[p].get_text() + "\n"

inquiry_entries = []
# Match pattern: Sl No, Date, Mine & Cause, Killed, Court constitution, Assessors
# Let's inspect rows by regex or splitting
inquiry_raw_lines = sec11_text.split('\n')
current_inq = None
inquiries = []

for line in inquiry_raw_lines:
    line_clean = line.strip()
    if not line_clean or 'Statement 5.15' in line_clean or 'COURT OF INQUIRY' in line_clean or 'Sl.    Date' in line_clean or '------------------' in line_clean:
        continue
    # Check if starts with a number followed by date DD/MM/YY
    m = re.match(r'^(\d+)\s+(\d{2}/\d{2}/\d{2})\s+(.+)$', line_clean)
    if m:
        if current_inq:
            inquiries.append(current_inq)
        current_inq = {
            'sl_no': int(m.group(1)),
            'date': m.group(2),
            'raw_rest': [m.group(3)]
        }
    elif current_inq:
        current_inq['raw_rest'].append(line_clean)

if current_inq:
    inquiries.append(current_inq)

print(f"Parsed {len(inquiries)} Courts of Inquiry.")

# ==========================================
# 3. EXTRACT ALL 0700 & 0500 ACCIDENT DETAILS (2016-2022)
# ==========================================
# We search all pages for accident description blocks under codes 0700 (Dust, Gas) and 0500 (Explosives)
yearly_gas_dust_explosives = []

for p_num in range(len(doc)):
    page_text = doc[p_num].get_text()
    if 'Code : 07' in page_text or 'Code : 05' in page_text:
        yearly_gas_dust_explosives.append({
            'page': p_num + 1,
            'text': page_text
        })

print(f"Found {len(yearly_gas_dust_explosives)} pages with 07xx or 05xx accident blocks.")

# Save intermediate extracted data to json for compilation
data_dump = {
    'total_major_accidents': len(major_accidents),
    'major_accidents_explosion': explosion_major,
    'inquiries_raw': inquiries,
    'yearly_pages_count': len(yearly_gas_dust_explosives)
}

with open('extracted_data.json', 'w', encoding='utf-8') as f:
    json.dump(data_dump, f, indent=2, ensure_ascii=False)

print("Extraction script completed successfully.")
