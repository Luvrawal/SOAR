# Simulates SSH/Login Brute Force Attack logs

import random
import time
from datetime import datetime

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

THRESHOLD = 5          # Failed attempts before alert triggers
TIME_WINDOW = 60       # Seconds to consider for brute force detection

# Common attacker IPs (simulated)

ATTACKER_IPS = [
    "192.168.1.105",
    "10.0.0.55",
    "172.16.0.200",
    "45.33.32.156",
    "198.51.100.77"
]

# Common target usernames attackers try

USERNAMES = ["admin", "root", "user", "test", "administrator", "kali"]

# Target system

TARGET_IP = "192.168.1.1"
TARGET_PORT = 22  # SSH port


# ─────────────────────────────────────────────
# LOG GENERATOR
# ─────────────────────────────────────────────

def generate_failed_login(attacker_ip, username):
    return {
        "timestamp"    : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "event_type"   : "FAILED_LOGIN",
        "src_ip"       : attacker_ip,
        "dst_ip"       : TARGET_IP,
        "dst_port"     : TARGET_PORT,
        "username"     : username,
        "protocol"     : "SSH",
        "status"       : "FAILED"
    }

def generate_successful_login(attacker_ip, username):
    return {
        "timestamp"    : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "event_type"   : "SUCCESSFUL_LOGIN",
        "src_ip"       : attacker_ip,
        "dst_ip"       : TARGET_IP,
        "dst_port"     : TARGET_PORT,
        "username"     : username,
        "protocol"     : "SSH",
        "status"       : "SUCCESS"
    }


# ─────────────────────────────────────────────
# BRUTE FORCE DETECTOR
# ─────────────────────────────────────────────

def detect_brute_force(logs):
    from collections import defaultdict

    ip_attempts  = defaultdict(int)
    ip_usernames = defaultdict(set)
    ip_hours     = defaultdict(set)
    ip_targets   = defaultdict(set)

    privileged   = ['admin', 'root', 'administrator']

    for log in logs:
        if log['event_type'] == 'FAILED_LOGIN':
            ip = log['src_ip']
            ip_attempts[ip]  += 1
            ip_usernames[ip].add(log['username'])
            ip_hours[ip].add(datetime.now().hour)
            ip_targets[ip].add(log['username'])

    alerts = []

    for ip, count in ip_attempts.items():
        if count < THRESHOLD:
            continue

        score   = 0
        reasons = []

        # HIGH CONFIDENCE (40pts) — MITRE T1110
        # High frequency failed logins from same IP
        if count > 10:
            score += 40
            reasons.append(f"[HIGH] {count} failed logins from same IP (T1110 Brute Force)")

        # HIGH CONFIDENCE (35pts) — MITRE T1110.004
        # Multiple usernames tried — credential stuffing
        if len(ip_usernames[ip]) > 3:
            score += 35
            reasons.append(f"[HIGH] {len(ip_usernames[ip])} different usernames tried (T1110.004 Credential Stuffing)")

        # MEDIUM CONFIDENCE (15pts) — Privilege escalation attempt
        # Targeting privileged accounts
        if any(u in ip_usernames[ip] for u in privileged):
            score += 15
            reasons.append("[MEDIUM] Privileged accounts targeted (admin/root)")

        # LOW CONFIDENCE (10pts)
        # Odd hours login attempt
        odd_hours = [h for h in ip_hours[ip] if h < 6 or h > 22]
        if odd_hours:
            score += 10
            reasons.append("[LOW] Login attempts during unusual hours")

        # Determine severity
        if score >= 75:
            severity = "CRITICAL"
        elif score >= 50:
            severity = "HIGH"
        elif score >= 25:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        alerts.append({
            "alert_type" : "BRUTE_FORCE_DETECTED",
            "severity"   : severity,
            "timestamp"  : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source"     : "option2_simulation",
            "details"    : {
                "attacker_ip"     : ip,
                "target_ip"       : TARGET_IP,
                "target_port"     : TARGET_PORT,
                "failed_attempts" : count,
                "usernames_tried" : list(ip_usernames[ip]),
                "risk_score"      : score,
                "reasons"         : reasons,
                "threshold"       : THRESHOLD,
                "protocol"        : "SSH"
            }
        })

    return alerts


# ─────────────────────────────────────────────
# MAIN SIMULATION
# ─────────────────────────────────────────────

def simulate(num_attempts=20, show_logs=True):
    print("\n" + "="*60)
    print("   BRUTE FORCE ATTACK SIMULATION")
    print("="*60)
    print(f"[*] Target IP   : {TARGET_IP}")
    print(f"[*] Target Port : {TARGET_PORT} (SSH)")
    print(f"[*] Threshold   : {THRESHOLD} failed attempts")
    print(f"[*] Simulating  : {num_attempts} login attempts")
    print("="*60)

    logs = []
    attacker_ip = random.choice(ATTACKER_IPS)
    print(f"\n[*] Attacker IP : {attacker_ip}\n")

    for i in range(num_attempts):
        username = random.choice(USERNAMES)

        # Last attempt succeeds (simulating successful brute force)
        if i == num_attempts - 1:
            log = generate_successful_login(attacker_ip, username)
            print(f"[!] Attempt {i+1:02d} : SUCCESS - {username}@{TARGET_IP} (BREACH!)")
        else:
            log = generate_failed_login(attacker_ip, username)
            print(f"[-] Attempt {i+1:02d} : FAILED  - {username}@{TARGET_IP}")

        logs.append(log)
        time.sleep(0.1)  # Small delay for realistic feel

    print("\n" + "="*60)
    print("[*] Analyzing logs for brute force pattern...")
    print("="*60)

    alerts = detect_brute_force(logs)

    if alerts:
            for alert in alerts:
                print(f"\n[ALERT] ALERT TRIGGERED!")
                print(f"   Type       : {alert['alert_type']}")
                print(f"   Severity   : {alert['severity']}")
                print(f"   Risk Score : {alert['details']['risk_score']}/100")
                print(f"   Attacker   : {alert['details']['attacker_ip']}")
                print(f"   Attempts   : {alert['details']['failed_attempts']}")
                print(f"   Usernames  : {alert['details']['usernames_tried']}")
                print(f"   Time       : {alert['timestamp']}")
                print(f"   Reasons    :")
                for r in alert['details']['reasons']:
                    print(f"      -> {r}")
    else:
        print("\n[*] No brute force detected.")

    return logs, alerts


if __name__ == "__main__":
    logs, alerts = simulate(num_attempts=20)