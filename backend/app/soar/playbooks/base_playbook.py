# Base Playbook class — Parent of all playbooks
# All 4 playbooks inherit from this class
# Follows NIST SP 800-61 incident response lifecycle

import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class BasePlaybook:
    """
    Parent class for all SOAR playbooks.
    Every playbook inherits these common methods.
    Follows NIST SP 800-61 4 phase lifecycle:
    1. Preparation
    2. Detection & Analysis
    3. Containment, Eradication & Recovery
    4. Post-Incident Activity
    """

    def __init__(self, name, mitre_technique):
        self.name            = name
        self.mitre_technique = mitre_technique
        self.incident_id     = self._generate_incident_id()
        self.start_time      = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.alert           = None
        self.threat_intel    = {}
        self.risk_score      = 0
        self.severity        = "LOW"
        self.response_taken  = []
        self.status          = "OPEN"

    # ─────────────────────────────────────────────
    # PHASE 1 — PREPARATION
    # ─────────────────────────────────────────────
    def _generate_incident_id(self):
        """Generate unique incident ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"INC-{timestamp}"

    def receive_alert(self, alert):
        """
        Receive and validate incoming alert
        NIST Phase: Detection & Analysis
        """
        self.alert = alert
        print(f"\n{'='*60}")
        print(f"  [ALERT] PLAYBOOK TRIGGERED: {self.name}")
        print(f"{'='*60}")
        print(f"  Incident ID  : {self.incident_id}")
        print(f"  Alert Type   : {alert.get('alert_type', 'Unknown')}")
        print(f"  Source       : {alert.get('source', 'Unknown')}")
        print(f"  Timestamp    : {alert.get('timestamp', 'Unknown')}")
        print(f"  MITRE TTP    : {self.mitre_technique}")
        print(f"{'='*60}")

    # ─────────────────────────────────────────────
    # PHASE 2 — DETECTION & ANALYSIS
    # ─────────────────────────────────────────────
    def enrich(self):
        """
        Gather threat intelligence
        Override in child playbook
        NIST Phase: Detection & Analysis
        """
        raise NotImplementedError(
            "Each playbook must implement its own enrich() method"
        )

    def calculate_risk_score(self):
        """
        Calculate final risk score combining:
        - Playbook detection score
        - Threat intel results
        NIST Phase: Detection & Analysis
        """
        # Bonus score from threat intel results
        bonus = 0

        # VirusTotal bonus
        vt = self.threat_intel.get('virustotal', {})
        if vt.get('malicious', 0) > 10:
            bonus += 15
        elif vt.get('malicious', 0) > 5:
            bonus += 10
        elif vt.get('malicious', 0) > 0:
            bonus += 5

        # AbuseIPDB bonus
        aipdb = self.threat_intel.get('abuseipdb', {})
        if aipdb.get('abuse_score', 0) > 80:
            bonus += 15
        elif aipdb.get('abuse_score', 0) > 50:
            bonus += 10
        elif aipdb.get('abuse_score', 0) > 20:
            bonus += 5

        # AlienVault bonus
        otx = self.threat_intel.get('alienvault', {})
        if otx.get('pulse_count', 0) > 10:
            bonus += 10
        elif otx.get('pulse_count', 0) > 0:
            bonus += 5

        # Cap bonus at 30
        bonus = min(bonus, 30)

        # Final score = detection score + threat intel bonus
        # Capped at 100
        self.risk_score = min(self.risk_score + bonus, 100)
        return self.risk_score

    def classify_severity(self):
        """
        Classify severity based on risk score
        Based on NIST SP 800-61 severity levels
        """
        if self.risk_score >= 75:
            self.severity = "CRITICAL"
        elif self.risk_score >= 50:
            self.severity = "HIGH"
        elif self.risk_score >= 25:
            self.severity = "MEDIUM"
        else:
            self.severity = "LOW"

        print(f"\n  [*] Risk Score : {self.risk_score}/100")
        print(f"  [*] Severity   : {self.severity}")
        return self.severity

    # ─────────────────────────────────────────────
    # PHASE 3 — CONTAINMENT & RESPONSE
    # ─────────────────────────────────────────────
    def respond(self):
        """
        Take automated response actions
        Override in child playbook
        NIST Phase: Containment, Eradication & Recovery
        """
        raise NotImplementedError(
            "Each playbook must implement its own respond() method"
        )

    def add_response_action(self, action):
        """Log a response action taken"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.response_taken.append({
            "action"    : action,
            "timestamp" : timestamp,
            "status"    : "COMPLETED"
        })
        print(f"  [OK] Response  : {action}")

    # ─────────────────────────────────────────────
    # PHASE 4 — POST INCIDENT
    # ─────────────────────────────────────────────
    def generate_report(self):
        """
        Generate structured incident report
        NIST Phase: Post-Incident Activity
        """
        self.status = "CLOSED"
        report = {
            "incident_id"    : self.incident_id,
            "playbook_name"  : self.name,
            "mitre_technique": self.mitre_technique,
            "alert_type"     : self.alert.get('alert_type', 'Unknown'),
            "severity"       : self.severity,
            "risk_score"     : self.risk_score,
            "status"         : self.status,
            "start_time"     : self.start_time,
            "end_time"       : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "alert_details"  : self.alert.get('details', {}),
            "threat_intel"   : self.threat_intel,
            "response_taken" : self.response_taken,
            "source"         : self.alert.get('source', 'Unknown')
        }

        # Save report as JSON
        report_dir = os.getenv("SOAR_REPORTS_DIR", os.path.join(os.getcwd(), "reports"))
        os.makedirs(report_dir, exist_ok=True)
        report_path = f"{report_dir}/{self.incident_id}.json"

        with open(report_path, 'w') as f:
            json.dump(report, f, indent=4)

        print(f"\n  [*] Report saved: {report_path}")
        return report

    # ─────────────────────────────────────────────
    # MAIN RUN METHOD
    # ─────────────────────────────────────────────
    def run(self, alert):
        """
        Main method — runs complete playbook lifecycle
        Follows NIST SP 800-61 4 phase process
        """
        # Phase 1 — Receive alert
        self.receive_alert(alert)

        # Phase 2 — Enrich + Score + Classify
        print(f"\n  [*] Phase 2: Detection & Analysis")
        print(f"  {'-'*40}")
        self.enrich()
        self.calculate_risk_score()
        self.classify_severity()

        # Phase 3 — Respond
        print(f"\n  [*] Phase 3: Containment & Response")
        print(f"  {'-'*40}")
        self.respond()

        # Phase 4 — Report
        print(f"\n  [*] Phase 4: Post-Incident Activity")
        print(f"  {'-'*40}")
        report = self.generate_report()

        print(f"\n{'='*60}")
        print(f"  [DONE] INCIDENT {self.incident_id} CLOSED")
        print(f"{'='*60}\n")

        return report