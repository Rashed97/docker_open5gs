#!/usr/bin/python3

import Open5GS
Open5GS_1 = Open5GS.Open5GS("172.22.0.2", 27017)

print(Open5GS_1.GetSubscriber('001010000116332'))
