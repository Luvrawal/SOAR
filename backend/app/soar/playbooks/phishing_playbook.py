# Phishing Detection Playbook
# MITRE ATT&CK: T1566 - Phishing
# NIST SP 800-61 compliant

import os

from app.soar.playbooks.base_playbook import BasePlaybook
from app.soar.utils.threat_intel import enrich_url, enrich_ip

class PhishingPlaybook(BasePlaybook):

    def __init__(self):
        super().__init__(
            name            = "Phishing Detection Playbook",
            mitre_technique = "T1566 - Phishing"
        )

    # ─────────────────────────────────────────────
    # PHASE 2 — ENRICH
    # ─────────────────────────────────────────────
    def enrich(self):
        """
        Enrich alert with threat intelligence
        Queries: VirusTotal, AlienVault OTX
        """
        details = self.alert.get('details', {})
        url     = details.get('url', '')
        sender  = details.get('sender', '')

        if not url:
            print("  [!] No URL found in alert")
            return

        print(f"  [*] Enriching URL: {url[:50]}...")
        url_intel = enrich_url(url)

        self.threat_intel = {
            "virustotal" : url_intel.get('virustotal', {}),
            "alienvault" : url_intel.get('alienvault', {})
        }

        vt  = self.threat_intel['virustotal']
        otx = self.threat_intel['alienvault']

        print(f"\n  [*] Threat Intel Results:")
        print(f"      VT  : {vt.get('summary', vt.get('error', 'No data'))}")
        print(f"      OTX : {otx.get('summary', otx.get('error', 'No data'))}")

        self._calculate_detection_score()

    def _calculate_detection_score(self):
        """
        Calculate detection score based on
        MITRE ATT&CK T1566 indicators
        """
        details = self.alert.get('details', {})
        score   = 0
        reasons = []

        url         = details.get('url', '')
        attack_type = details.get('attack_type', '')
        sender      = details.get('sender', '')
        subject     = details.get('subject', '')
        has_https   = details.get('has_https', True)
        risk_score  = details.get('risk_score', 0)

        # If alert already has risk score from simulator use it
        if risk_score:
            score = risk_score
            reasons = details.get('reasons', [])
            self.risk_score = score
            print(f"\n  [*] Detection Score: {score}/100")
            print(f"  [*] Reasons:")
            for r in reasons:
                print(f"      -> {r}")
            return

        # HIGH CONFIDENCE (40pts) — MITRE T1566.002
        suspicious_tlds = ['.tk', '.ml', '.cf', '.ga', '.gq', '.br']
        if any(url.endswith(tld) or tld in url for tld in suspicious_tlds):
            score += 40
            reasons.append(
                "[HIGH] Suspicious TLD linked to phishing infrastructure (T1566.002)"
            )

        # HIGH CONFIDENCE (35pts) — MITRE T1566.002
        if attack_type in ['phishing', 'malware', 'defacement']:
            score += 35
            reasons.append(
                f"[HIGH] URL classified as {attack_type} (T1566.002)"
            )

        # MEDIUM CONFIDENCE (20pts) — MITRE T1566
        urgent_keywords = ['urgent', 'verify', 'suspended',
                          'expire', 'compromised', 'action']
        if subject and any(kw in subject.lower() for kw in urgent_keywords):
            score += 20
            reasons.append(
                "[MEDIUM] Urgent/threatening language in subject (T1566)"
            )

        # LOW CONFIDENCE (5pts)
        if not has_https:
            score += 5
            reasons.append("[LOW] URL uses insecure HTTP protocol")

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
        details = self.alert.get('details', {})
        url     = details.get('url', 'Unknown')
        sender  = details.get('sender', 'Unknown')

        if self.severity == "CRITICAL":
            self.add_response_action(f"BLOCK domain: {url[:50]}")
            self.add_response_action(f"QUARANTINE all emails from: {sender}")
            self.add_response_action("Alert all users about phishing campaign")
            self.add_response_action("Block URL on web proxy and firewall")
            self.add_response_action("Escalate to SOC team immediately")
            self.add_response_action("Preserve email headers for forensics")

        elif self.severity == "HIGH":
            self.add_response_action(f"BLOCK domain: {url[:50]}")
            self.add_response_action(f"QUARANTINE emails from: {sender}")
            self.add_response_action("Notify affected users")
            self.add_response_action("Block URL on web proxy")

        elif self.severity == "MEDIUM":
            self.add_response_action(f"FLAG URL for review: {url[:50]}")
            self.add_response_action("Send warning to recipient")
            self.add_response_action("Monitor for further phishing attempts")

        else:
            self.add_response_action(f"LOG suspicious URL: {url[:50]}")
            self.add_response_action("Continue monitoring")


# ─────────────────────────────────────────────
# TEST
# ─────────────────────────────────────────────
if __name__ == "__main__":

    # Test with simulated alert
    print("\n[TEST 1] Testing with Simulated Alert")
    from app.soar.option2_simulation.simulate_phishing import simulate
    emails, sim_alerts = simulate(num_emails=10)

    if sim_alerts:
        playbook = PhishingPlaybook()
        report   = playbook.run(sim_alerts[0])
        print(f"\n  Report Preview:")
        print(f"  Incident ID : {report['incident_id']}")
        print(f"  Severity    : {report['severity']}")
        print(f"  Risk Score  : {report['risk_score']}")
        print(f"  Responses   : {len(report['response_taken'])} actions taken")

    # Test with dataset alert
    print("\n[TEST 2] Testing with Dataset Alert")
    from app.soar.utils.log_parser import parse_phishing
    base = os.getenv("SOAR_DATASET_DIR", os.path.expanduser("~/Desktop/soar_platform/option1_datasets"))
    filepath = f"{base}/phishing/malicious_phish.csv"
    alerts   = parse_phishing(filepath)

    if alerts:
        playbook = PhishingPlaybook()
        report   = playbook.run(alerts[0])
        print(f"\n  Report Preview:")
        print(f"  Incident ID : {report['incident_id']}")
        print(f"  Severity    : {report['severity']}")
        print(f"  Risk Score  : {report['risk_score']}")
        print(f"  Responses   : {len(report['response_taken'])} actions taken")