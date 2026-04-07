# playbooks/network_anomaly_playbook.py
# Network Anomaly Detection Playbook
# MITRE ATT&CK: T1071 - C2, T1030 - Data Exfiltration
# NIST SP 800-61 compliant

import os

from app.soar.playbooks.base_playbook import BasePlaybook
from app.soar.utils.threat_intel import enrich_ip

class NetworkAnomalyPlaybook(BasePlaybook):

    def __init__(self):
        super().__init__(
            name            = "Network Anomaly Detection Playbook",
            mitre_technique = "T1071/T1030 - C2 Communication/Data Exfiltration"
        )

    # ─────────────────────────────────────────────
    # PHASE 2 — ENRICH
    # ─────────────────────────────────────────────
    def enrich(self):
        """
        Enrich alert with threat intelligence
        Queries: VirusTotal, AbuseIPDB, AlienVault OTX
        """
        details = self.alert.get('details', {})
        src_ip  = details.get('src_ip', '')

        if not src_ip:
            print("  [!] No source IP found in alert")
            return

        print(f"  [*] Enriching source IP: {src_ip}")
        ip_intel = enrich_ip(src_ip)

        self.threat_intel = {
            "virustotal" : ip_intel.get('virustotal', {}),
            "abuseipdb"  : ip_intel.get('abuseipdb', {}),
            "alienvault" : ip_intel.get('alienvault', {})
        }

        vt    = self.threat_intel['virustotal']
        aipdb = self.threat_intel['abuseipdb']
        otx   = self.threat_intel['alienvault']

        print(f"\n  [*] Threat Intel Results:")
        print(f"      VT       : {vt.get('summary', vt.get('error', 'No data'))}")
        print(f"      AbuseIPDB: {aipdb.get('summary', aipdb.get('error', 'No data'))}")
        print(f"      OTX      : {otx.get('summary', otx.get('error', 'No data'))}")

        self._calculate_detection_score()

    def _calculate_detection_score(self):
        """
        Calculate detection score based on
        MITRE ATT&CK T1071 and T1030 indicators
        """
        details    = self.alert.get('details', {})
        score      = 0
        reasons    = []

        # Get values
        protocol   = details.get('protocol', '')
        attack_cat = details.get('attack_cat', '')
        src_bytes  = int(details.get('src_bytes', 0))
        dst_bytes  = int(details.get('dst_bytes', 0))
        src_pkts   = int(details.get('src_packets', 0))
        risk_score = details.get('risk_score', 0)

        # If alert already has risk score from simulator
        if risk_score:
            score   = risk_score
            reasons = details.get('reasons', [])
            self.risk_score = score
            print(f"\n  [*] Detection Score: {score}/100")
            print(f"  [*] Reasons:")
            for r in reasons:
                print(f"      -> {r}")
            return

        # MITRE ATT&CK attack category mapping
        ATTACK_MITRE = {
            "Reconnaissance" : "T1595",
            "Exploits"       : "T1203",
            "DoS"            : "T1499",
            "Backdoor"       : "T1071",
            "Shellcode"      : "T1059",
            "Worms"          : "T1210",
            "Fuzzers"        : "T1190",
        }

        # HIGH CONFIDENCE (40pts) — Direct ATT&CK TTP match
        critical_attacks = ["Backdoor", "Shellcode", "Worms"]
        high_attacks     = ["Exploits", "DoS"]

        if attack_cat in critical_attacks:
            mitre_id = ATTACK_MITRE.get(attack_cat, "T1071")
            score   += 40
            reasons.append(
                f"[HIGH] {attack_cat} detected - Direct TTP match ({mitre_id})"
            )
        elif attack_cat in high_attacks:
            mitre_id = ATTACK_MITRE.get(attack_cat, "T1071")
            score   += 30
            reasons.append(
                f"[HIGH] {attack_cat} detected - Direct TTP match ({mitre_id})"
            )
        elif attack_cat:
            score   += 20
            reasons.append(
                f"[HIGH] Attack category detected: {attack_cat}"
            )

        # HIGH CONFIDENCE (35pts) — MITRE T1071
        # Unusual protocol = possible C2 communication
        unusual_protocols = ["ospf", "arp", "icmp"]
        if protocol.lower() in unusual_protocols:
            score += 35
            reasons.append(
                f"[HIGH] Unusual protocol '{protocol}' - possible C2 (T1071)"
            )

        # MEDIUM CONFIDENCE (15pts) — MITRE T1030
        # Abnormal byte ratio = possible data exfiltration
        if dst_bytes > 0 and src_bytes / dst_bytes > 100:
            score += 15
            reasons.append(
                f"[MEDIUM] Abnormal byte ratio - possible exfiltration (T1030)"
            )
        elif dst_bytes == 0 and src_bytes > 10000:
            score += 15
            reasons.append(
                f"[MEDIUM] One-way large transfer - possible exfiltration (T1030)"
            )

        # LOW CONFIDENCE (10pts)
        if src_pkts > 1000:
            score += 10
            reasons.append(
                f"[LOW] High packet rate: {src_pkts} packets"
            )

        self.risk_score = min(score, 100)

        print(f"\n  [*] Detection Score: {self.risk_score}/100")
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
        details    = self.alert.get('details', {})
        src_ip     = details.get('src_ip', 'Unknown')
        attack_cat = details.get('attack_cat', 'Unknown')

        if self.severity == "CRITICAL":
            self.add_response_action(
                f"BLOCK source IP immediately: {src_ip}"
            )
            self.add_response_action(
                f"ISOLATE affected network segment"
            )
            self.add_response_action(
                f"Alert SOC team - {attack_cat} attack detected"
            )
            self.add_response_action(
                "Capture full packet dump for forensics"
            )
            self.add_response_action(
                "Block suspicious traffic on firewall"
            )
            self.add_response_action(
                "Escalate to Incident Response team"
            )

        elif self.severity == "HIGH":
            self.add_response_action(
                f"BLOCK source IP: {src_ip}"
            )
            self.add_response_action(
                "Alert SOC team for investigation"
            )
            self.add_response_action(
                "Enable enhanced network monitoring"
            )
            self.add_response_action(
                "Review firewall rules"
            )

        elif self.severity == "MEDIUM":
            self.add_response_action(
                f"FLAG source IP for monitoring: {src_ip}"
            )
            self.add_response_action(
                "Send alert to network security team"
            )
            self.add_response_action(
                "Increase logging verbosity on affected segment"
            )

        else:
            self.add_response_action(
                f"LOG suspicious traffic from: {src_ip}"
            )
            self.add_response_action(
                "Continue monitoring network"
            )


# ─────────────────────────────────────────────
# TEST
# ─────────────────────────────────────────────
if __name__ == "__main__":

    # Test with simulated alert
    print("\n[TEST 1] Testing with Simulated Alert")
    from app.soar.option2_simulation.simulate_network_anomaly import simulate
    traffic, sim_alerts = simulate(num_traffic=10)

    if sim_alerts:
        playbook = NetworkAnomalyPlaybook()
        report   = playbook.run(sim_alerts[0])
        print(f"\n  Report Preview:")
        print(f"  Incident ID : {report['incident_id']}")
        print(f"  Severity    : {report['severity']}")
        print(f"  Risk Score  : {report['risk_score']}")
        print(f"  Responses   : {len(report['response_taken'])} actions taken")

    # Test with dataset alert
    print("\n[TEST 2] Testing with Dataset Alert")
    from app.soar.utils.log_parser import parse_network_anomaly
    base = os.getenv("SOAR_DATASET_DIR", os.path.expanduser("~/Desktop/soar_platform/option1_datasets"))
    filepath = f"{base}/network_anomaly/UNSW_NB15_training-set.csv"
    alerts   = parse_network_anomaly(filepath)

    if alerts:
        playbook = NetworkAnomalyPlaybook()
        report   = playbook.run(alerts[0])
        print(f"\n  Report Preview:")
        print(f"  Incident ID : {report['incident_id']}")
        print(f"  Severity    : {report['severity']}")
        print(f"  Risk Score  : {report['risk_score']}")
        print(f"  Responses   : {len(report['response_taken'])} actions taken")
