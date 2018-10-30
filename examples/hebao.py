#!/usr/bin/python

"""
linuxrouter.py: Example network with Linux IP router

This example converts a Node into a router using IP forwarding
already built into Linux.

The example topology creates a router and three IP subnets:

    - 192.168.1.0/24 (r0-eth1, IP: 192.168.1.1)
    - 172.16.0.0/12 (r0-eth2, IP: 172.16.0.1)
    - 10.0.0.0/8 (r0-eth3, IP: 10.0.0.1)

Each subnet consists of a single host connected to
a single switch:

    r0-eth1 - s1-eth1 - h1-eth0 (IP: 192.168.1.100)
    r0-eth2 - s2-eth1 - h2-eth0 (IP: 172.16.0.100)
    r0-eth3 - s3-eth1 - h3-eth0 (IP: 10.0.0.100)

The example relies on default routing entries that are
automatically created for each router interface, as well
as 'defaultRoute' parameters for the host interfaces.

Additional routes may be added to the router or hosts by
executing 'ip route' or 'route' commands on the router or hosts.
"""


from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node
from mininet.log import setLogLevel, info
from mininet.cli import CLI


class LinuxRouter( Node ):
    "A Node with IP forwarding enabled."

    def config( self, **params ):
        super( LinuxRouter, self).config( **params )
        # Enable forwarding on the router
        self.cmd( 'sysctl net.ipv4.ip_forward=1' )

    def terminate( self ):
        self.cmd( 'sysctl net.ipv4.ip_forward=0' )
        super( LinuxRouter, self ).terminate()

class NatRouter( LinuxRouter ):

    def config( self, **params ):
        super( NatRouter, self).config( **params )
        # Enable forwarding on the router
        self.cmd( 'iptables -t nat -A POSTROUTING -' )

    def terminate( self ):
        self.cmd( 'sysctl net.ipv4.ip_forward=0' )
        super( NatRouter, self ).terminate()

class NetworkTopo( Topo ):
    "A LinuxRouter connecting three IP subnets"

    def build( self, **_opts ):

        topo = {
            'switches': {
                'office_switch': {},
                'office_vm_switch': {},
                'unicom_switch': {},
            },
            'hosts': {
                'office_air': {
                    'ip': '192.168.122.107/24',
                    'switch': 'office_switch',
                    'routes': [
                        ('0.0.0.0/24', '192.168.222.1'),
                    ],
                },
                'office_printer': {
                    'ip': '192.168.122.127/24',
                    'switch': 'office_switch',
                    'routes': [
                        ('0.0.0.0/24', '192.168.222.1'),
                    ],
                },
                'office_vm_titan': {
                    'ip': '10.168.222.136/24',
                    'switch': 'office_vm_switch',
                    'routes': [
                        ('0.0.0.0/24', '10.168.222.1'),
                    ],
                },
            },
            'routers': {
                'office_router': {
                    'lan': {
                        'ip': '192.168.122.1/24',
                        'switch': 'office_switch',
                    },
                    'wan': {
                        'ip': '192.168.222.100/24',
                        'switch': 'unicom_switch',
                        'nat': True,
                        'routes': [
                            ('0.0.0.0/24', '192.168.222.1'),
                            ('10.168.222.0/24', '192.168.222.90'),
                        ],
                    },
                },
                'kubenode': {
                    'host': {
                        'ip': '192.168.222.171/24',
                        'switch': 'unicom_switch',
                        'routes': [
                            ('0.0.0.0/24', '192.168.222.1')
                        ],
                    },
                    'wan': {
                        'ip': '192.168.222.100/24',
                        'switch': 'unicom_switch',
                    }
                },
                'router222': {
                    'host': {
                        'ip': '192.168.222.90/24',
                        'switch': 'unicom_switch', #
                        'nat': True,
                    },
                    'vm': {
                        'ip': '10.168.222.1/24',
                        'switch': 'office_vm_switch',
                    }
                },
            },
        }
        swi = 0
        for name, sw in topo['switches'].iteritems():
            sw['_name'] = 's%d' % swi
            swi += 1
            self.addSwitch(sw['_name'])
        hi = 0
        for name, h in topo['hosts'].iteritems():
            h['_name'] = 'h%d' % hi
            hi += 1
            self.addHost(h['_name'])
            self.addLink(h['_name'], topo['switches'][h['switch']]['_name'])
        ri = 0
        for name, r in topo['routers'].iteritems():
            r['_name'] = 'r%d' % ri
            ri += 1
            self.addNode(r['_name'], cls=LinuxRouter)
            for portname, port in r.iteritems():
                if portname.startswith('_'):
                    continue
                self.addLink(r['_name'], topo['switches'][port['switch']]['_name'])

        return
        # r0, s0: office router
        r0_ip_lan = '192.168.122.1/24'
        r0_ip_wan = '192.168.222.100/24'
        r0 = self.addNode( 'r0', cls=LinuxRouter, ip=r0_ip_lan )
        s0 = self.addSwitch( 's0' )
        self.addLink( s0, r0, params2={ 'ip': r0_ip_lan } )

        # r1, s1: unicom isp router
        r1_ip_lan = '192.168.222.1/24'
        r1 = self.addNode( 'r1', cls=LinuxRouter, ip=r1_ip_lan )
        s1 = self.addSwitch( 's1' )
        self.addLink( s1, r1, params2={ 'ip': r1_ip_lan } )
        self.addLink( s1, r0, params2={ 'ip': r0_ip_wan } )

        # h0: office notebook
        # h1: office printer
        h0 = self.addHost( 'h0', ip='192.168.122.107/24', defaultRoute='via 192.168.122.1' )
        h1 = self.addHost( 'h1', ip='192.168.122.127/24', defaultRoute='via 192.168.122.1' )
        self.addLink( h0, s0 )
        self.addLink( h1, s0 )

        # r2, s2: kubenode
        r2_ip_host = '192.168.222.171/24'
        r2_ip_vpn = '10.8.0.31/24'
        r2 = self.addNode( 'r2', cls=LinuxRouter, ip=r2_ip_host )
        s2 = self.addSwitch( 's2' )
        self.addLink( s2, r2, params2={ 'ip': r2_ip_host } )
        self.addLink( s1, r2 )

        # r3, s3: router222
        r3_ip_ext = '192.168.222.90/24'
        r3_ip_vm = '10.168.222.0/24'
        r3 = self.addNode( 'r3', cls=LinuxRouter, ip=r3_ip_ext )
        s3 = self.addSwitch( 's3' )
        self.addLink( s3, r3, params2={ 'ip': r3_ip_ext } )
        self.addLink( s2, r3 )

def run():
    "Test linux router"
    topo = NetworkTopo()
    net = Mininet( topo=topo )  # controller is used by s1-s3
    net.start()
    info( '*** Routing Table on Router:\n' )
    info( net[ 'r0' ].cmd( 'route' ) )
    info( net[ 'r1' ].cmd( 'route' ) )
    CLI( net )
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    run()
