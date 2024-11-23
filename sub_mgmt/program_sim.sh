#!/bin/bash
# BSD 2-Clause License

# Copyright (c) 2024, Rashed Abdel-Tawab
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.

# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.

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

# Script to program UICC

helpFunction()
{
   echo ""
   echo "Usage: $0 -a ADM1 -p PLMN -s ICCID -k Ki -o OpC"
   echo -e "\t-a The ADM1 PIN of the UICC"
   echo -e "\t-p The PLMN of the network to program the UICC for"
   echo -e "\t-s The UICC ICCID"
   echo -e "\t-k The authentication key (Ki) value to be programmed to the UICC"
   echo -e "\t-o The Operator Code (OPc) value to be programmed to the UICC"
   exit 1 # Exit script after printing help
}

while getopts "a:p:s:k:o:h" opt
do
   case "$opt" in
      a ) adm="$OPTARG" ;;
      p ) plmn="$OPTARG" ;;
      s ) iccid="$OPTARG" ;;
      k ) ki="$OPTARG" ;;
      o ) opc="$OPTARG" ;;
      h ) helpFunction ;;
      ? ) helpFunction ;; # Print helpFunction in case parameter is non-existent
   esac
done

# Print helpFunction in case parameters are empty
if [ -z "$adm" ] || [ -z "$plmn" ] || [ -z "$iccid" ] || [ -z "$ki" ] || [ -z "$opc" ]
then
   echo "Some or all of the parameters are empty";
   helpFunction
fi

imsi=$plmn$(echo $iccid | cut -c9-18)
mcc=$(echo $plmn | cut -c-3)
mnc=$(echo $plmn | cut -c4-)
msisdn="+1101202"$(echo $imsi | rev | cut -c-4 | rev)

# Begin script in case all parameters are correct
echo "ADM1: $adm"
echo "ICCID: $iccid"
echo "IMSI: $imsi"
echo "MCC: $mcc"
echo "MNC: $mnc"
echo "Ki: $ki"
echo "OPc: $opc"
echo "MSISDN: $msisdn"

#    --dry-run \
./pysim/pySim-prog.py -p0 \
    -a $adm \
    -n RashedNet \
    -s "$iccid" \
    -i "$imsi" \
    -x $mcc -y $mnc \
    -k $ki \
    -o $opc \
    --msisdn "$msisdn" \
    --pcscf "pcscf.ims.mnc0$mnc.mcc$mcc.3gppnetwork.org" \
    --ims-hdomain "ims.mnc0$mnc.mcc$mcc.3gppnetwork.org" \
    --impi "$imsi@ims.mnc0$mnc.mcc$mcc.3gppnetwork.org" \
    --impu "sip:$imsi@ims.mnc0$mnc.mcc$mcc.3gppnetwork.org" \
    --epdgid "epdg.epc.mnc0$mnc.mcc$mcc.pub.3gppnetwork.org" \
    --epdgSelection $plmn

./pysim/pySim-shell.py -p0 --script sim-carrier-app.script
