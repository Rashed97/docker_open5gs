#!/bin/bash

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
