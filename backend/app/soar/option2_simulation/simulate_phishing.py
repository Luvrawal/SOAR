# Simulates Phishing Email Attack logs

import random
import time
from datetime import datetime

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

# Simulated malicious domains
MALICIOUS_DOMAINS = [
    "br-icloud.com.br",
    "secure-paypal-login.tk",
    "amazon-account-verify.ml",
    "google-security-alert.cf",
    "microsoft-update-center.ga",
    "apple-id-locked.gq",
    "netflix-billing-update.tk",
]

# Simulated legitimate domains
LEGIT_DOMAINS = [
    "google.com",
    "microsoft.com",
    "github.com",
    "stackoverflow.com",
    "amazon.com"
]

# Simulated sender emails
MALICIOUS_SENDERS = [
    "security@br-icloud.com.br",
    "noreply@secure-paypal-login.tk",
    "support@amazon-account-verify.ml",
    "alert@google-security-alert.cf",
]

# Simulated targets
TARGETS = [
    "employee1@company.com",
    "employee2@company.com",
    "admin@company.com",
    "hr@company.com"
]

# Phishing keywords in subject
PHISHING_SUBJECTS = [
    "Urgent: Your account has been compromised",
    "Action Required: Verify your identity",
    "Your password will expire in 24 hours",
    "Suspicious login detected - verify now",
    "Your account is suspended - click here",
]

LEGIT_SUBJECTS = [
    "Team meeting tomorrow at 10am",
    "Q4 report attached",
    "Welcome to the newsletter",
    "Your order has been shipped",
]


# ─────────────────────────────────────────────
# LOG GENERATOR
# ─────────────────────────────────────────────
def generate_phishing_email():
    sender = random.choice(MALICIOUS_SENDERS)
    domain = sender.split('@')[1]
    url    = f"http://{random.choice(MALICIOUS_DOMAINS)}/login?redirect=verify"
    return {
        "timestamp"    : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "event_type"   : "EMAIL_RECEIVED",
        "sender"       : sender,
        "sender_domain": domain,
        "recipient"    : random.choice(TARGETS),
        "subject"      : random.choice(PHISHING_SUBJECTS),
        "url"          : url,
        "has_attachment": random.choice([True, False]),
        "is_phishing"  : True
    }

def generate_legit_email():
    domain = random.choice(LEGIT_DOMAINS)
    return {
        "timestamp"    : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "event_type"   : "EMAIL_RECEIVED",
        "sender"       : f"noreply@{domain}",
        "sender_domain": domain,
        "recipient"    : random.choice(TARGETS),
        "subject"      : random.choice(LEGIT_SUBJECTS),
        "url"          : f"https://{domain}",
        "has_attachment": False,
        "is_phishing"  : False
    }


# ─────────────────────────────────────────────
# PHISHING DETECTOR
# ─────────────────────────────────────────────
def analyze_email(email):
    score   = 0
    reasons = []

    # HIGH CONFIDENCE (40pts) — MITRE T1566.002
    # Suspicious TLD directly tied to phishing infrastructure
    suspicious_tlds = ['.tk', '.ml', '.cf', '.ga', '.gq', '.br']
    if any(email['sender_domain'].endswith(tld) for tld in suspicious_tlds):
        score += 40
        reasons.append("[HIGH] Suspicious TLD linked to phishing infrastructure (T1566.002)")

    # HIGH CONFIDENCE (35pts) — MITRE T1566.002
    # URL domain mismatch — core phishing technique
    url_domain = email['url'].split('/')[2] if '/' in email['url'] else ''
    if url_domain and email['sender_domain'] not in url_domain:
        score += 35
        reasons.append("[HIGH] URL domain mismatch with sender domain (T1566.002)")

    # MEDIUM CONFIDENCE (20pts) — MITRE T1566
    # Urgent/threatening language — social engineering indicator
    urgent_keywords = ['urgent', 'verify', 'suspended', 'expire',
                       'compromised', 'action required', 'locked']
    if any(kw in email['subject'].lower() for kw in urgent_keywords):
        score += 20
        reasons.append("[MEDIUM] Urgent/threatening language detected (T1566 Social Engineering)")

    # LOW CONFIDENCE (5pts)
    # HTTP instead of HTTPS — weak signal alone
    if not email['url'].startswith('https'):
        score += 5
        reasons.append("[LOW] URL uses insecure HTTP protocol")

    # Determine severity based on MITRE ATT&CK confidence thresholds
    if score >= 75:
        severity = "CRITICAL"
    elif score >= 50:
        severity = "HIGH"
    elif score >= 25:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    return score, severity, reasons


def detect_phishing(emails):
    alerts = []
    for email in emails:
        score, severity, reasons = analyze_email(email)
        if score >= 30:
            alerts.append({
                "alert_type" : "PHISHING_EMAIL_DETECTED",
                "severity"   : severity,
                "timestamp"  : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "source"     : "option2_simulation",
                "details"    : {
                    "sender"        : email['sender'],
                    "recipient"     : email['recipient'],
                    "subject"       : email['subject'],
                    "url"           : email['url'],
                    "risk_score"    : score,
                    "reasons"       : reasons,
                    "has_attachment": email['has_attachment']
                }
            })
    return alerts


# ─────────────────────────────────────────────
# MAIN SIMULATION
# ─────────────────────────────────────────────
def simulate(num_emails=10):
    print("\n" + "="*60)
    print("   PHISHING EMAIL ATTACK SIMULATION")
    print("="*60)
    print(f"[*] Simulating {num_emails} incoming emails...")
    print("="*60 + "\n")

    emails = []

    for i in range(num_emails):
        # 60% chance phishing, 40% legit
        if random.random() < 0.6:
            email = generate_phishing_email()
            tag = "[SUSPECT] PHISHING"
        else:
            email = generate_legit_email()
            tag = "[OK] LEGIT   "

        print(f"[Email {i+1:02d}] {tag} | From: {email['sender'][:35]:<35} | Subject: {email['subject'][:30]}")
        emails.append(email)
        time.sleep(0.1)

    print("\n" + "="*60)
    print("[*] Analyzing emails for phishing patterns...")
    print("="*60)

    alerts = detect_phishing(emails)

    if alerts:
        print(f"\n[ALERT] {len(alerts)} PHISHING ALERT(S) TRIGGERED!\n")
        for alert in alerts:
            print(f"   Sender    : {alert['details']['sender']}")
            print(f"   Recipient : {alert['details']['recipient']}")
            print(f"   Risk Score: {alert['details']['risk_score']}/100")
            print(f"   Severity  : {alert['severity']}")
            print(f"   Reasons   : {', '.join(alert['details']['reasons'])}")
            print(f"   URL       : {alert['details']['url']}")
            print()
    else:
        print("\n[*] No phishing detected.")

    return emails, alerts


if __name__ == "__main__":
    emails, alerts = simulate(num_emails=10)