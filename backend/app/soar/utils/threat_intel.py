# Threat Intelligence module
# Integrates: VirusTotal, AbuseIPDB, AlienVault OTX, MalwareBazaar
# Follows Open/Closed Principle — add new tools by adding new functions only

import requests
import os
import time
import logging
from requests import Response
from dotenv import load_dotenv
from app.core.config import settings

logger = logging.getLogger(__name__)

# Load API keys from .env file
load_dotenv()

VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY")
ABUSEIPDB_API_KEY  = os.getenv("ABUSEIPDB_API_KEY")
ALIENVAULT_API_KEY = os.getenv("ALIENVAULT_API_KEY")
MALWAREBAZAAR_API_KEY = os.getenv("MALWAREBAZAAR_API_KEY")


def _missing_key_result(source: str, key_name: str) -> dict:
    return {
        "source": source,
        "error": f"{key_name}_not_configured",
        "degraded": True,
    }


def _error_result(source: str, message: str, transient: bool = False) -> dict:
    return {
        "source": source,
        "error": message,
        "degraded": True,
        "transient": transient,
    }


def _request_with_retries(
    method: str,
    url: str,
    source: str,
    headers: dict | None = None,
    params: dict | None = None,
    data: dict | None = None,
) -> Response:
    timeout = max(1, int(settings.THREAT_INTEL_TIMEOUT_SECONDS))
    max_retries = max(0, int(settings.THREAT_INTEL_MAX_RETRIES))
    backoff = max(0.0, float(settings.THREAT_INTEL_RETRY_BACKOFF_SECONDS))

    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            return requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                data=data,
                timeout=timeout,
            )
        except requests.RequestException as exc:
            last_error = exc
            logger.warning(
                "Threat intel request failed",
                extra={"source": source, "attempt": attempt + 1, "max_retries": max_retries, "error": str(exc)},
            )
            if attempt < max_retries and backoff > 0:
                time.sleep(backoff * (attempt + 1))

    raise last_error if last_error is not None else RuntimeError("request_failed")

# ─────────────────────────────────────────────
# VIRUSTOTAL FUNCTIONS
# ─────────────────────────────────────────────

def query_virustotal_ip(ip):
    """Check IP reputation on VirusTotal"""
    print(f"   [VT] Querying IP: {ip}")
    if not VIRUSTOTAL_API_KEY:
        return _missing_key_result("VirusTotal", "VIRUSTOTAL_API_KEY")
    try:
        url      = f"https://www.virustotal.com/api/v3/ip_addresses/{ip}"
        headers  = {"x-apikey": VIRUSTOTAL_API_KEY}
        response = _request_with_retries("GET", url, "VirusTotal", headers=headers)

        if response.status_code == 200:
            data       = response.json()
            stats      = data['data']['attributes']['last_analysis_stats']
            malicious  = stats.get('malicious', 0)
            suspicious = stats.get('suspicious', 0)
            total      = sum(stats.values())
            return {
                "source"     : "VirusTotal",
                "ip"         : ip,
                "malicious"  : malicious,
                "suspicious" : suspicious,
                "total"      : total,
                "summary"    : f"{malicious}/{total} engines flagged as malicious"
            }
        else:
            return _error_result("VirusTotal", f"status_{response.status_code}")

    except Exception as e:
        return _error_result("VirusTotal", str(e), transient=True)


def query_virustotal_url(url_to_check):
    """Check URL reputation on VirusTotal"""
    print(f"   [VT] Querying URL: {url_to_check[:50]}...")
    if not VIRUSTOTAL_API_KEY:
        return _missing_key_result("VirusTotal", "VIRUSTOTAL_API_KEY")
    try:
        import base64
        # VirusTotal requires URL to be base64 encoded
        url_id   = base64.urlsafe_b64encode(
            url_to_check.encode()
        ).decode().strip("=")
        url      = f"https://www.virustotal.com/api/v3/urls/{url_id}"
        headers  = {"x-apikey": VIRUSTOTAL_API_KEY}
        response = _request_with_retries("GET", url, "VirusTotal", headers=headers)

        if response.status_code == 200:
            data       = response.json()
            stats      = data['data']['attributes']['last_analysis_stats']
            malicious  = stats.get('malicious', 0)
            suspicious = stats.get('suspicious', 0)
            total      = sum(stats.values())
            return {
                "source"     : "VirusTotal",
                "url"        : url_to_check,
                "malicious"  : malicious,
                "suspicious" : suspicious,
                "total"      : total,
                "summary"    : f"{malicious}/{total} engines flagged as malicious"
            }
        else:
            return _error_result("VirusTotal", f"status_{response.status_code}")

    except Exception as e:
        return _error_result("VirusTotal", str(e), transient=True)


def query_virustotal_hash(file_hash):
    """Check file hash reputation on VirusTotal"""
    print(f"   [VT] Querying Hash: {file_hash[:20]}...")
    if not VIRUSTOTAL_API_KEY:
        return _missing_key_result("VirusTotal", "VIRUSTOTAL_API_KEY")
    try:
        url      = f"https://www.virustotal.com/api/v3/files/{file_hash}"
        headers  = {"x-apikey": VIRUSTOTAL_API_KEY}
        response = _request_with_retries("GET", url, "VirusTotal", headers=headers)

        if response.status_code == 200:
            data       = response.json()
            stats      = data['data']['attributes']['last_analysis_stats']
            malicious  = stats.get('malicious', 0)
            suspicious = stats.get('suspicious', 0)
            total      = sum(stats.values())
            return {
                "source"     : "VirusTotal",
                "hash"       : file_hash,
                "malicious"  : malicious,
                "suspicious" : suspicious,
                "total"      : total,
                "summary"    : f"{malicious}/{total} engines flagged as malicious"
            }
        elif response.status_code == 404:
            return {
                "source"  : "VirusTotal",
                "hash"    : file_hash,
                "summary" : "Hash not found in VirusTotal database"
            }
        else:
            return _error_result("VirusTotal", f"status_{response.status_code}")

    except Exception as e:
        return _error_result("VirusTotal", str(e), transient=True)


# ─────────────────────────────────────────────
# ABUSEIPDB FUNCTIONS
# ─────────────────────────────────────────────

def query_abuseipdb(ip):
    """Check IP abuse confidence score on AbuseIPDB"""
    print(f"   [AIPDB] Querying IP: {ip}")
    if not ABUSEIPDB_API_KEY:
        return _missing_key_result("AbuseIPDB", "ABUSEIPDB_API_KEY")
    try:
        url      = "https://api.abuseipdb.com/api/v2/check"
        headers  = {
            "Key"   : ABUSEIPDB_API_KEY,
            "Accept": "application/json"
        }
        params   = {
            "ipAddress"    : ip,
            "maxAgeInDays" : 90  # Check reports from last 90 days
        }
        response = _request_with_retries("GET", url, "AbuseIPDB", headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()['data']
            return {
                "source"            : "AbuseIPDB",
                "ip"                : ip,
                "abuse_score"       : data.get('abuseConfidenceScore', 0),
                "total_reports"     : data.get('totalReports', 0),
                "country"           : data.get('countryCode', 'Unknown'),
                "isp"               : data.get('isp', 'Unknown'),
                "is_whitelisted"    : data.get('isWhitelisted', False),
                "summary"           : f"Abuse confidence: {data.get('abuseConfidenceScore', 0)}% ({data.get('totalReports', 0)} reports)"
            }
        else:
            return _error_result("AbuseIPDB", f"status_{response.status_code}")

    except Exception as e:
        return _error_result("AbuseIPDB", str(e), transient=True)


# ─────────────────────────────────────────────
# ALIENVAULT OTX FUNCTIONS
# ─────────────────────────────────────────────

def query_alienvault_ip(ip):
    """Check IP reputation on AlienVault OTX"""
    print(f"   [OTX] Querying IP: {ip}")
    if not ALIENVAULT_API_KEY:
        return _missing_key_result("AlienVault OTX", "ALIENVAULT_API_KEY")
    try:
        url      = f"https://otx.alienvault.com/api/v1/indicators/IPv4/{ip}/general"
        headers  = {"X-OTX-API-KEY": ALIENVAULT_API_KEY}
        response = _request_with_retries("GET", url, "AlienVault OTX", headers=headers)

        if response.status_code == 200:
            data        = response.json()
            pulse_count = data.get('pulse_info', {}).get('count', 0)
            return {
                "source"      : "AlienVault OTX",
                "ip"          : ip,
                "pulse_count" : pulse_count,
                "reputation"  : data.get('reputation', 0),
                "summary"     : f"Found in {pulse_count} threat intelligence pulses"
            }
        else:
            return _error_result("AlienVault OTX", f"status_{response.status_code}")

    except Exception as e:
        return _error_result("AlienVault OTX", str(e), transient=True)


def query_alienvault_url(url_to_check):
    """Check URL reputation on AlienVault OTX"""
    print(f"   [OTX] Querying URL: {url_to_check[:50]}...")
    if not ALIENVAULT_API_KEY:
        return _missing_key_result("AlienVault OTX", "ALIENVAULT_API_KEY")
    try:
        url      = f"https://otx.alienvault.com/api/v1/indicators/url/{url_to_check}/general"
        headers  = {"X-OTX-API-KEY": ALIENVAULT_API_KEY}
        response = _request_with_retries("GET", url, "AlienVault OTX", headers=headers)

        if response.status_code == 200:
            data        = response.json()
            pulse_count = data.get('pulse_info', {}).get('count', 0)
            return {
                "source"      : "AlienVault OTX",
                "url"         : url_to_check,
                "pulse_count" : pulse_count,
                "summary"     : f"Found in {pulse_count} threat intelligence pulses"
            }
        else:
            return _error_result("AlienVault OTX", f"status_{response.status_code}")

    except Exception as e:
        return _error_result("AlienVault OTX", str(e), transient=True)


def query_alienvault_hash(file_hash):
    """Check file hash on AlienVault OTX"""
    print(f"   [OTX] Querying Hash: {file_hash[:20]}...")
    if not ALIENVAULT_API_KEY:
        return _missing_key_result("AlienVault OTX", "ALIENVAULT_API_KEY")
    try:
        url      = f"https://otx.alienvault.com/api/v1/indicators/file/{file_hash}/general"
        headers  = {"X-OTX-API-KEY": ALIENVAULT_API_KEY}
        response = _request_with_retries("GET", url, "AlienVault OTX", headers=headers)

        if response.status_code == 200:
            data        = response.json()
            pulse_count = data.get('pulse_info', {}).get('count', 0)
            return {
                "source"      : "AlienVault OTX",
                "hash"        : file_hash,
                "pulse_count" : pulse_count,
                "summary"     : f"Found in {pulse_count} threat intelligence pulses"
            }
        else:
            return _error_result("AlienVault OTX", f"status_{response.status_code}")

    except Exception as e:
        return _error_result("AlienVault OTX", str(e), transient=True)


# ─────────────────────────────────────────────
# MALWAREBAZAAR FUNCTIONS (No API key needed)
# ─────────────────────────────────────────────

def query_malwarebazaar(file_hash):
    """Check file hash against MalwareBazaar database"""
    print(f"   [MB] Querying Hash: {file_hash[:20]}...")
    if not MALWAREBAZAAR_API_KEY:
        return _missing_key_result("MalwareBazaar", "MALWAREBAZAAR_API_KEY")
    try:
        url      = "https://mb-api.abuse.ch/api/v1/"
        data     = {
            "query"     : "get_info",
            "hash"      : file_hash
        }
        headers  = {"Auth-Key": MALWAREBAZAAR_API_KEY}
        response = _request_with_retries("POST", url, "MalwareBazaar", headers=headers, data=data)

        if response.status_code == 200:
            result = response.json()
            if result.get('query_status') == 'ok':
                malware_info = result['data'][0]
                return {
                    "source"       : "MalwareBazaar",
                    "hash"         : file_hash,
                    "found"        : True,
                    "malware_name" : malware_info.get('signature', 'Unknown'),
                    "file_type"    : malware_info.get('file_type', 'Unknown'),
                    "tags"         : malware_info.get('tags', []),
                    "summary"      : f"KNOWN MALWARE: {malware_info.get('signature', 'Unknown')}"
                }
            else:
                return {
                    "source"  : "MalwareBazaar",
                    "hash"    : file_hash,
                    "found"   : False,
                    "summary" : "Hash not found in MalwareBazaar database"
                }
        else:
            return _error_result("MalwareBazaar", f"status_{response.status_code}")

    except Exception as e:
        return _error_result("MalwareBazaar", str(e), transient=True)


# ─────────────────────────────────────────────
# COMBINED ENRICHMENT FUNCTIONS
# These call multiple tools at once
# ─────────────────────────────────────────────

def enrich_ip(ip):
    """
    Full IP enrichment using all relevant tools
    Used by: Brute Force + Network Anomaly playbooks
    """
    print(f"\n   [*] Enriching IP: {ip}")
    result = {
        "ip"          : ip,
        "virustotal"  : query_virustotal_ip(ip),
        "abuseipdb"   : query_abuseipdb(ip),
        "alienvault"  : query_alienvault_ip(ip)
    }
    result["provider_errors"] = {
        provider: data.get("error")
        for provider, data in result.items()
        if isinstance(data, dict) and data.get("error")
    }
    result["degraded"] = bool(result["provider_errors"])
    return result


def enrich_url(url):
    """
    Full URL enrichment using all relevant tools
    Used by: Phishing playbook
    """
    print(f"\n   [*] Enriching URL: {url[:50]}...")
    result = {
        "url"         : url,
        "virustotal"  : query_virustotal_url(url),
        "alienvault"  : query_alienvault_url(url)
    }
    result["provider_errors"] = {
        provider: data.get("error")
        for provider, data in result.items()
        if isinstance(data, dict) and data.get("error")
    }
    result["degraded"] = bool(result["provider_errors"])
    return result


def enrich_hash(file_hash):
    """
    Full hash enrichment using all relevant tools
    Used by: Malware playbook
    """
    print(f"\n   [*] Enriching Hash: {file_hash[:20]}...")
    result = {
        "hash"          : file_hash,
        "virustotal"    : query_virustotal_hash(file_hash),
        "alienvault"    : query_alienvault_hash(file_hash),
        "malwarebazaar" : query_malwarebazaar(file_hash)
    }
    result["provider_errors"] = {
        provider: data.get("error")
        for provider, data in result.items()
        if isinstance(data, dict) and data.get("error")
    }
    result["degraded"] = bool(result["provider_errors"])
    return result


# ─────────────────────────────────────────────
# TEST ALL FUNCTIONS
# ─────────────────────────────────────────────
if __name__ == "__main__":

    print("\n" + "="*60)
    print("   THREAT INTEL MODULE TEST")
    print("="*60)

    # Test IP enrichment with a known malicious IP
    print("\n[TEST 1] IP Enrichment")
    print("-"*40)
    ip_result = enrich_ip("1.1.1.1")  # Using Cloudflare DNS as safe test
    print(f"   VT Result  : {ip_result['virustotal'].get('summary', ip_result['virustotal'].get('error', 'No data'))}")
    print(f"   AIPDB Result: {ip_result['abuseipdb'].get('summary', ip_result['abuseipdb'].get('error', 'No data'))}")
    print(f"   OTX Result : {ip_result['alienvault'].get('summary', ip_result['alienvault'].get('error', 'No data'))}")

    # Test URL enrichment
    print("\n[TEST 2] URL Enrichment")
    print("-"*40)
    url_result = enrich_url("http://malware.wicar.org/data/ms14_064_ole_not_xp.html")
    print(f"\n   VT Result  : {url_result['virustotal']['summary']}")
    print(f"   OTX Result : {url_result['alienvault']['summary']}")

    # Test Hash enrichment with known malware hash
    print("\n[TEST 3] Hash Enrichment")
    print("-"*40)
    hash_result = enrich_hash(
        "44d88612fea8a8f36de82e1278abb02f"  # Known EICAR test hash
    )
    print(f"\n   VT Result  : {hash_result['virustotal']['summary']}")
    print(f"   OTX Result : {hash_result['alienvault']['summary']}")
    print(f"   MB Result  : {hash_result['malwarebazaar'].get('summary', hash_result['malwarebazaar'].get('error', 'No data'))}")

    print("\n" + "="*60)
    print("   THREAT INTEL TEST COMPLETE")
    print("="*60)