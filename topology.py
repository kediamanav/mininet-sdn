#!/usr/bin/python

from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch
from mininet.node import IVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf
from subprocess import call

def myNetwork():

    net = Mininet( topo=None,
                   build=False,
                   ipBase='10.0.0.0/24')

    info( '*** Adding controller\n' )
    c0=net.addController(name='c0',
                      controller=RemoteController,
                      protocol='tcp',
                      port=6633)

    info( '*** Add switches and routers\n')
    r11 = net.addSwitch('r11', cls=OVSKernelSwitch)
    r12 = net.addSwitch('r12', cls=OVSKernelSwitch)
    r1 = net.addSwitch('r1', cls=OVSKernelSwitch)
    r2 = net.addSwitch('r2', cls=OVSKernelSwitch)
    r3 = net.addSwitch('r3', cls=OVSKernelSwitch)
    r4 = net.addSwitch('r4', cls=OVSKernelSwitch)

    info( '*** Add hosts\n')
    h1 = net.addHost('h1', cls=Host, ip='10.0.1.2', defaultRoute='via 10.0.1.1')
    h2 = net.addHost('h2', cls=Host, ip='10.0.1.3', defaultRoute='via 10.0.1.1')
    h3 = net.addHost('h3', cls=Host, ip='10.0.2.2', defaultRoute='via 10.0.2.1')
    h4 = net.addHost('h4', cls=Host, ip='10.0.3.2', defaultRoute='via 10.0.3.1')
    h5 = net.addHost('h5', cls=Host, ip='10.0.4.2', defaultRoute='via 10.0.4.1')
    h6 = net.addHost('h6', cls=Host, ip='10.0.4.3', defaultRoute='via 10.0.4.1')

    info( '*** Add links\n')
    #Hosts to switches and routers
    net.addLink(h1, r11)
    net.addLink(h2, r11)
    net.addLink(h5, r12)
    net.addLink(h6, r12)
    net.addLink(h3, r3)
    net.addLink(h4, r2)

    #Switches and router connections
    net.addLink(r11, r1)
    net.addLink(r12, r4)

    #Router connections
    net.addLink(r1, r3)
    net.addLink(r1, r2)
    net.addLink(r2, r4)
    net.addLink(r3, r4)

    #set mac addresses of the interfaces
    r1.intf('r1-eth1').setMAC('00:00:00:00:00:11');
    r1.intf('r1-eth2').setMAC('00:00:00:00:00:12');
    r1.intf('r1-eth3').setMAC('00:00:00:00:00:13');
    r2.intf('r2-eth1').setMAC('00:00:00:00:00:21');
    r2.intf('r2-eth2').setMAC('00:00:00:00:00:22');
    r2.intf('r2-eth3').setMAC('00:00:00:00:00:23');
    r3.intf('r3-eth1').setMAC('00:00:00:00:00:31');
    r3.intf('r3-eth2').setMAC('00:00:00:00:00:32');
    r3.intf('r3-eth3').setMAC('00:00:00:00:00:33');
    r4.intf('r4-eth1').setMAC('00:00:00:00:00:41');
    r4.intf('r4-eth2').setMAC('00:00:00:00:00:42');
    r4.intf('r4-eth3').setMAC('00:00:00:00:00:43');

    #set ip addresses of the interfaces
    """
    r1.intf('r1-eth1').setIP('10.0.1.1',24);
    r1.intf('r1-eth2').setIP('192.0.1.1',24);
    r1.intf('r1-eth3').setIP('192.0.2.1',24);
    r2.intf('r2-eth1').setIP('10.0.3.1',24);
    r2.intf('r2-eth2').setIP('192.0.2.2',24);
    r2.intf('r2-eth3').setIP('192.0.3.1',24);
    r3.intf('r3-eth1').setIP('10.0.2.1',24);
    r3.intf('r3-eth2').setIP('192.0.1.2',24);
    r3.intf('r3-eth3').setIP('192.0.4.1',24);
    r4.intf('r4-eth1').setIP('10.0.4.1',24);
    r4.intf('r4-eth2').setIP('192.0.3.2',24);
    r4.intf('r4-eth3').setIP('192.0.4.2',24);
    """



    info( '*** Starting network\n')
    net.build()
    info( '*** Starting controllers\n')
    for controller in net.controllers:
        controller.start()

    info( '*** Starting switches\n')
    net.get('r11').start([c0])
    net.get('r12').start([c0])
    net.get('r1').start([c0])
    net.get('r2').start([c0])
    net.get('r3').start([c0])
    net.get('r4').start([c0])

    info( '*** Post configure switches and hosts\n')

    # delete unnecessary route entry
    h1.cmd("route del -net 10.0.0.0 gw 0.0.0.0 netmask 255.0.0.0 dev h1-eth0")
    h2.cmd("route del -net 10.0.0.0 gw 0.0.0.0 netmask 255.0.0.0 dev h2-eth0")
    h3.cmd("route del -net 10.0.0.0 gw 0.0.0.0 netmask 255.0.0.0 dev h3-eth0")
    h4.cmd("route del -net 10.0.0.0 gw 0.0.0.0 netmask 255.0.0.0 dev h4-eth0")
    h5.cmd("route del -net 10.0.0.0 gw 0.0.0.0 netmask 255.0.0.0 dev h5-eth0")
    h6.cmd("route del -net 10.0.0.0 gw 0.0.0.0 netmask 255.0.0.0 dev h6-eth0")

    CLI(net)
    net.stop()



if __name__ == '__main__':
    setLogLevel( 'info' )
    myNetwork()

