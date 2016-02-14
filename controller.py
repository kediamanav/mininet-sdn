from pox.core import core
import pox.openflow.libopenflow_01 as of
import pox.lib.packet as pkt
from pox.lib.packet.arp import arp
from pox.lib.addresses import EthAddr, IPAddr
from pox.lib.util import dpid_to_str
from pox.lib.packet.ethernet import ethernet
import struct

log = core.getLogger()

packet_queue = {}
ip_to_mac = {}


def prefix_match(ip1,ip2,net):
  #print ip1,ip2,net
  i1 = ip1.strip().split('.')
  i2 = ip2.strip().split('.')
  i1 = [int(i) for i in i1]
  i2 = [int(i) for i in i2]
  count = 0
  for i in range(0,4):
    if(i1[i] == i2[i]): 
      count += 8
    else:
      break

  if(count>=net):
    return True
  else:  
    return False


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


def routeChecker(event, ip):

  #Find from routing table
  file_name = "r"+str(int(event.connection.dpid))+".txt"
  #print file_name

  # Get next hop IP and other connections
  nexthopip = ""
  interface = ""

  with open('/home/mininet/mininet-sdn/routing_tables/'+file_name,'r') as f:
    length = 0
    for line in f:
      line=line.strip()
      line=line.split(',')
      if prefix_match(ip,line[0],int(line[1])):
        if length<int(line[1]):
          length=int(line[1])
          nexthopip = line[2]
          interface = line[3]

  print nexthopip,interface,length
  return nexthopip, interface, length



def sendICPMMessage(event,type,code):
  src_ip,my_mac = get_MAC_IP(event.connection.dpid,event.port)

  p=event.parsed.find("ipv4")
  packet = event.parsed

  #print p
  #print packet

  icmp = pkt.icmp()
  icmp.type = type
  icmp.code = code

  data = p.pack()
  data = data[:p.hl * 4 + 8]
  data = struct.pack("!HH", 0,0) + data
  icmp.payload = data

  # Make the IP packet around it
  ipp = pkt.ipv4()
  ipp.protocol = ipp.ICMP_PROTOCOL
  ipp.srcip = IPAddr(src_ip)
  ipp.dstip = p.srcip

  # Ethernet around that...
  e = pkt.ethernet()
  e.src = EthAddr(my_mac)
  e.dst = packet.src
  e.type = e.IP_TYPE

  # Hook them up...
  ipp.payload = icmp
  e.payload = ipp

  #print e
  #print e.payload

  # Send it back to the input port
  event.connection.send(of.ofp_packet_out(
    data=e.pack(),
    action=of.ofp_action_output(port=event.port)))

  log.debug("%s ICMP %s", ipp.dstip, ipp.srcip)



def get_MAC_IP(dpid, port):
  with open('/home/mininet/mininet-sdn/dpid_port_2_ip_mac.txt') as f:
    for line in f.readlines():
      tokens = line.split(',')
      if int(tokens[0]) == dpid and int(tokens[1]) == port:
        my_ip = tokens[2]
        my_mac = tokens[3]

  return (my_ip, my_mac)



def get_MAC(ip, dpid, port, event):
  (my_ip, my_mac) = get_MAC_IP(dpid, port)

  arp_req = arp(
    opcode = arp.REQUEST,
    hwdst = EthAddr("00:00:00:00:00:00"),
    hwsrc = EthAddr(my_mac),
    protodst = IPAddr(ip),
    protosrc = IPAddr(my_ip)
    )

  eth_packet = ethernet(type=ethernet.ARP_TYPE,
                src=EthAddr(my_mac),
                dst=EthAddr("ff:ff:ff:ff:ff:ff"))
  eth_packet.payload = arp_req

  #print eth_packet
  #log.info(eth_packet)

  msg = of.ofp_packet_out(data = eth_packet.pack())
  msg.actions.append(of.ofp_action_output(port = of.OFPP_ALL))
  event.connection.send(msg)

  log.debug("ARP request from %i:%i for ip= %s" %(dpid, port, ip))



def _do_source_learning(event):
  eth_packet = event.parsed
  arp_packet = eth_packet.payload

  if arp_packet.protosrc not in ip_to_mac:
    ip_to_mac[arp_packet.protosrc] = arp_packet.hwsrc
    log.info("Stored in ARP cache: ip=%s => mac=%s",
          arp_packet.protosrc, arp_packet.hwsrc)



def _handle_arp_request(event):
  eth_packet = event.parsed
  arp_packet = eth_packet.payload
  log.info("ARP request: ip=%s query ip=%s", arp_packet.protosrc,
        arp_packet.protodst)

  dpid = event.connection.dpid
  inport = event.port
  protodst = arp_packet.protodst

  (my_ip, my_mac) = get_MAC_IP(dpid, inport)

  if IPAddr(my_ip) != protodst:
    return


  #log.info("hwdst: %s, hwsrc: %s, protodst: %s, protosrc: %s", arp_packet.hwsrc, my_mac, arp_packet.protosrc, arp_packet.protodst)
  arp_reply = arp(opcode=arp.REPLY,
            hwdst=arp_packet.hwsrc,
            hwsrc=EthAddr(my_mac),
            protodst=arp_packet.protosrc,
            protosrc=arp_packet.protodst)


  eth_reply = ethernet(type=ethernet.ARP_TYPE,
               src=arp_reply.hwsrc,
               dst=arp_reply.hwdst)

  eth_reply.payload = arp_reply


  event.connection.send(of.ofp_packet_out(
      data=eth_reply.pack(),
      action=of.ofp_action_output(port=event.port)))

  log.info("Send ARP reply to host=%s on port=%s on behalf of "
          "ip=%s", arp_reply.protodst, event.port,
          arp_reply.protosrc)


def _handle_arp_reply(event):

  eth_packet = event.parsed
  arp_packet = eth_packet.payload
  log.info("ARP reply: ip=%s destination mac=%s", arp_packet.protosrc,
        arp_packet.hwsrc)

  if str(arp_packet.protosrc) in packet_queue:

    for packet,port in packet_queue[str(arp_packet.protosrc)]:

        packet.dst = arp_packet.hwsrc

        event.connection.send(of.ofp_packet_out(
            data=packet.pack(),
            action=of.ofp_action_output(port=port)))

        print packet,port
        log.info(packet.find("ipv4"))

    del packet_queue[str(arp_packet.protosrc)]


def getMyIP(event, dstip):

  num_of_ports = len(event.connection.features.ports)-1

  for i in range(1,num_of_ports+1):

    my_ip,my_mac = get_MAC_IP(event.connection.dpid,i)

    if prefix_match(dstip,my_ip,32):
      return True

  return False



def _handle_PacketIn (event):
  print "\n\n"
  packet = event.parsed

  if not packet.parsed:
    log.warning("Packet incomplete")  
    return

  log.info(packet)

  id = event.connection.dpid


  #For switch
  if id==11 or id==12:
    log.info("Packet in to switch s%i" %(id-10))

    """
    num_of_ports = len(event.connection.features.ports)-1
    print num_of_ports

    for i in range(1,num_of_ports+1):

      if i==event.port:
        continue

      my_ip,src_mac = get_MAC_IP(id,i)

      e = pkt.ethernet(type=packet.type, src=EthAddr(src_mac), dst=EthAddr("ff:ff:ff:ff:ff:ff"))
      e.payload = packet.find("ethernet").payload

      msg = of.ofp_packet_out(data = e.pack())
      msg.actions.append(of.ofp_action_output(port = i))
      event.connection.send(msg)

      log.info("Broadcasting %s.%i -> %s" %(src_mac, event.ofp.in_port, interface))
      
    """

    msg = of.ofp_packet_out(data = event.ofp)
    msg.actions.append(of.ofp_action_output(port = of.OFPP_ALL))
    event.connection.send(msg)

  else:

    #For router
    log.info("Packet in to router r%i" %(id))

    if packet.find("arp"):

      arp_packet = packet.payload

      #source learning
      _do_source_learning(event)

      # Process ARP request
      if arp_packet.opcode == arp.REQUEST:
        _handle_arp_request(event)
      # Process ARP reply
      elif arp_packet.opcode == arp.REPLY:
        _handle_arp_reply(event)


    # Reply to pings
    elif packet.find("icmp") and getMyIP(event,str(packet.find("ipv4").dstip)):
      # Make the ping reply
      log.info("ICMP Ping message")

      icmp = pkt.icmp()
      icmp.type = pkt.TYPE_ECHO_REPLY
      icmp.payload = packet.find("icmp").payload

      # Make the IP packet around it
      ipp = pkt.ipv4()
      ipp.protocol = ipp.ICMP_PROTOCOL
      ipp.srcip = packet.find("ipv4").dstip
      ipp.dstip = packet.find("ipv4").srcip
      ipp.ttl=64

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
  
    else:

      #For forwarding
      p = packet.find("ipv4")

      #Checking min length of IP Header
      if p.hl<5:
        log.warning("IP header less than minimum length")
        return

      log.info("IP header size good to go!")

      #Check the checksum
      csum = checksum(p)
      if csum!=p.csum:
        log.warning("Checksum not matching")
        return

      log.info("IP checksum perfecto!")

      #Decrement TTL
      p.ttl = p.ttl -1
      

      #Send ICMP Message for TLE
      if p.ttl==0:
        log.warning("Send time limit exceeded ICMP message")
        sendICPMMessage(event,11,0)

      else:
        #Recompute Checksum and set it
        p.csum = checksum(p)

        #Checkup route table
        nexthopip, interface, length = routeChecker(event, str(p.dstip))

        #print nexthopip, interface, length

        #Generate net unreachable ICMP
        if length==0:
          num_of_ports = len(event.connection.features.ports)-1
          #print num_of_ports

          flag=0

          for i in range(1,num_of_ports+1):

            my_ip,src_mac = get_MAC_IP(id,i)
            #print my_ip, p.dstip, src_mac

            if prefix_match(str(p.dstip),my_ip,24):
              flag=1
              break

          if flag==0:
            log.warning("Destination net unreachable ICMP message")
            sendICPMMessage(event,3,0)
          else:
            log.warning("Destination host unreachable ICMP message")
            sendICPMMessage(event,3,1)

        else:
          r_ip,src_mac = get_MAC_IP(id,int(interface[6]))

          e = pkt.ethernet(type=packet.type, src=EthAddr(src_mac), dst=packet.dst)
          e.payload = p
          

          if IPAddr(nexthopip) in ip_to_mac:
            e.dst = ip_to_mac[IPAddr(nexthopip)]

            event.connection.send(of.ofp_packet_out(
                data=e.pack(),
                action=of.ofp_action_output(port=int(interface[6]))))

          else:
            #Enqueue packet
            if nexthopip not in packet_queue:
              packet_queue[nexthopip] = []
            packet_queue[nexthopip].append((e, int(interface[6])))

            get_MAC(nexthopip,id,int(interface[6]), event)



def launch ():
  import pox.log.color
  pox.log.color.launch()
  import pox.log
  pox.log.launch(format="[@@@bold@@@level%(name)-22s@@@reset] " +
                        "@@@bold%(message)s@@@normal")

  core.openflow.addListenerByName("PacketIn", _handle_PacketIn)

  log.info("Pong component running.")