# Simulates Network Anomaly/Intrusion Detection logs
# Risk scoring based on MITRE ATT&CK T1071, T1030

import random
import time
from datetime import datetime

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

# Attack categories mapped to MITRE ATT&CK
ATTACK_CATEGORIES = {
    "Reconnaissance" : "T1595",
    "Exploits"       : "T1203",
    "DoS"            : "T1499",
    "Backdoor"       : "T1071",
    "Shellcode"      : "T1059",
    "Worms"          : "T1210",
    "Fuzzers"        : "T1190",
}

# Protocols
PROTOCOLS = ["tcp", "udp", "ospf", "icmp", "arp"]

# Services
SERVICES  = ["http", "ftp", "ssh", "dns", "smtp", "-"]

# States
STATES    = ["INT", "FIN", "CON", "REQ", "RST"]

# Simulated IPs
ATTACKER_IPS = ["45.33.32.156", "198.51.100.77", "192.168.1.105", "10.0.0.55"]
TARGET_IPS   = ["192.168.1.1",  "192.168.1.10",  "192.168.1.20",  "10.0.0.1"]


# ─────────────────────────────────────────────
# LOG GENERATOR
# ─────────────────────────────────────────────
def generate_attack_traffic():
    attack_cat = random.choice(list(ATTACK_CATEGORIES.keys()))
    return {
        "timestamp"   : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "event_type"  : "NETWORK_TRAFFIC",
        "src_ip"      : random.choice(ATTACKER_IPS),
        "dst_ip"      : random.choice(TARGET_IPS),
        "protocol"    : random.choice(PROTOCOLS),
        "service"     : random.choice(SERVICES),
        "state"       : random.choice(STATES),
        "src_bytes"   : random.randint(5000, 500000),
        "dst_bytes"   : random.randint(0, 1000),
        "src_packets" : random.randint(100, 5000),
        "dst_packets" : random.randint(0, 10),
        "attack_cat"  : attack_cat,
        "label"       : 1
    }

def generate_normal_traffic():
    return {
        "timestamp"   : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "event_type"  : "NETWORK_TRAFFIC",
        "src_ip"      : f"192.168.1.{random.randint(1, 254)}",
        "dst_ip"      : f"192.168.1.{random.randint(1, 254)}",
        "protocol"    : random.choice(["tcp", "udp"]),
        "service"     : random.choice(["http", "dns", "smtp"]),
        "state"       : "FIN",
        "src_bytes"   : random.randint(100, 5000),
        "dst_bytes"   : random.randint(100, 5000),
        "src_packets" : random.randint(1, 50),
        "dst_packets" : random.randint(1, 50),
        "attack_cat"  : "Normal",
        "label"       : 0
    }


# ─────────────────────────────────────────────
# NETWORK ANOMALY DETECTOR
# Based on MITRE ATT&CK T1071, T1030
# ─────────────────────────────────────────────
def analyze_traffic(traffic):
    score   = 0
    reasons = []

    if traffic['label'] == 0:
        return 0, "LOW", []

    attack_cat = traffic['attack_cat']
    mitre_id   = ATTACK_CATEGORIES.get(attack_cat, "T1071")

    # HIGH CONFIDENCE (40pts) — Direct ATT&CK TTP match
    critical_attacks = ["Backdoor", "Shellcode", "Worms"]
    high_attacks     = ["Exploits", "DoS"]

    if attack_cat in critical_attacks:
        score += 40
        reasons.append(f"[HIGH] {attack_cat} attack category detected ({mitre_id} Direct TTP Match)")
    elif attack_cat in high_attacks:
        score += 30
        reasons.append(f"[HIGH] {attack_cat} attack category detected ({mitre_id} Direct TTP Match)")

    # HIGH CONFIDENCE (35pts) — MITRE T1071
    # Unusual protocol usage — C2 communication indicator
    unusual_protocols = ["ospf", "arp", "icmp"]
    if traffic['protocol'] in unusual_protocols:
        score += 35
        reasons.append(f"[HIGH] Unusual protocol '{traffic['protocol']}' — possible C2 communication (T1071)")

    # MEDIUM CONFIDENCE (15pts) — MITRE T1030
    # Abnormal byte ratio — data exfiltration indicator
    src_bytes = traffic['src_bytes']
    dst_bytes = traffic['dst_bytes']
    if dst_bytes > 0 and src_bytes / dst_bytes > 100:
        score += 15
        reasons.append(f"[MEDIUM] Abnormal src/dst byte ratio ({src_bytes}/{dst_bytes}) — possible exfiltration (T1030)")
    elif dst_bytes == 0 and src_bytes > 10000:
        score += 15
        reasons.append(f"[MEDIUM] One-way large data transfer — possible exfiltration (T1030)")

    # LOW CONFIDENCE (10pts)
    # High packet rate
    if traffic['src_packets'] > 1000:
        score += 10
        reasons.append(f"[LOW] High packet rate: {traffic['src_packets']} packets")

    # Determine severity
    if score >= 75:
        severity = "CRITICAL"
    elif score >= 50:
        severity = "HIGH"
    elif score >= 25:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    return score, severity, reasons


def detect_anomalies(traffic_logs):
    alerts = []
    for traffic in traffic_logs:
        score, severity, reasons = analyze_traffic(traffic)
        if score >= 25:
            alerts.append({
                "alert_type" : "NETWORK_ANOMALY_DETECTED",
                "severity"   : severity,
                "timestamp"  : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "source"     : "option2_simulation",
                "details"    : {
                    "src_ip"     : traffic['src_ip'],
                    "dst_ip"     : traffic['dst_ip'],
                    "protocol"   : traffic['protocol'],
                    "service"    : traffic['service'],
                    "src_bytes"  : traffic['src_bytes'],
                    "dst_bytes"  : traffic['dst_bytes'],
                    "attack_cat" : traffic['attack_cat'],
                    "mitre_id"   : ATTACK_CATEGORIES.get(traffic['attack_cat'], "T1071"),
                    "risk_score" : score,
                    "reasons"    : reasons
                }
            })
    return alerts


# ─────────────────────────────────────────────
# MAIN SIMULATION
# ─────────────────────────────────────────────
def simulate(num_traffic=10):
    print("\n" + "="*60)
    print("   NETWORK ANOMALY DETECTION SIMULATION")
    print("="*60)
    print(f"[*] Simulating {num_traffic} network traffic flows...")
    print("="*60 + "\n")

    traffic_logs = []

    for i in range(num_traffic):
        # 60% attack, 40% normal
        if random.random() < 0.6:
            traffic = generate_attack_traffic()
            tag     = f"[SUSPECT] {traffic['attack_cat']:<15}"
        else:
            traffic = generate_normal_traffic()
            tag     = "[OK] Normal       "

        print(f"[Flow {i+1:02d}] {tag} | {traffic['src_ip']:<15} -> {traffic['dst_ip']:<15} | Proto: {traffic['protocol']:<5} | Bytes: {traffic['src_bytes']}")
        traffic_logs.append(traffic)
        time.sleep(0.1)

    print("\n" + "="*60)
    print("[*] Analyzing traffic for anomalies...")
    print("="*60)

    alerts = detect_anomalies(traffic_logs)

    if alerts:
        print(f"\n[ALERT] {len(alerts)} NETWORK ANOMALY ALERT(S) TRIGGERED!\n")
        for alert in alerts:
            print(f"   Src IP     : {alert['details']['src_ip']}")
            print(f"   Dst IP     : {alert['details']['dst_ip']}")
            print(f"   Protocol   : {alert['details']['protocol']}")
            print(f"   Attack Cat : {alert['details']['attack_cat']}")
            print(f"   MITRE ID   : {alert['details']['mitre_id']}")
            print(f"   Risk Score : {alert['details']['risk_score']}/100")
            print(f"   Severity   : {alert['severity']}")
            print(f"   Reasons    :")
            for r in alert['details']['reasons']:
                print(f"      -> {r}")
            print()
    else:
        print("\n[*] No anomalies detected.")

    return traffic_logs, alerts


if __name__ == "__main__":
    traffic_logs, alerts = simulate(num_traffic=10)