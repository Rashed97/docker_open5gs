# Subscription Management and UICC Programming

## Using the Docker container

TODO - DO NOT USE

Several issues are still present with the Docker container:
- Cannot exec from one container to another for Open5GS dbcli commands
- Cannot use localhost for PyHSS and osmoHLR

## Using the script(s)

### Install Pre-requisites

Install required packages (replace xUbuntu_24.04 with your distribution and version):

```
export OSMOCOM_REPO="https://downloads.osmocom.org/packages/osmocom:/latest/xUbuntu_24.04"
wget $OSMOCOM_REPO/Release.key && sudo mv Release.key /etc/apt/trusted.gpg.d/osmocom-latest.asc
sudo echo "deb [signed-by=/etc/apt/trusted.gpg.d/osmocom-latest.asc] $OSMOCOM_REPO/ ./" > /etc/apt/sources.list.d/osmocom-latest.list
sudo apt update
sudo apt install python3-dev python3-osmopy-utils python3-pymongo python3-bson python3-pycryptodome python3-cmd2
```

Install Ki/OPc Generator:

```
pip install git+https://github.com/iotconnectivity/kiopcgenerator#egg=kiopcgenerator
```

Sync pySim to this directory:

```
git clone https://gitea.osmocom.org/sim-card/pysim.git
cd pysim
sudo apt install --no-install-recommends \
	pcscd libpcsclite-dev \
	python3 \
	python3-setuptools \
	python3-pycryptodome \
	python3-pyscard \
	python3-pip
pip3 install --user -r requirements.txt
```

### Using the unified script
TODO

The `program_and_add.py` script simplifies the process by condensing everything into one script, however this has not been validated properly yet.

### Using the seperate scripts
#### Generate Ki and OPc
Use the gen_pair.py script to generate your Ki and OPc pair:

```
./gen_pair.py
```

Your output should look like this:

```
{'KI': 'D79F9B3430124778B25BCCBC6CED8C8F',
 'eKI': '8FAC9FE22D306EA4CB86279B3473D8CB',
 'OPC': '34077031C9AF38D7ECB6FD6AC4B1BCFB'}
```

Save the generated Ki and OPc values for use in the next scripts. The eKi is not currently utilized.

NOTE: any 32 character string will work for Ki and OPc in the current setup, however we're utilizing the actual methods to generate them to future-proof against added security checks in the network core.

#### Program UICC
Use the program_sim.sh script to program your UICC. Make sure that the script is located in the same directory as your pySim sync. If you ran git clone in this folder, then you have nothing else to do.

```
./program_sim.sh -a ADM1 -p PLMN -s ICCID -k Ki -o OPc
```

Replace the arguments as follows:
- ADM1: the ADM1 PIN for your UICC. If you're using a sysmocom sysmoISIM-SJA2 or SJA5 then the ADM1 PIN is on the card and was emailed to you at time of purchase
- PLMN: the PLMN of the network. Make sure this is the same PLMN you've set in .env for the Docker images
- ICCID: the ICCID of the UICC. If you're using a sysmocom sysmoISIM-SJA2 or SJA5 then this is non-modifiable, but you must put it here for pySim to select the UICC correctly
- Ki: the Ki value generated above
- OPc: the OPc value generated above

Your actual command will look something like this:
```
./program_sim.sh -a 72089329 -p 00101 -s 8949440000001163326 -k D79F9B3430124778B25BCCBC6CED8C8F -o 34077031C9AF38D7ECB6FD6AC4B1BCFB
```

#### Add Subscriber to Network Databases
Before adding your subscriber to the databases, you need to derive several values. The program_sim.sh script automatically derives the values for the IMSI and MSISDN from the PLMN and ICCID,
but the add_subscriber.py script expects them to be passed manually. To ensure that your values match, you will need to derive the IMSI and MSISDN yourself to pass to the script, otherwise
you will not be able to connect to the network as your values will not match.

To derive the IMSI: `imsi = plmn + iccid[8:18]`. Take the PLMN (5 digits) and then add the last 10 digits of the ICCID you're using (note: the last digit of the ICCID is a checksum digit. DO NOT INCLUDE THIS). For example: PLMN `00101` + ICCID `8949440000001163326` yields: `00101 + 0000116332 = 001010000116332` as your IMSI

To derive the MSISDN: `msisdn = "+1101202" + imsi[-4:]`. Take the last 4 digits of the derived IMSI and append them to `+1101202` for your MSISDN. For example, for IMSI `001010000116332` , the MSISDN would be `"+11012026332"`.

Now use the add_subscriber.py script to add your newly created UICC subscription to the HSS/UDR (Open5GS database), the IMS HSS (PyHSS), and the HLR (osmoHLR)

```
./add_subscriber.py -i IMSI -k Ki -o OPc --msisdn MSISDN --pyhss-url localhost --osmohlr-ctrl-host localhost
```

Replace the arguments as follows:
- IMSI: the IMSI that you derived above
- Ki: the Ki value generated above
- OPc: the OPc value generated above
- MSISDN: the MSISDN value derived above

Note: the PyHSS and osmoHLR hosts should be localhost if you're running this script on the same machine that the network Docker containers are running on. Ensure you have the containers up before running this script. If you're running this script on a different machine, replace `localhost` with correct hostname/address.

Your actual command will look something like this:
```
./add_subscriber.py -i 001010000116332 -k D79F9B3430124778B25BCCBC6CED8C8F -o 34077031C9AF38D7ECB6FD6AC4B1BCFB --msisdn "+11012026332" --pyhss-url localhost --osmohlr-ctrl-host localhost
```
