# SDN ARP Handling using POX and Mininet

## Objective
This project demonstrates ARP handling, host discovery, forwarding, and traffic blocking in an SDN network using POX and Mininet.

## Tools Used
- Ubuntu Linux
- Mininet
- Open vSwitch
- POX Controller

## Files
- `arp_policy.py` : POX controller code
- `screenshots/` : output screenshots
- `report.pdf` : project report (optional)

## Topology
- h1 = 10.0.0.1
- h2 = 10.0.0.2
- h3 = 10.0.0.3
- s1 = switch

## Features
- Intercepts ARP packets
- Learns IP-MAC mappings
- Enables host discovery
- Installs OpenFlow match-action rules
- Allows communication between selected hosts
- Blocks communication for selected flows


# 🚀 Execution Steps
## Step 1: Start POX Controller
cd ~/pox
./pox.py log.level --DEBUG openflow.of_01 misc.arp_policy

## Step 2: Start Mininet
sudo mn -c
sudo mn --topo single,3 --mac --switch ovsk,protocols=OpenFlow10 --controller remote,ip=127.0.0.1,port=6633

## Step 3: Verify Topology
dump

## Step 4: Test Allowed Communication
h1 ping -c 3 h2

## Step 5: Test Blocked Communication
h1 ping -c 3 h3

## Step 6: Bandwidth Testing (iperf)
## Allowed case:
h2 iperf -s &
h1 iperf -c 10.0.0.2
## Blocked case:
h3 iperf -s &
h1 iperf -c 10.0.0.3

## Step 7: Verify OpenFlow Flow Table (in another terminal)
sudo ovs-ofctl dump-flows s1

## Step 8: Check ARP Table (Host Discovery)
h1 arp -n


