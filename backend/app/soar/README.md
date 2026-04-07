# SOAR Platform
## Security Orchestration, Automation and Response

BTech CSE Capstone Project 2026

---

## Overview
A complete SOAR platform that automatically detects, analyzes
and responds to cybersecurity incidents. Built following
NIST SP 800-61 incident response lifecycle and MITRE ATT&CK
framework for risk scoring.

---

## Features
- Auto detection of 4 attack types
- MITRE ATT&CK based risk scoring
- 4 threat intel integrations
- Automated response actions
- PDF incident report generation
- Real dataset + live simulation support

---

## Attack Types Supported
1. Brute Force (MITRE T1110)
2. Phishing (MITRE T1566)
3. Malware Detection (MITRE T1204/T1027)
4. Network Anomaly (MITRE T1071/T1030)

---

## Framework
- NIST SP 800-61 - Incident Response Lifecycle
- MITRE ATT&CK - Risk Scoring Framework

---

## Tech Stack
- Python 3
- pandas, requests, python-dotenv, fpdf2, colorama, OTXv2

---

## Threat Intelligence Tools
- VirusTotal - File/URL/Hash scanning
- AbuseIPDB - IP reputation
- AlienVault OTX - IOC enrichment
- MalwareBazaar - Malware hash lookup

---

## Project Structure
soar_platform/
├── main.py                         # Main orchestrator
├── config/
│   ├── settings.py                 # Global settings
│   └── risk_config.py              # Risk scoring config
├── option1_datasets/               # Real security datasets
│   ├── brute_force/
│   ├── phishing/
│   ├── malware/
│   └── network_anomaly/
├── option2_simulation/             # Attack simulators
│   ├── simulate_bruteforce.py
│   ├── simulate_phishing.py
│   ├── simulate_malware.py
│   └── simulate_network_anomaly.py
├── playbooks/                      # Core SOAR playbooks
│   ├── base_playbook.py
│   ├── brute_force_playbook.py
│   ├── phishing_playbook.py
│   ├── malware_playbook.py
│   └── network_anomaly_playbook.py
├── utils/                          # Helper modules
│   ├── log_parser.py
│   ├── threat_intel.py
│   └── reporter.py
├── reports/                        # Auto generated reports
├── requirements.txt
└── .env                            # API keys (create manually)

---

## Setup Instructions

### Step 1 - Clone Repository
```bash
git clone https://github.com/Divyanshur7910/soar-platform.git
cd soar-platform
```

### Step 2 - Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 3 - Get Your Own Free API Keys
Get free API keys from these websites:
- VirusTotal   : https://virustotal.com
- AbuseIPDB    : https://abuseipdb.com
- AlienVault   : https://otx.alienvault.com
- MalwareBazaar: https://bazaar.abuse.ch

### Step 4 - Create .env File
Create a file called .env in the root folder:
VIRUSTOTAL_API_KEY=your_key_here
ABUSEIPDB_API_KEY=your_key_here
ALIENVAULT_API_KEY=your_key_here
MALWAREBAZAAR_API_KEY=your_key_here

### Step 5 - Download Datasets (Optional)
Install kaggle CLI:
```bash
pip install kaggle
```

Setup kaggle API key from kaggle.com then run:
```bash
cd option1_datasets/brute_force
kaggle datasets download -d devendra416/ddos-datasets --unzip

cd ../phishing
kaggle datasets download -d sid321axn/malicious-urls-dataset --unzip

cd ../malware
kaggle datasets download -d amauricio/pe-files-malwares --unzip

cd ../network_anomaly
kaggle datasets download -d mrwellsdavid/unsw-nb15 --unzip
```

### Step 6 - Run Platform
```bash
cd soar-platform
source venv/bin/activate
python main.py
```

---

## How It Works
Input (Dataset or Simulation)
↓
Auto Attack Type Detection
↓
Correct Playbook Triggered
↓
Threat Intel Enrichment
(VirusTotal + AbuseIPDB + AlienVault + MalwareBazaar)
↓
MITRE ATT&CK Risk Scoring
↓
Severity Classification
(CRITICAL / HIGH / MEDIUM / LOW)
↓
Automated Response Actions
↓
JSON + PDF Incident Report Generated

---

## JSON Output Format
Every incident generates this JSON:
```json
{
    "incident_id"    : "INC-20260404041940",
    "playbook_name"  : "Phishing Detection Playbook",
    "mitre_technique": "T1566 - Phishing",
    "alert_type"     : "PHISHING_URL",
    "severity"       : "HIGH",
    "risk_score"     : 55,
    "status"         : "CLOSED",
    "start_time"     : "2026-04-04 04:19:40",
    "end_time"       : "2026-04-04 04:19:42",
    "alert_details"  : {},
    "threat_intel"   : {},
    "response_taken" : [],
    "source"         : "option1_dataset"
}
```

---

## API Integration (For Backend Team)

### Endpoints Backend Must Build
POST /api/incidents
→ Receives incident JSON from SOAR
→ Saves to database
GET /api/incidents
→ Returns all incidents
GET /api/incidents/{incident_id}
→ Returns single incident
GET /api/incidents?severity=CRITICAL
→ Returns filtered incidents
GET /api/stats
→ Returns dashboard statistics

### Database Schema
TABLE: incidents
incident_id      VARCHAR  (Primary Key)
playbook_name    VARCHAR
mitre_technique  VARCHAR
alert_type       VARCHAR
severity         VARCHAR
risk_score       INTEGER
status           VARCHAR
start_time       DATETIME
end_time         DATETIME
alert_details    JSON
threat_intel     JSON
response_taken   JSON
source           VARCHAR
created_at       DATETIME

---

## Frontend Dashboard Requirements

Summary Cards
→ Total incidents
→ CRITICAL count (red)
→ HIGH count (orange)
→ MEDIUM count (yellow)
→ LOW count (green)
Incidents Table
→ Incident ID
→ Attack Type
→ Severity (color coded)
→ Risk Score
→ Timestamp
→ Status
Incident Detail Page
→ All incident fields
→ Response actions taken
→ Threat intel results
→ Download PDF button
Severity Chart
→ Pie/bar chart
Reports Section
→ List of PDF reports
→ Download button


---

## Future Scope
- Wazuh SIEM integration for real time detection
- Machine learning based anomaly detection
- Additional playbooks (Ransomware, DDoS, IOC)
- Cloud deployment
- Mobile alerts

---

## References
- NIST SP 800-61: https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-61r2.pdf
- MITRE ATT&CK: https://attack.mitre.org
- VirusTotal API: https://developers.virustotal.com
- AbuseIPDB API: https://www.abuseipdb.com/api