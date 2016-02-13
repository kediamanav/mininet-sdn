from pox.core import core
import pox.openflow.libopenflow_01 as of
import pox.lib.packet as pkt
from pox.lib.addresses import EthAddr
from pox.lib.util import dpidToStr

log = core.getLogger()


def prefix_match(ip1,ip2,net):
  i1 = ip1.strip().split('.')
  i2 = ip2.strip().split('.')
  i1 = [int(i) for i in i1]
  i2 = [int(i) for i in i2]
  count = 0
  for i in range(0,4):
    if(i1[i] == i2[i]): count += 8
    else: break
  if(count>=net): return True
  else: return False


def checksum(pack_ip):
    # log.info(pack_ip.v)
    # log.info(pack_ip.hl)
    # log.info(pack_ip.tos)
    # log.info(pack_ip.iplen)
    # log.info(pack_ip.id)
    # log.info(pack_ip.flags)
    # log.info(pack_ip.frag)
    # log.info(pack_ip.ttl)
    # log.info(pack_ip.protocol)
    # log.info(pack_ip.srcip)
    # log.info(pack_ip.dstip)
    # log.info(pack_ip.checksum())
    return pack_ip.checksum()


def _handle_PacketIn (event):
  packet = event.parsed

  print event.connection.dpid

  if not packet.parsed:
    log.warning("Packet incomplete")  
    return

  #packet_in = event.ofp

  log.info(packet)
  id = event.connection.dpid

  if packet.find("arp"):
    # Reply to ARP
    a = packet.find("arp")
    log.info(a)
    if a.opcode == a.REQUEST:
      r = pkt.arp()
      r.hwtype = a.hwtype
      r.prototype = a.prototype
      r.hwlen = a.hwlen
      r.protolen = a.protolen
      r.opcode = r.REPLY
      r.hwdst = a.hwsrc
      r.protodst = a.protosrc
      r.protosrc = a.protodst
      r.hwsrc = EthAddr("ee:0a:ff:d2:b7:03")
      e = pkt.ethernet(type=packet.type, src=r.hwsrc, dst=a.hwsrc)
      e.payload = r

      msg = of.ofp_packet_out()
      msg.data = e.pack()
      msg.actions.append(of.ofp_action_output(port = of.OFPP_IN_PORT))
      msg.in_port = event.port
      event.connection.send(msg)

      log.info("%s ARPed for %s", r.protodst, r.protosrc)


  elif packet.find("ipv4"):

    if (id==1 or id==2):

    #   print "Switch"

    #   ipp = pkt.ipv4()
    #   e = pkt.ethernet(type=packet.type, src=packet.src, dst="ff:ff:ff:ff:ff:ff")
    #   e.payload = ipp

    #   msg = of.ofp_packet_out()
    #   msg.data = e.pack()
    #   msg.actions.append(of.ofp_action_output(port = of.OFPP_IN_PORT))
    #   msg.in_port = event.port
    #   event.connection.send(msg)

      msg = of.ofp_flow_mod()
      msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
      event.connection.send(msg)
      log.info("Hubifying %s", dpidToStr(event.dpid))

    #   log.debug("Broadcasting %s.%i -> %s.%i" %(packet.src, event.ofp.in_port, packet.dst, of.OFPP_ALL))

    else:
      print "Router"
      
      p = packet.find("ipv4")
      log.info(p)

      #Checking min length of IP Header
      if p.hl<5:
        log.warning("IP header less than minimum length")
        return

      #Check the checksum
      csum = checksum(p)
      if csum!=p.csum:
        log.warning("Checksum not matching")
        return

      #Decrement TTL
      if p.ttl==0:
        log.warning("Send time limit exceeded ICMP message")
        return

      p.ttl = p.ttl -1


      #Recompute Checksum and set it
      p.csum = checksum(p)

      
      #Find from routing table
      file_name = "r"+str(int(event.connection.dpid)-2)+".txt"
      print file_name


      # Get next hop IP and other connections
      nexthopip = ""
      interface = ""

      with open('/home/mininet/mininet-sdn/routing_tables/'+file_name,'r') as f:
        length = 0
        for line in f:
          line=line.strip()
          line=line.split(',')
          if prefix_match(p.dst_ip,line[0],int(line[1])):
            if length>int(line[1]):
              length=int(line[1])
              nexthopip = line[2]
              interface = line[3]

      print nexthopip,interface

  """
  
 
  elif packet.find("icmp"):
    # Reply to pings

    # Make the ping reply
    icmp = pkt.icmp()
    icmp.type = pkt.TYPE_ECHO_REPLY
    icmp.payload = packet.find("icmp").payload

    # Make the IP packet around it
    ipp = pkt.ipv4()
    ipp.protocol = ipp.ICMP_PROTOCOL
    ipp.srcip = packet.find("ipv4").dstip
    ipp.dstip = packet.find("ipv4").srcip

    # Ethernet around that...
    e = pkt.ethernet()
    e.src = packet.dst
    e.dst = packet.src
    e.type = e.IP_TYPE

    # Hook them up...
    ipp.payload = icmp
    e.payload = ipp

    # Send it back to the input port
    msg = of.ofp_packet_out()
    msg.actions.append(of.ofp_action_output(port = of.OFPP_IN_PORT))
    msg.data = e.pack()
    msg.in_port = event.port
    event.connection.send(msg)

    log.debug("%s pinged %s", ipp.dstip, ipp.srcip)

  elif packet.find("tcp"):
    log.debug("tcp found: %s:%s to %s:%s", packet.find("ipv4").srcip, packet.find("tcp").srcport, packet.find("ipv4").dstip, packet.find("tcp").dstport)

  elif packet.find("udp"):
    log.debug("udp found: %s:%s to %s:%s", packet.find("ipv4").srcip, packet.find("udp").srcport, packet.find("ipv4").dstip, packet.find("udp").dstport)
  """

def launch ():
  import pox.log.color
  pox.log.color.launch()
  import pox.log
  pox.log.launch(format="[@@@bold@@@level%(name)-22s@@@reset] " +
                        "@@@bold%(message)s@@@normal")

  core.openflow.addListenerByName("PacketIn", _handle_PacketIn)

  log.info("Pong component running.")