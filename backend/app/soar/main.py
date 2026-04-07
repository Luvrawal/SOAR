# main.py
# SOAR Platform - Main Orchestrator
# Automatically detects attack type and triggers correct playbook
# Follows NIST SP 800-61 + MITRE ATT&CK Framework

import os
import sys
import time
import json
from datetime import datetime

# Import all playbooks
from app.soar.playbooks.brute_force_playbook import BruteForcePlaybook
from app.soar.playbooks.phishing_playbook import PhishingPlaybook
from app.soar.playbooks.malware_playbook import MalwarePlaybook
from app.soar.playbooks.network_anomaly_playbook import NetworkAnomalyPlaybook

# Import parsers
from app.soar.utils.log_parser import (
    parse_brute_force,
    parse_phishing,
    parse_malware,
    parse_network_anomaly
)

# Import simulators
from app.soar.option2_simulation.simulate_bruteforce import simulate as sim_bruteforce
from app.soar.option2_simulation.simulate_phishing import simulate as sim_phishing
from app.soar.option2_simulation.simulate_malware import simulate as sim_malware
from app.soar.option2_simulation.simulate_network_anomaly import simulate as sim_network

# Import reporter
from app.soar.utils.reporter import generate_pdf_report

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
BASE_DIR = os.getenv("SOAR_BASE_DIR", os.path.dirname(__file__))
DATASET_DIR = os.getenv("SOAR_DATASET_DIR", f"{BASE_DIR}/option1_datasets")
REPORTS_DIR = os.getenv("SOAR_REPORTS_DIR", f"{BASE_DIR}/reports")

# Cache to avoid duplicate API calls (NOTE 11)
ip_cache   = {}
url_cache  = {}
hash_cache = {}


# ─────────────────────────────────────────────
# AUTO ATTACK TYPE CLASSIFIER (NOTE 1)
# Automatically identifies attack type
# Never asks user to choose attack type
# ─────────────────────────────────────────────
def identify_attack_type(alert):
    """
    Automatically identifies attack type from alert data
    No human intervention required
    Based on alert_type field set by parsers/simulators
    """
    alert_type = alert.get('alert_type', '').upper()

    # Brute Force indicators
    if any(x in alert_type for x in ['BRUTE', 'DDOS', 'LOGIN']):
        return 'brute_force'

    # Phishing indicators
    if any(x in alert_type for x in ['PHISH', 'URL', 'EMAIL']):
        return 'phishing'

    # Malware indicators
    if any(x in alert_type for x in ['MALWARE', 'VIRUS', 'RANSOMWARE']):
        return 'malware'

    # Network anomaly indicators
    if any(x in alert_type for x in ['NETWORK', 'ANOMALY', 'INTRUSION']):
        return 'network_anomaly'

    # Check details for more clues
    details = alert.get('details', {})

    if details.get('src_ip') and details.get('failed_attempts'):
        return 'brute_force'

    if details.get('url') or details.get('sender'):
        return 'phishing'

    if details.get('file_name') or details.get('entropy'):
        return 'malware'

    if details.get('protocol') or details.get('attack_cat'):
        return 'network_anomaly'

    return 'unknown'


# ─────────────────────────────────────────────
# PLAYBOOK RUNNER
# ─────────────────────────────────────────────
def run_playbook(alert):
    """
    Auto detect attack type and run correct playbook
    Returns incident report
    """
    attack_type = identify_attack_type(alert)

    if attack_type == 'brute_force':
        playbook = BruteForcePlaybook()
    elif attack_type == 'phishing':
        playbook = PhishingPlaybook()
    elif attack_type == 'malware':
        playbook = MalwarePlaybook()
    elif attack_type == 'network_anomaly':
        playbook = NetworkAnomalyPlaybook()
    else:
        print(f"  [!] Unknown attack type for alert: {alert.get('alert_type')}")
        return None

    # Run playbook
    report = playbook.run(alert)

    # Generate PDF report
    if report:
        generate_pdf_report(report)

    return report


# ─────────────────────────────────────────────
# PROCESS MULTIPLE ALERTS WITH CACHING
# ─────────────────────────────────────────────
def process_alerts(alerts, max_alerts=50):
    """
    Process multiple alerts with smart caching
    Same IP/URL/Hash queried only ONCE
    Results reused for duplicate alerts
    """
    print(f"\n  [*] Processing {min(len(alerts), max_alerts)} alerts...")
    print(f"  [*] Total available: {len(alerts)}")
    print(f"  {'-'*50}")

    results = {
        "total"    : 0,
        "critical" : 0,
        "high"     : 0,
        "medium"   : 0,
        "low"      : 0,
        "unknown"  : 0
    }

    # Cache storage — avoids duplicate API calls
    seen_ips   = set()
    seen_urls  = set()
    seen_hash  = set()

    for i, alert in enumerate(alerts[:max_alerts]):
        print(f"\n  [Alert {i+1}/{min(len(alerts), max_alerts)}]")

        # Check if we already processed this indicator
        details = alert.get('details', {})
        src_ip  = details.get('src_ip') or details.get('attacker_ip', '')
        url     = details.get('url', '')
        fhash   = details.get('file_name', '')

        # Skip if same IP already fully processed
        if src_ip and src_ip in seen_ips:
            print(f"  [*] Skipping duplicate IP: {src_ip} (cached)")
            continue

        if url and url in seen_urls:
            print(f"  [*] Skipping duplicate URL (cached)")
            continue

        # Add to seen cache
        if src_ip:
            seen_ips.add(src_ip)
        if url:
            seen_urls.add(url)
        if fhash:
            seen_hash.add(fhash)

        report = run_playbook(alert)

        if report:
            results['total'] += 1
            severity = report.get('severity', 'unknown').lower()
            if severity in results:
                results[severity] += 1

        # Small delay to avoid API rate limiting
        time.sleep(0.5)

    return results


# ─────────────────────────────────────────────
# DISPLAY SUMMARY
# ─────────────────────────────────────────────
def display_summary(results, source):
    """Display final processing summary"""
    print(f"\n{'='*60}")
    print(f"  PROCESSING SUMMARY")
    print(f"{'='*60}")
    print(f"  Source          : {source}")
    print(f"  Total Processed : {results['total']}")
    print(f"  {'-'*40}")
    print(f"  CRITICAL       : {results['critical']}")
    print(f"  HIGH           : {results['high']}")
    print(f"  MEDIUM         : {results['medium']}")
    print(f"  LOW            : {results['low']}")
    print(f"  {'-'*40}")
    print(f"  Reports saved to: {REPORTS_DIR}")
    print(f"{'='*60}\n")


# ─────────────────────────────────────────────
# OPTION 1 — DATASET MODE
# ─────────────────────────────────────────────
def run_dataset_mode():
    """
    Run SOAR platform using real datasets
    Option 1 from our plan
    """
    print(f"\n{'='*60}")
    print(f"  SOAR PLATFORM - DATASET MODE")
    print(f"{'='*60}")
    print(f"  Select dataset to process:")
    print(f"  1. Brute Force  (DDoS Dataset)")
    print(f"  2. Phishing     (Malicious URLs)")
    print(f"  3. Malware      (PE Files)")
    print(f"  4. Network Anomaly (UNSW-NB15)")
    print(f"  5. Run ALL datasets")
    print(f"{'='*60}")

    choice = input("\n  Enter choice (1-5): ").strip()

    if choice == '1' or choice == '5':
        print(f"\n[*] Loading Brute Force dataset...")
        alerts = parse_brute_force(
            f"{DATASET_DIR}/brute_force/ddos_balanced/final_dataset.csv"
        )
        results = process_alerts(alerts, max_alerts=20)
        display_summary(results, "Brute Force Dataset")

    if choice == '2' or choice == '5':
        print(f"\n[*] Loading Phishing dataset...")
        alerts = parse_phishing(
            f"{DATASET_DIR}/phishing/malicious_phish.csv"
        )
        results = process_alerts(alerts, max_alerts=20)
        display_summary(results, "Phishing Dataset")

    if choice == '3' or choice == '5':
        print(f"\n[*] Loading Malware dataset...")
        alerts = parse_malware(
            f"{DATASET_DIR}/malware/dataset_malwares.csv"
        )
        results = process_alerts(alerts, max_alerts=20)
        display_summary(results, "Malware Dataset")

    if choice == '4' or choice == '5':
        print(f"\n[*] Loading Network Anomaly dataset...")
        alerts = parse_network_anomaly(
            f"{DATASET_DIR}/network_anomaly/UNSW-NB15_training-set.csv"
        )
        results = process_alerts(alerts, max_alerts=20)
        display_summary(results, "Network Anomaly Dataset")


# ─────────────────────────────────────────────
# OPTION 2 — SIMULATION MODE
# ─────────────────────────────────────────────
def run_simulation_mode():
    """
    Run SOAR platform using live simulations
    Option 2 from our plan
    Perfect for live presentations!
    """
    print(f"\n{'='*60}")
    print(f"  SOAR PLATFORM - SIMULATION MODE")
    print(f"{'='*60}")
    print(f"  Select attack to simulate:")
    print(f"  1. Brute Force Attack")
    print(f"  2. Phishing Email Attack")
    print(f"  3. Malware Detection")
    print(f"  4. Network Anomaly")
    print(f"  5. Run ALL simulations")
    print(f"{'='*60}")

    choice = input("\n  Enter choice (1-5): ").strip()

    if choice == '1' or choice == '5':
        print(f"\n[*] Simulating Brute Force Attack...")
        _, alerts = sim_bruteforce(num_attempts=20)
        if alerts:
            results = process_alerts(alerts, max_alerts=len(alerts))
            display_summary(results, "Brute Force Simulation")

    if choice == '2' or choice == '5':
        print(f"\n[*] Simulating Phishing Attack...")
        _, alerts = sim_phishing(num_emails=10)
        if alerts:
            results = process_alerts(alerts, max_alerts=len(alerts))
            display_summary(results, "Phishing Simulation")

    if choice == '3' or choice == '5':
        print(f"\n[*] Simulating Malware Detection...")
        _, alerts = sim_malware(num_files=10)
        if alerts:
            results = process_alerts(alerts, max_alerts=len(alerts))
            display_summary(results, "Malware Simulation")

    if choice == '4' or choice == '5':
        print(f"\n[*] Simulating Network Anomaly...")
        _, alerts = sim_network(num_traffic=10)
        if alerts:
            results = process_alerts(alerts, max_alerts=len(alerts))
            display_summary(results, "Network Anomaly Simulation")


# ─────────────────────────────────────────────
# MAIN MENU
# ─────────────────────────────────────────────
def main():
    """
    Main entry point for SOAR Platform
    """
    print(f"\n{'='*60}")
    print(f"  ██████╗  ██████╗  █████╗ ██████╗ ")
    print(f"  ██╔════╝ ██╔═══██╗██╔══██╗██╔══██╗")
    print(f"  ███████╗ ██║   ██║███████║██████╔╝")
    print(f"  ╚════██║ ██║   ██║██╔══██║██╔══██╗")
    print(f"  ██████╔╝ ╚██████╔╝██║  ██║██║  ██║")
    print(f"  ╚═════╝   ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝")
    print(f"{'='*60}")
    print(f"  Security Orchestration, Automation & Response")
    print(f"  Framework: NIST SP 800-61 + MITRE ATT&CK")
    print(f"  Version  : 1.0")
    print(f"{'='*60}")
    print(f"\n  Select Mode:")
    print(f"  1. Dataset Mode  (Real security datasets)")
    print(f"  2. Simulation Mode (Live attack simulation)")
    print(f"  3. Exit")
    print(f"{'='*60}")

    choice = input("\n  Enter choice (1-3): ").strip()

    if choice == '1':
        run_dataset_mode()
    elif choice == '2':
        run_simulation_mode()
    elif choice == '3':
        print("\n  Goodbye!\n")
        sys.exit(0)
    else:
        print("\n  Invalid choice. Please try again.")
        main()


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    main()
