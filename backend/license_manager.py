import os
import sys
import uuid
import json
import hmac
import hashlib
import base64
import platform
from datetime import datetime, date

SECRET_KEY = "ANTIGRAVITY_CCTV_MASTER_SECRET_KEY_2026"
LICENSE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "license.lic")

def get_machine_hwid() -> str:
    """
    Generates a unique, deterministic Hardware ID (HWID) for the current machine.
    """
    try:
        node = str(uuid.getnode())
        system_info = f"{platform.node()}-{platform.processor()}-{node}"
        hwid_hash = hashlib.sha256(system_info.encode('utf-8')).hexdigest()[:16].upper()
        # Format as XXXX-XXXX-XXXX-XXXX
        return f"{hwid_hash[:4]}-{hwid_hash[4:8]}-{hwid_hash[8:12]}-{hwid_hash[12:16]}"
    except Exception:
        return "DEFAULT-HWID-0000-1111"

def generate_license_key(client_name: str, hwid: str, expiry_date_str: str, plan_name: str = "PRO") -> str:
    """
    Generates a cryptographically signed Base64 license key string.
    expiry_date_str format: YYYY-MM-DD or 'LIFETIME'
    hwid: Specific HWID or 'UNIVERSAL'
    """
    payload = {
        "client": client_name,
        "hwid": hwid.strip().upper(),
        "expiry": expiry_date_str.strip().upper(),
        "plan": plan_name,
        "issued": str(date.today())
    }
    
    payload_json = json.dumps(payload, sort_keys=True)
    payload_b64 = base64.b64encode(payload_json.encode('utf-8')).decode('utf-8')
    
    # Compute HMAC-SHA256 signature
    sig = hmac.new(SECRET_KEY.encode('utf-8'), payload_b64.encode('utf-8'), hashlib.sha256).hexdigest()[:16].upper()
    
    full_license = f"{payload_b64}.{sig}"
    return full_license

def verify_license_key(license_str: str) -> tuple[bool, str, dict]:
    """
    Verifies a license key string.
    Returns (is_valid, status_message, payload_dict)
    """
    if not license_str or "." not in license_str:
        return False, "Invalid License Key format.", {}
        
    try:
        payload_b64, sig = license_str.strip().split(".", 1)
        expected_sig = hmac.new(SECRET_KEY.encode('utf-8'), payload_b64.encode('utf-8'), hashlib.sha256).hexdigest()[:16].upper()
        
        if not hmac.compare_digest(sig.upper(), expected_sig):
            return False, "License signature verification failed (Tampered key).", {}
            
        payload_json = base64.b64decode(payload_b64.encode('utf-8')).decode('utf-8')
        payload = json.loads(payload_json)
        
        # HWID check
        key_hwid = payload.get("hwid", "")
        current_hwid = get_machine_hwid()
        if key_hwid != "UNIVERSAL" and key_hwid != current_hwid:
            return False, f"License is bound to another machine (HWID: {key_hwid}).", payload
            
        # Expiry check
        expiry_str = payload.get("expiry", "")
        if expiry_str != "LIFETIME":
            exp_date = datetime.strptime(expiry_str, "%Y-%m-%d").date()
            if date.today() > exp_date:
                return False, f"License expired on {expiry_str}.", payload
                
        return True, "License Active & Valid", payload
        
    except Exception as e:
        return False, f"License error: {e}", {}

def save_license(license_str: str):
    """Saves license string to local file."""
    with open(LICENSE_FILE, "w", encoding="utf-8") as f:
        f.write(license_str.strip())

def load_stored_license() -> str:
    """Loads stored license string if file exists."""
    if os.path.exists(LICENSE_FILE):
        try:
            with open(LICENSE_FILE, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            return ""
    return ""

def verify_stored_license() -> tuple[bool, str, dict]:
    """Loads and verifies the stored license file."""
    license_str = load_stored_license()
    return verify_license_key(license_str)
