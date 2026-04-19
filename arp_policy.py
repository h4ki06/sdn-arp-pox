from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.packet.ethernet import ethernet
from pox.lib.packet.arp import arp
from pox.lib.packet.ipv4 import ipv4
from pox.lib.addresses import EthAddr, IPAddr

log = core.getLogger()

# Learned state
mac_to_port = {}   # {dpid: {mac: port}}
arp_table = {}     # {ip: mac}

# Blocked flow scenario: h1 -> h3
BLOCKED = {
    ("10.0.0.1", "10.0.0.3")
}


def send_packet(connection, packet_data, out_port):
    msg = of.ofp_packet_out()
    msg.data = packet_data
    msg.actions.append(of.ofp_action_output(port=out_port))
    connection.send(msg)


def send_arp_reply(connection, req, out_port):
    r = arp()
    r.opcode = arp.REPLY
    r.hwsrc = arp_table[req.protodst]
    r.hwdst = req.hwsrc
    r.protosrc = req.protodst
    r.protodst = req.protosrc

    e = ethernet(type=ethernet.ARP_TYPE, src=r.hwsrc, dst=r.hwdst)
    e.payload = r

    msg = of.ofp_packet_out()
    msg.data = e.pack()
    msg.actions.append(of.ofp_action_output(port=out_port))
    connection.send(msg)

    log.info("Sent ARP reply: %s is-at %s", str(r.protosrc), str(r.hwsrc))


def install_flow(connection, in_port, dst_mac, out_port):
    msg = of.ofp_flow_mod()
    msg.match.in_port = in_port
    msg.match.dl_dst = dst_mac
    msg.actions.append(of.ofp_action_output(port=out_port))
    connection.send(msg)


def install_drop_flow(connection, src_ip, dst_ip):
    msg = of.ofp_flow_mod()
    msg.priority = 100
    msg.match.dl_type = ethernet.IP_TYPE
    msg.match.nw_src = IPAddr(src_ip)
    msg.match.nw_dst = IPAddr(dst_ip)
    # no actions => drop
    connection.send(msg)
    log.info("Installed DROP rule for %s -> %s", src_ip, dst_ip)


def _handle_ConnectionUp(event):
    dpid = event.connection.dpid
    mac_to_port.setdefault(dpid, {})
    log.info("Switch %s connected", dpid)


def _handle_PacketIn(event):
    packet = event.parsed
    if not packet.parsed:
        log.warning("Ignoring incomplete packet")
        return

    connection = event.connection
    dpid = connection.dpid
    in_port = event.port

    mac_to_port.setdefault(dpid, {})

    # Learn source MAC -> port
    mac_to_port[dpid][packet.src] = in_port

    # Handle ARP
    if packet.type == ethernet.ARP_TYPE:
        a = packet.payload

        # Learn host discovery info
        arp_table[a.protosrc] = a.hwsrc
        log.info("ARP learned: %s -> %s on port %s", a.protosrc, a.hwsrc, in_port)

        # If ARP request and target known, answer directly from controller
        if a.opcode == arp.REQUEST:
            if a.protodst in arp_table:
                send_arp_reply(connection, a, in_port)
                return
            else:
                # Unknown ARP target => flood
                msg = of.ofp_packet_out()
                msg.data = event.ofp
                msg.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
                connection.send(msg)
                return

        # ARP replies can also be flooded/forwarded
        msg = of.ofp_packet_out()
        msg.data = event.ofp
        msg.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
        connection.send(msg)
        return

    # Handle IPv4 policy
    if packet.type == ethernet.IP_TYPE:
        ip_pkt = packet.payload
        src_ip = str(ip_pkt.srcip)
        dst_ip = str(ip_pkt.dstip)

        if (src_ip, dst_ip) in BLOCKED:
            log.info("Blocking IPv4 traffic: %s -> %s", src_ip, dst_ip)
            install_drop_flow(connection, src_ip, dst_ip)
            return

    # Normal L2 forwarding
    dst = packet.dst

    if dst in mac_to_port[dpid]:
        out_port = mac_to_port[dpid][dst]
        install_flow(connection, in_port, dst, out_port)
        send_packet(connection, event.ofp, out_port)
        log.info("Installed forwarding rule: %s -> port %s", dst, out_port)
    else:
        msg = of.ofp_packet_out()
        msg.data = event.ofp
        msg.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
        connection.send(msg)


def launch():
    core.openflow.addListenerByName("ConnectionUp", _handle_ConnectionUp)
    core.openflow.addListenerByName("PacketIn", _handle_PacketIn)
    log.info("ARP policy POX controller started")
