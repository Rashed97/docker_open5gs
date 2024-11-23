#!/usr/bin/python3
# BSD 2-Clause License
#
# Copyright (c) 2024, Rashed Abdel-Tawab
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import pprint
import uuid
import kiopcgenerator
import subprocess

# Paths to other scripts to use
script_program_sim_path = '/program_sim.sh'
script_add_subscriber_path = '/add_subscriber.py'

# TODO: Allow passing these with arguments
op = "74E2FE5C673BD5F141FFAD0F12320430"
transport = "29DE2CC486338BEE009D429ECEBDFE69"

def main():
    parser = argparse.ArgumentParser(description="Automate programming UICCs with pySim and adding subscribers to Open5GS, PyHSS, and OsmoHLR.")
    # TODO: re-enable once program_sim.sh can also accept an IMSI argument
    #parser.add_argument("-i", "--imsi", required=False, help="The subscriber ID (IMSI); optional, only set this to override the automatically calculated IMSI")
    parser.add_argument("-a", "--adm1", required=True, help="The ADM1 PIN of the UICC")
    parser.add_argument("-p", "--plmn", required=True, help="The PLMN of the network")
    parser.add_argument("-s", "--iccid", required=True, help="The UICC ICCID")
    # TODO: re-enable once program_sim.sh can also accept an MSISDN argument
    #parser.add_argument("-m", "--msisdn", required=False, help="The MSISDN for the subscriber (with '+' prefix); optional, only set this to override the automatically calculated MSISDN")
    parser.add_argument("--pyhss-url", required=True, help="The PyHSS API base URL (FQDN or IP address)")
    parser.add_argument("--osmohlr-ctrl-host", required=True, help="The OsmoHLR CTRL interface host")
    parser.add_argument("--skip-core-hss", required=False, action='store_true', help="Skip adding the subscriber to the EPC/5GC HSS")
    parser.add_argument("--skip-pyhss", required=False, action='store_true', help="Skip adding the subscriber to PyHSS")
    parser.add_argument("--skip-osmohlr", required=False, action='store_true', help="Skip adding the subscriber to OsmoHLR")

    args = parser.parse_args()

    # Generates random Ki for this subscriber
    ki = kiopcgenerator.gen_ki()

    # Generate OPc and eKi derived from Ki
    opc = kiopcgenerator.gen_opc(op, ki)
    eki = kiopcgenerator.gen_eki(transport, ki) # NOTE: currently unused

    # Setup arguments for UICC programming and call script
    script_program_sim_args = ['-a', args.adm, '-p', args.plmn, '-s', args.iccid, '-k', args.ki, '-o', args.opc]
    try:
        result = subprocess.run(
            [script_program_sim_path] + script_program_sim_args,  # Call script as an external process
            check=True,                # Raise exception on non-zero exit
            text=True,                 # Capture output as text
            capture_output=True        # Capture stdout and stderr
        )
        print("program_sim.sh Output:", result.stdout)
        print("program_sim.sh Errors (if any):", result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"program_sim.sh failed with exit code {e.returncode}")
        print(f"Error output: {e.stderr}")

    #if not args.imsi:

    # Calculate IMSI
    imsi = args.plmn + args.iccid[8:18]

    # Extract MCC and MNC
    mcc = args.plmn[:3]
    mnc = args.plmn[3:]

    # Calculate MSISDN
    msisdn = "+1101202" + imsi[-4:]

    # Setup arguments for subscriber addition
    script_add_subscriber_args = ['-i', imsi, '-k', ki, '-o', opc, '--msisdn', msisdn, '--pyhss-url', args.pyhss_url '--osmohlr-ctrl-host', args.osmohlr_ctrl_host]
    if args.skip_core_hss:
        script_add_subscriber_args.append("--skip-core-hss")
    if args.skip_pyhss:
        script_add_subscriber_args.append("--skip-pyhss")
    if args.skip_osmohlr:
        script_add_subscriber_args.append("--skip-osmohlr")
    try:
        result = subprocess.run(
            [script_add_subscriber_path] + script_add_subscriber_args,  # Call script as an external process
            check=True,                # Raise exception on non-zero exit
            text=True,                 # Capture output as text
            capture_output=True        # Capture stdout and stderr
        )
        print("add_subscriber.sh Output:", result.stdout)
        print("add_subscriber.sh Errors (if any):", result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"add_subscriber.sh failed with exit code {e.returncode}")
        print(f"Error output: {e.stderr}")

if __name__ == "__main__":
    main()
