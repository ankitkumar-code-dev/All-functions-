# manual_ration.py - Manual script to get ration card from Aadhar

import os
import re
import json
import base64
import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

# ============================================================
# MERA RATION CONFIG
# ============================================================
MERATION_AES_KEY = bytes.fromhex("64ca098b0a8481987615e69b0f8d43ef")
MERATION_AES_IV = bytes.fromhex("6e696340696d70647323646564757030")
MERATION_API_KEY = "1a7a78f970a7a6d0a5042aebc0fbf4a67c999a87c9fde871b17017c82b477396"
MERATION_BASE_URL = "https://meraration.nic.in/onorc/v1"

def meration_encrypt_aadhar(aadhar: str) -> str:
    """Encrypt Aadhar number for Mera Ration API"""
    cipher = AES.new(MERATION_AES_KEY, AES.MODE_CBC, MERATION_AES_IV)
    ct = cipher.encrypt(pad(aadhar.encode("utf-8"), AES.block_size))
    b64_inner = base64.b64encode(ct)
    b64_outer = base64.b64encode(b64_inner)
    return b64_outer.decode("utf-8")

def get_ration_card_from_aadhar(aadhar_number):
    """Get ration card number from Aadhar"""
    try:
        # Clean Aadhar number
        aadhar = re.sub(r"\s+", "", aadhar_number)
        
        # Validate Aadhar
        if not aadhar.isdigit() or len(aadhar) != 12:
            return {"success": False, "error": "Invalid Aadhar (must be 12 digits)"}
        
        print(f"Processing Aadhar: {aadhar}")
        
        # Create session
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Dart/3.5 (dart:io)",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Bearer",
            "Language": "en",
            "Key": MERATION_API_KEY,
        })
        
        # Encrypt Aadhar
        encrypted_aadhar = meration_encrypt_aadhar(aadhar)
        print(f"Encrypted Aadhar: {encrypted_aadhar[:50]}...")
        
        # Send request
        print("Sending OTP request...")
        resp = session.post(
            f"{MERATION_BASE_URL}/verifyAadharNumber",
            json={"aadharNumber": encrypted_aadhar, "forceUpdate": ""}
        )
        
        result = resp.json()
        print(f"Response Status: {result.get('success')}")
        
        if result.get("success"):
            data = result.get("data", {})
            return {
                "success": True,
                "rationCardNumber": data.get("rationCardNumber"),
                "txnId": data.get("txnId"),
                "imeiNo": data.get("imeiNo", "N/A"),
                "message": "OTP sent successfully"
            }
        else:
            return {
                "success": False,
                "error": result.get("message", "Unknown error"),
                "raw_response": result
            }
            
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"Network error: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Error: {str(e)}"}

def main():
    """Main function to run the script"""
    print("=" * 60)
    print("AADHAR TO RATION CARD FINDER")
    print("=" * 60)
    print()
    
    # Get Aadhar from user
    aadhar = input("Enter 12-digit Aadhar Number: ").strip()
    
    if not aadhar:
        print("Error: Aadhar number is required")
        return
    
    # Get ration card
    print("\nFetching ration card details...\n")
    result = get_ration_card_from_aadhar(aadhar)
    
    # Display results
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    
    if result.get("success"):
        print(f"✅ SUCCESS!")
        print(f"Ration Card Number: {result.get('rationCardNumber', 'N/A')}")
        print(f"Transaction ID: {result.get('txnId', 'N/A')}")
        print(f"IMEI: {result.get('imeiNo', 'N/A')}")
        print(f"Message: {result.get('message', 'OTP sent successfully')}")
        print("\n📱 An OTP has been sent to your registered mobile number.")
        print("Use this OTP to verify and get full family details.")
    else:
        print(f"❌ FAILED!")
        print(f"Error: {result.get('error', 'Unknown error')}")
        if result.get("raw_response"):
            print(f"Raw Response: {json.dumps(result.get('raw_response'), indent=2)}")
    
    print("=" * 60)

if __name__ == "__main__":
    main()