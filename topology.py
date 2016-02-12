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
                   ipBase='10.0.0.0/8')

    info( '*** Adding controller\n' )
    c0=net.addController(name='c0',
                      controller=Controller,
                      protocol='tcp',
                      port=6633)

    info( '*** Add switches and routers\n')
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch)
    s2 = net.addSwitch('s2', cls=OVSKernelSwitch)
    r1 = net.addSwitch('r1', cls=OVSKernelSwitch, intfeth0='10.0.1.1', eth2='10.0.2.1')
    r2 = net.addSwitch('r2', cls=OVSKernelSwitch)
    r3 = net.addSwitch('r3', cls=OVSKernelSwitch)
    r4 = net.addSwitch('r4', cls=OVSKernelSwitch)

    info( '*** Add hosts\n')
    h1 = net.addHost('h1', cls=Host, ip='10.0.1.2', defaultRoute=None)
    h2 = net.addHost('h2', cls=Host, ip='10.0.1.3', defaultRoute=None)
    h3 = net.addHost('h3', cls=Host, ip='10.0.2.2', defaultRoute=None)
    h4 = net.addHost('h4', cls=Host, ip='10.0.3.2', defaultRoute=None)
    h5 = net.addHost('h5', cls=Host, ip='10.0.4.2', defaultRoute=None)
    h6 = net.addHost('h6', cls=Host, ip='10.0.4.3', defaultRoute=None)

    info( '*** Add links\n')
    #Hosts to switches and routers
    net.addLink(h1, s1)
    net.addLink(h2, s1)
    net.addLink(h5, s2)
    net.addLink(h6, s2)
    net.addLink(h3, r3)
    net.addLink(h4, r2)

    #Switches and router connections
    net.addLink(s1, r1)
    net.addLink(s2, r4)

    #Router connections
    net.addLink(r1, r3)
    net.addLink(r1, r2)
    net.addLink(r2, r4)
    net.addLink(r3, r4)


    #set ip addresses of the interfaces
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


    info( '*** Starting network\n')
    net.build()
    info( '*** Starting controllers\n')
    for controller in net.controllers:
        controller.start()

    info( '*** Starting switches\n')
    net.get('s1').start([c0])
    net.get('s2').start([c0])
    net.get('r1').start([c0])
    net.get('r2').start([c0])
    net.get('r3').start([c0])
    net.get('r4').start([c0])

    info( '*** Post configure switches and hosts\n')

    CLI(net)
    net.stop()



if __name__ == '__main__':
    setLogLevel( 'info' )
    myNetwork()

