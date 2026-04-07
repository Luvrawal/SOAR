import pandas as pd
from datetime import datetime
import os

# ─────────────────────────────────────────────
# STANDARD ALERT FORMAT
# Every parser returns alerts in this format
# ─────────────────────────────────────────────

def create_alert(alert_type, severity, details, source):
    return {
        "alert_type"  : alert_type,
        "severity"    : severity,
        "timestamp"   : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source"      : source,
        "details"     : details
    }


# ─────────────────────────────────────────────
# PARSER 1 — BRUTE FORCE (DDoS Dataset)
# ─────────────────────────────────────────────

def parse_brute_force(filepath):
    print(f"\n[*] Loading Brute Force dataset from {filepath}...")
    alerts = []

    try:
        df = pd.read_csv(filepath, nrows=5000)
        print(f"[*] Total rows loaded: {len(df)}")

        # Filter only attack rows
        attack_df = df[df['Label'] != 'BENIGN']
        print(f"[*] Attack rows found: {len(attack_df)}")

        for _, row in attack_df.iterrows():
            details = {
                "src_ip"       : row.get('Src IP', 'Unknown'),
                "dst_ip"       : row.get('Dst IP', 'Unknown'),
                "src_port"     : row.get('Src Port', 0),
                "dst_port"     : row.get('Dst Port', 0),
                "protocol"     : row.get('Protocol', 'Unknown'),
                "flow_pkts_s"  : row.get('Flow Pkts/s', 0),
                "syn_flag_cnt" : row.get('SYN Flag Cnt', 0),
                "rst_flag_cnt" : row.get('RST Flag Cnt', 0),
                "attack_label" : row.get('Label', 'Unknown')
            }

            # Determine severity based on packet rate
            flow_pkts = float(row.get('Flow Pkts/s', 0))
            if flow_pkts > 10000:
                severity = "CRITICAL"
            elif flow_pkts > 5000:
                severity = "HIGH"
            elif flow_pkts > 1000:
                severity = "MEDIUM"
            else:
                severity = "LOW"

            alert = create_alert(
                alert_type = "BRUTE_FORCE_DDOS",
                severity   = severity,
                details    = details,
                source     = "option1_dataset"
            )
            alerts.append(alert)

    except Exception as e:
        print(f"[ERROR] Failed to parse brute force dataset: {e}")

    print(f"[*] Total alerts generated: {len(alerts)}")
    return alerts


# ─────────────────────────────────────────────
# PARSER 2 — PHISHING (Malicious URLs Dataset)
# ─────────────────────────────────────────────
def parse_phishing(filepath):
    print(f"\n[*] Loading Phishing dataset from {filepath}...")
    alerts = []

    try:
        df = pd.read_csv(filepath)
        print(f"[*] Total rows loaded: {len(df)}")

        # Filter only malicious/phishing rows
        attack_df = df[df['type'] != 'benign']
        print(f"[*] Malicious URLs found: {len(attack_df)}")

        for _, row in attack_df.iterrows():
            url  = row.get('url', '')
            utype = row.get('type', 'unknown')

            details = {
                "url"          : url,
                "attack_type"  : utype,
                "url_length"   : len(str(url)),
                "has_ip"       : any(c.isdigit() for c in str(url).split('/')[0]),
                "has_https"    : str(url).startswith('https'),
            }

            # Determine severity based on attack type
            if utype == 'phishing':
                severity = "HIGH"
            elif utype == 'malware':
                severity = "CRITICAL"
            elif utype == 'defacement':
                severity = "MEDIUM"
            else:
                severity = "LOW"

            alert = create_alert(
                alert_type = "PHISHING_URL",
                severity   = severity,
                details    = details,
                source     = "option1_dataset"
            )
            alerts.append(alert)

    except Exception as e:
        print(f"[ERROR] Failed to parse phishing dataset: {e}")

    print(f"[*] Total alerts generated: {len(alerts)}")
    return alerts


# ─────────────────────────────────────────────
# PARSER 3 — MALWARE (PE Files Dataset)
# ─────────────────────────────────────────────
def parse_malware(filepath):
    print(f"\n[*] Loading Malware dataset from {filepath}...")
    alerts = []

    try:
        df = pd.read_csv(filepath)
        print(f"[*] Total rows loaded: {len(df)}")

        # Filter only malware rows (Malware column = 1)
        attack_df = df[df['Malware'] == 1]
        print(f"[*] Malware samples found: {len(attack_df)}")

        for _, row in attack_df.iterrows():
            details = {
                "file_name"                  : row.get('Name', 'Unknown'),
                "suspicious_import_functions": row.get('SuspiciousImportFunctions', 0),
                "suspicious_name_section"    : row.get('SuspiciousNameSection', 0),
                "section_max_entropy"        : row.get('SectionMaxEntropy', 0),
                "number_of_sections"         : row.get('NumberOfSections', 0),
                "malware_label"              : 1
            }

            # Determine severity based on entropy and suspicious imports
            entropy = float(row.get('SectionMaxEntropy', 0))
            suspicious = int(row.get('SuspiciousImportFunctions', 0))

            if entropy > 7.0 or suspicious > 5:
                severity = "CRITICAL"
            elif entropy > 6.0 or suspicious > 3:
                severity = "HIGH"
            elif entropy > 5.0 or suspicious > 1:
                severity = "MEDIUM"
            else:
                severity = "LOW"

            alert = create_alert(
                alert_type = "MALWARE_DETECTED",
                severity   = severity,
                details    = details,
                source     = "option1_dataset"
            )
            alerts.append(alert)

    except Exception as e:
        print(f"[ERROR] Failed to parse malware dataset: {e}")

    print(f"[*] Total alerts generated: {len(alerts)}")
    return alerts


# ─────────────────────────────────────────────
# PARSER 4 — NETWORK ANOMALY (UNSW-NB15)
# ─────────────────────────────────────────────
def parse_network_anomaly(filepath):
    print(f"\n[*] Loading Network Anomaly dataset from {filepath}...")
    alerts = []

    try:
        df = pd.read_csv(filepath, nrows=5000)
        print(f"[*] Total rows loaded: {len(df)}")

        # Filter only attack rows (label = 1)
        attack_df = df[df['label'] == 1]
        print(f"[*] Attack rows found: {len(attack_df)}")

        for _, row in attack_df.iterrows():
            details = {
                "protocol"    : row.get('proto', 'Unknown'),
                "service"     : row.get('service', 'Unknown'),
                "state"       : row.get('state', 'Unknown'),
                "src_bytes"   : row.get('sbytes', 0),
                "dst_bytes"   : row.get('dbytes', 0),
                "attack_cat"  : row.get('attack_cat', 'Unknown'),
                "src_packets" : row.get('spkts', 0),
                "dst_packets" : row.get('dpkts', 0),
            }

            # Determine severity based on attack category
            attack_cat = str(row.get('attack_cat', '')).strip().lower()
            if attack_cat in ['backdoor', 'shellcode', 'worms']:
                severity = "CRITICAL"
            elif attack_cat in ['exploits', 'dos']:
                severity = "HIGH"
            elif attack_cat in ['reconnaissance', 'fuzzers']:
                severity = "MEDIUM"
            else:
                severity = "LOW"

            alert = create_alert(
                alert_type = "NETWORK_ANOMALY",
                severity   = severity,
                details    = details,
                source     = "option1_dataset"
            )
            alerts.append(alert)

    except Exception as e:
        print(f"[ERROR] Failed to parse network anomaly dataset: {e}")

    print(f"[*] Total alerts generated: {len(alerts)}")
    return alerts


# ─────────────────────────────────────────────
# TEST ALL PARSERS
# ─────────────────────────────────────────────
if __name__ == "__main__":
    base = os.getenv("SOAR_DATASET_DIR", os.path.expanduser("~/Desktop/soar_platform/option1_datasets"))

    # Test Brute Force Parser
    bf_alerts = parse_brute_force(
        f"{base}/brute_force/ddos_balanced/final_dataset.csv"
    )
    print(f"\nSample Brute Force Alert:\n{bf_alerts[0] if bf_alerts else 'No alerts'}")

    # Test Phishing Parser
    ph_alerts = parse_phishing(
        f"{base}/phishing/malicious_phish.csv"
    )
    print(f"\nSample Phishing Alert:\n{ph_alerts[0] if ph_alerts else 'No alerts'}")

    # Test Malware Parser
    mw_alerts = parse_malware(
        f"{base}/malware/dataset_malwares.csv"
    )
    print(f"\nSample Malware Alert:\n{mw_alerts[0] if mw_alerts else 'No alerts'}")

    # Test Network Anomaly Parser
    na_alerts = parse_network_anomaly(
        f"{base}/network_anomaly/UNSW_NB15_training-set.csv"
    )
    print(f"\nSample Network Anomaly Alert:\n{na_alerts[0] if na_alerts else 'No alerts'}")