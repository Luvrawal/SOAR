#  Brute Force Attack Playbook
# MITRE ATT&CK: T1110 - Brute Force
# NIST SP 800-61 compliant

import os

from app.soar.playbooks.base_playbook import BasePlaybook
from app.soar.utils.threat_intel import enrich_ip

class BruteForcePlaybook(BasePlaybook):

    def __init__(self):
        super().__init__(
            name             = "Brute Force Detection Playbook",
            mitre_technique  = "T1110 - Brute Force"
        )

    # ─────────────────────────────────────────────
    # PHASE 2 — ENRICH
    # ─────────────────────────────────────────────
    def enrich(self):
        """
        Enrich alert with threat intelligence
        Queries: VirusTotal, AbuseIPDB, AlienVault OTX
        """
        details    = self.alert.get('details', {})
        src_ip     = details.get('src_ip') or details.get('attacker_ip', '')

        if not src_ip:
            print("  [!] No source IP found in alert")
            return

        print(f"  [*] Enriching attacker IP: {src_ip}")
        ip_intel = enrich_ip(src_ip)

        self.threat_intel = {
            "virustotal" : ip_intel.get('virustotal', {}),
            "abuseipdb"  : ip_intel.get('abuseipdb', {}),
            "alienvault" : ip_intel.get('alienvault', {})
        }

        # Print threat intel summary
        vt    = self.threat_intel['virustotal']
        aipdb = self.threat_intel['abuseipdb']
        otx   = self.threat_intel['alienvault']

        print(f"\n  [*] Threat Intel Results:")
        print(f"      VT       : {vt.get('summary', vt.get('error', 'No data'))}")
        print(f"      AbuseIPDB: {aipdb.get('summary', aipdb.get('error', 'No data'))}")
        print(f"      OTX      : {otx.get('summary', otx.get('error', 'No data'))}")

        # Calculate initial detection score
        self._calculate_detection_score()

    def _calculate_detection_score(self):
        """
        Calculate detection score based on
        MITRE ATT&CK T1110 indicators
        """
        details  = self.alert.get('details', {})
        score    = 0
        reasons  = []

        # Get values from alert details
        # Works for both dataset alerts and simulation alerts
        failed_attempts = (
            details.get('failed_attempts') or
            details.get('flow_pkts_s', 0)
        )
        usernames_tried = details.get('usernames_tried', [])
        attack_label    = details.get('attack_label', '')

        try:
            failed_attempts = float(failed_attempts)
        except:
            failed_attempts = 0

        # HIGH CONFIDENCE (40pts) — MITRE T1110
        if failed_attempts > 10 or attack_label:
            score += 40
            reasons.append(
                f"[HIGH] High frequency attack detected (T1110 Brute Force)"
            )

        # HIGH CONFIDENCE (35pts) — MITRE T1110.004
        if len(usernames_tried) > 3:
            score += 35
            reasons.append(
                f"[HIGH] {len(usernames_tried)} usernames tried (T1110.004 Credential Stuffing)"
            )

        # MEDIUM CONFIDENCE (15pts)
        privileged = ['admin', 'root', 'administrator']
        if any(u in usernames_tried for u in privileged):
            score += 15
            reasons.append(
                "[MEDIUM] Privileged accounts targeted"
            )

        # LOW CONFIDENCE (10pts)
        dst_port = details.get('dst_port', details.get('target_port', 0))
        try:
            dst_port = int(dst_port)
        except:
            dst_port = 0

        if dst_port in [22, 3389, 21, 23]:
            score += 10
            reasons.append(
                f"[LOW] Attack targeting sensitive port {dst_port}"
            )

        self.risk_score = score

        print(f"\n  [*] Detection Score: {score}/100")
        print(f"  [*] Reasons:")
        for r in reasons:
            print(f"      -> {r}")

    # ─────────────────────────────────────────────
    # PHASE 3 — RESPOND
    # ─────────────────────────────────────────────
    def respond(self):
        """
        Automated response based on severity
        NIST Phase: Containment, Eradication & Recovery
        """
        details = self.alert.get('details', {})
        src_ip  = (
            details.get('src_ip') or
            details.get('attacker_ip', 'Unknown')
        )

        if self.severity == "CRITICAL":
            self.add_response_action(f"BLOCK IP {src_ip} on firewall immediately")
            self.add_response_action("Lock all targeted user accounts")
            self.add_response_action("Alert SOC team - immediate investigation required")
            self.add_response_action("Capture network traffic for forensic analysis")
            self.add_response_action("Escalate to Incident Response team")

        elif self.severity == "HIGH":
            self.add_response_action(f"BLOCK IP {src_ip} on firewall")
            self.add_response_action("Lock targeted user accounts temporarily")
            self.add_response_action("Alert SOC team for investigation")
            self.add_response_action("Enable enhanced logging on target system")

        elif self.severity == "MEDIUM":
            self.add_response_action(f"FLAG IP {src_ip} for monitoring")
            self.add_response_action("Send alert to security team")
            self.add_response_action("Enable rate limiting on login endpoint")

        else:
            self.add_response_action(f"LOG IP {src_ip} for future reference")
            self.add_response_action("Continue monitoring")


# ─────────────────────────────────────────────
# TEST
# ─────────────────────────────────────────────
if __name__ == "__main__":

    # Test with simulated alert
    print("\n[TEST 1] Testing with Simulated Alert")

    from app.soar.option2_simulation.simulate_bruteforce import simulate
    logs, sim_alerts = simulate(num_attempts=20)

    if sim_alerts:
        playbook = BruteForcePlaybook()
        report   = playbook.run(sim_alerts[0])
        print(f"\n  Report Preview:")
        print(f"  Incident ID : {report['incident_id']}")
        print(f"  Severity    : {report['severity']}")
        print(f"  Risk Score  : {report['risk_score']}")
        print(f"  Responses   : {len(report['response_taken'])} actions taken")

    # Test with dataset alert
    print("\n[TEST 2] Testing with Dataset Alert")

    from app.soar.utils.log_parser import parse_brute_force
    base = os.getenv("SOAR_DATASET_DIR", os.path.expanduser("~/Desktop/soar_platform/option1_datasets"))
    filepath = f"{base}/brute_force/ddos_balanced/final_dataset.csv"
    alerts   = parse_brute_force(filepath)

    if alerts:
        playbook = BruteForcePlaybook()
        report   = playbook.run(alerts[0])
        print(f"\n  Report Preview:")
        print(f"  Incident ID : {report['incident_id']}")
        print(f"  Severity    : {report['severity']}")
        print(f"  Risk Score  : {report['risk_score']}")
        print(f"  Responses   : {len(report['response_taken'])} actions taken")