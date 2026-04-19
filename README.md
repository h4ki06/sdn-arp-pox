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

## Run POX
```bash
cd ~/pox
./pox.py log.level --DEBUG openflow.of_01 misc.arp_policy
