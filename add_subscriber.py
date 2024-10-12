#!/usr/bin/python3

import argparse
import subprocess
import requests
import socket

from osmopy.osmo_ipa import Ctrl

# OsmoCtrlClient class handles the socket connection to OsmoHLR's CTRL interface.
class OsmoCtrlClient(Ctrl):
    def __init__(self):
        super().__init__()  # Initialize the base Ctrl class
        self.sock = None

    def connect(self, host, port):
        # Manually create a socket and connect to the CTRL interface
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setblocking(1)
        self.sock.connect((host, port))
        print(f"Connected to {host}:{port}")

    def send_command(self, var, value = None):
        print(f"Sending command: {var}")
        self._leftovers(self.sock, socket.MSG_DONTWAIT)
        (r, c) = self.cmd(var, value)
        self.sock.send(c)
        while True:
                ret = self.sock.recv(4096)
                # handle multiple messages, ignore TRAPs
                ret = self.skip_traps(ret)
                if ret != None:
                    (i, k, v) = self.parse(ret)
                    break;
        return (self.rem_header(ret),) + self.verify(ret, r, var, value)

    def close(self):
        if self.sock:
            self.sock.close()
            print("Connection closed")

    def _leftovers(self, sock, fl):
        """
        Read outstanding data if any according to flags
        """
        try:
            data = sock.recv(1024, fl)
        except socket.error as _:
            return False
        if len(data) != 0:
            tail = data
            while True:
                (head, tail) = Ctrl().split_combined(tail)
                print("Got message:", Ctrl().rem_header(head))
                if len(tail) == 0:
                    break
            return True
        return False

def add_to_open5gs(imsi, ki, opc):
    """
    Add subscriber to Open5GS HSS using the open5gs-dbctl tool.
    """
    try:
        subprocess.run(
            ["docker", "exec", "-it", "hss", "misc/db/open5gs-dbctl", "add", imsi, ki, opc],
            check=True
        )
        print("Subscriber added to Open5GS HSS successfully.")

    except subprocess.CalledProcessError as e:
        print(f"Failed to add subscriber to Open5GS HSS: {e}")

def format_pyhss_url(api_base_url):
    """
    Format the PyHSS URL by ensuring 'http://' is prepended and ':8080' is appended.
    """
    if not api_base_url.startswith('http://'):
        api_base_url = f"http://{api_base_url}"

    return f"{api_base_url}:8080"

def add_auc_to_pyhss(api_base_url, imsi, ki, opc, amf="8000", sqn=0):
    """
    Add a new AUC to PyHSS and return the auc_id.
    """
    api_url = format_pyhss_url(api_base_url)
    data = {
        "ki": ki,
        "opc": opc,
        "amf": amf,
        "sqn": sqn,
        "imsi": imsi
    }
    try:
        response = requests.put(f"{api_url}/auc/", headers={"Content-Type": "application/json"}, json=data)
        response.raise_for_status()
        auc_id = response.json().get("auc_id")
        if auc_id is None:
            raise ValueError("AUC ID not found in response.")
        print(f"AUC added to PyHSS successfully. AUC ID: {auc_id}")
        return auc_id

    except (requests.exceptions.RequestException, ValueError) as e:
        print(f"Failed to add AUC to PyHSS: {e}")
        return None

def add_subscriber_to_pyhss(api_base_url, imsi, msisdn, auc_id, default_apn=1, apn_list="1,2", ue_ambr_dl=0, ue_ambr_ul=0):
    """
    Add subscriber to PyHSS via the REST API and validate the response.
    """
    api_url = format_pyhss_url(api_base_url)
    data = {
        "imsi": imsi,
        "enabled": True,
        "auc_id": auc_id,
        "default_apn": default_apn,
        "apn_list": apn_list,
        "msisdn": msisdn,
        "ue_ambr_dl": ue_ambr_dl,
        "ue_ambr_ul": ue_ambr_ul
    }
    try:
        response = requests.put(f"{api_url}/subscriber/", headers={"Content-Type": "application/json"}, json=data)
        response.raise_for_status()
        response_data = response.json()

        if (response_data.get("imsi") == imsi and
            response_data.get("msisdn") == msisdn.strip('+') and
            response_data.get("auc_id") == auc_id and
            response_data.get("default_apn") == default_apn and
            response_data.get("apn_list") == apn_list):
            print("Subscriber added to PyHSS successfully and validated.")
        else:
            print("Validation failed: Response does not match input values.")
            print(f"Expected: {data}")
            print(f"Received: {response_data}")

    except requests.exceptions.RequestException as e:
        print(f"Failed to add subscriber to PyHSS: {e}")

def add_ims_subscriber_to_pyhss(api_base_url, imsi, msisdn, sh_profile="string", scscf_peer="scscf.ims.mnc001.mcc001.3gppnetwork.org", ifc_path="default_ifc.xml", scscf="sip:scscf.ims.mnc001.mcc001.3gppnetwork.org:6060", scscf_realm="ims.mnc001.mcc001.3gppnetwork.org", msisdn_list=None):
    """
    Add IMS subscriber to PyHSS via the REST API and validate the response.
    """
    api_url = format_pyhss_url(api_base_url)
    if msisdn_list is None:
        msisdn_list = f"[{msisdn}]"

    data = {
        "imsi": imsi,
        "msisdn": msisdn,
        "sh_profile": sh_profile,
        "scscf_peer": scscf_peer,
        "msisdn_list": msisdn_list,
        "ifc_path": ifc_path,
        "scscf": scscf,
        "scscf_realm": scscf_realm
    }

    try:
        response = requests.put(f"{api_url}/ims_subscriber/", headers={"Content-Type": "application/json"}, json=data)
        response.raise_for_status()
        response_data = response.json()

        if (response_data.get("imsi") == imsi and
            response_data.get("msisdn") == msisdn.strip('+') and
            response_data.get("scscf") == scscf and
            response_data.get("scscf_realm") == scscf_realm and
            response_data.get("scscf_peer") == scscf_peer):
            print("IMS Subscriber added to PyHSS successfully and validated.")
        else:
            print("Validation failed: Response does not match input values.")
            print(f"Expected: {data}")
            print(f"Received: {response_data}")

    except requests.exceptions.RequestException as e:
        print(f"Failed to add IMS subscriber to PyHSS: {e}")

def add_to_osmohlr(ctrl_host, imsi, msisdn, ctrl_port=4259):
    """
    Add subscriber to OsmoHLR using a socket connection.
    """
    try:
        # Initialize the CTRL client
        client = OsmoCtrlClient()

        # Connect to the OsmoHLR CTRL interface
        client.connect(ctrl_host, ctrl_port)

        # Format and send the command, and get the response
        command = f"subscriber.create"
        value = f"{imsi}"
        response = client.send_command(command, value)

        # Check the response
        if "ERROR" in response[0].decode("utf-8"):
            print(f"Failed to add subscriber to OsmoHLR: {response}")
        else:
            print("Subscriber added to OsmoHLR successfully.")

        # Set the MSISDN if the subscriber creation succeeded
        command = f"subscriber.by-imsi-{imsi}.msisdn"
        value = f"{msisdn.strip('+')}"
        response = client.send_command(command, value)

        # Check the response
        if "ERROR" in response[0].decode("utf-8"):
            print(f"Failed to set subscriber MSISDN: {response}")
        else:
            print("Subscriber MSISDN set successfully.")

        # Close the connection
        client.close()

    except Exception as e:
        print(f"Error while adding subscriber to OsmoHLR: {e}")

def main():
    parser = argparse.ArgumentParser(description="Automate adding subscribers to Open5GS, PyHSS, and OsmoHLR.")
    parser.add_argument("-i", "--imsi", required=True, help="The subscriber ID (IMSI)")
    parser.add_argument("-k", "--ki", required=True, help="The authentication key (Ki) value of the subscriber's UICC")
    parser.add_argument("-o", "--opc", required=True, help="The Operator Code (OPc) value of the subscriber's UICC")
    parser.add_argument("-m", "--msisdn", required=True, help="The MSISDN for the subscriber (with '+' prefix)")
    parser.add_argument("--pyhss-url", required=True, help="The PyHSS API base URL (FQDN or IP address)")
    parser.add_argument("--osmohlr-ctrl-host", required=True, help="The OsmoHLR CTRL interface host")
    parser.add_argument("--skip-core-hss", required=False, action='store_true', help="Skip adding the subscriber to the EPC/5GC HSS")
    parser.add_argument("--skip-pyhss", required=False, action='store_true', help="Skip adding the subscriber to PyHSS")
    parser.add_argument("--skip-osmohlr", required=False, action='store_true', help="Skip adding the subscriber to OsmoHLR")

    args = parser.parse_args()

    # Add AUC to PyHSS and get the AUC ID if not skipping PyHSS
    auc_id = None
    if not args.skip_pyhss:
        auc_id = add_auc_to_pyhss(args.pyhss_url, args.imsi, args.ki, args.opc)
        if auc_id is None:
            print("Aborting: Failed to add AUC to PyHSS.")
            return

    # Add subscriber to Open5GS if not skipping core HSS
    if not args.skip_core_hss:
        add_to_open5gs(args.imsi, args.ki, args.opc)

    # Add subscriber to PyHSS if not skipping
    if not args.skip_pyhss and auc_id:
        add_subscriber_to_pyhss(args.pyhss_url, args.imsi, args.msisdn, auc_id)
        add_ims_subscriber_to_pyhss(args.pyhss_url, args.imsi, args.msisdn)

    # Add subscriber to OsmoHLR if not skipping
    if not args.skip_osmohlr:
        add_to_osmohlr(args.osmohlr_ctrl_host, args.imsi, args.msisdn)

if __name__ == "__main__":
    main()
