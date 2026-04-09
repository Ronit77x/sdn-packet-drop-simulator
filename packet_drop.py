from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.packet import ipv4

log = core.getLogger()
mac_to_port = {}

def _handle_PacketIn(event):
    packet = event.parsed
    if not packet.parsed:
        return

    dpid = event.connection.dpid
    in_port = event.port

    src = packet.src
    dst = packet.dst

    mac_to_port.setdefault(dpid, {})
    mac_to_port[dpid][src] = in_port

    # 🔴 IP-based DROP condition (BEST METHOD)
    ip = packet.find('ipv4')

    if ip:
        if str(ip.srcip) == "10.0.0.1" and str(ip.dstip) == "10.0.0.3":
            log.info("Dropping packet from h1 to h3")

            # Install DROP rule
            msg = of.ofp_flow_mod()
            msg.match.dl_type = 0x0800  # IP
            msg.match.nw_src = ip.srcip
            msg.match.nw_dst = ip.dstip

            # No actions = DROP
            event.connection.send(msg)
            return

    # ✅ NORMAL FORWARDING (learning switch)
    if dst in mac_to_port[dpid]:
        out_port = mac_to_port[dpid][dst]
    else:
        out_port = of.OFPP_FLOOD

    msg = of.ofp_packet_out()
    msg.data = event.ofp
    msg.actions.append(of.ofp_action_output(port=out_port))
    msg.in_port = in_port

    event.connection.send(msg)

def launch():
    core.openflow.addListenerByName("PacketIn", _handle_PacketIn)
    log.info("Packet Drop Controller started 🚀")
