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


import json

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node
from mininet.link import Intf
from mininet.log import setLogLevel, info
from mininet.cli import CLI

class LinuxHost(Node):

    def config( self, **params ):
        r = super( LinuxHost, self).config( **params )
        self.setParam(r, 'setSysctls', sysctls=params.get('sysctls'))
        self.setParam(r, 'setSysctls', sysctls=params.get('sysctls'))
        return r

    def setSysctls(self, *sysctls):
        result = ''
        for sysctl in sysctls:
            result += self.cmd('sysctl %s' % sysctl)
        return result


class LinuxRouter(LinuxHost):
    "A Node with IP forwarding enabled."

    def config( self, **params ):
        r = super( LinuxRouter, self).config( **params )
        # Enable forwarding on the router
        self.setParam(r, 'setSysctls', sysctls=['net.ipv4.ip_forward=1'])
        return r

class RoutesIntf(Intf):

    def config(self, **params):
        r = super(RoutesIntf, self).config(**params)
        self.setParam(r, 'setRoutes', routes=params.get('routes'))
        self.setParam(r, 'setMasquerade', routes=params.get('masquerade'))
        return r

    def setMasquerade(self, masquerade):
        if masquerade:
            return self.cmd('iptables -t nat -A POSTROUTING -o %s -j MASQUERADE' % self.name)

    def setRoutes(self, *routes):
        result = ''
        for route in routes:
            net = route[0]
            cmd = 'ip route add ' + net
            if len(route) >= 2:
                gw = route[1]
                cmd += ' via ' + gw
            cmd += ' dev ' + self.name
            result += self.cmd(cmd)
        return result

class NetworkTopo( Topo ):
    "A LinuxRouter connecting three IP subnets"

    def build( self, **_opts ):

        topo = {
            'switches': {
                'office_switch': {},
                'office_vm_switch': {},
                'unicom_switch': {},
                'openvpn_switch': {},
            },
            'hosts': {
                'office_air': {
                    'ip': '192.168.122.107/24',
                    'switch': 'office_switch',
                    'routes': [
                        ('0.0.0.0/0', '192.168.122.1'),
                    ],
                },
                'office_printer': {
                    'ip': '192.168.122.127/24',
                    'switch': 'office_switch',
                    'routes': [
                        ('0.0.0.0/0', '192.168.122.1'),
                    ],
                },
                'office_vm_titan': {
                    'ip': '10.168.222.136/24',
                    'switch': 'office_vm_switch',
                    'routes': [
                        ('0.0.0.0/0', '10.168.222.1'),
                    ],
                },
                'home_yousong': {
                    'ip': '10.8.0.36/24',
                    'switch': 'openvpn_switch',
                    'routes': [
                        ('192.168.222.0/24', '10.8.0.31'),
                        ('192.168.122.0/24', '10.8.0.2'),
                        ('10.168.222.0/24', '10.8.0.1'),
                    ],
                },
            },
            'routers': {
                'office_router': {
                    'ports': {
                        'lan': {
                            'ip': '192.168.122.1/24',
                            'switch': 'office_switch',
                        },
                        'wan': {
                            'ip': '192.168.222.100/24',
                            'switch': 'unicom_switch',
                            'masquerade': True,
                            'routes': [
                                ('10.168.222.0/24', '192.168.222.90'),
                                ('0.0.0.0/0', '192.168.222.1'),
                            ],
                        },
                        'openvpn': {
                            'ip': '10.8.0.2/24',
                            'switch': 'openvpn_switch',
                        },
                    },
                    'sysctls': [
                        'net.ipv4.conf.all.rp_filter=2',
                    ],
                },
                'kubenode': {
                    'ports': {
                        'host': {
                            'ip': '192.168.222.171/24',
                            'switch': 'unicom_switch',
                            'routes': [
                                ('10.168.222.0/24', '192.168.222.90'),
                                ('0.0.0.0/0', '192.168.222.1'),
                            ],
                        },
                        'openvpn': {
                            'ip': '10.8.0.31/24',
                            'switch': 'openvpn_switch',
                            'routes': [
                                ('192.168.122.0/24', '10.8.0.2'),
                            ],
                        },
                    },
                },
                'router222': {
                    'ports': {
                        'host': {
                            'ip': '192.168.222.90/24',
                            'switch': 'unicom_switch', #
                            'routes': [
                                ('10.8.0.0/24', '192.168.222.171'),
                                ('192.168.122.0/24', '192.168.222.171'),
                                ('0.0.0.0/0', '192.168.222.1'),
                            ],
                        },
                        'vm': {
                            'ip': '10.168.222.1/24',
                            'switch': 'office_vm_switch',
                        },
                    },
                },
                'routervpn': {
                    'ports': {
                        'vpn': {
                            'ip': '10.8.0.1/24',
                            'switch': 'openvpn_switch', #
                            'routes': [
                                ('192.168.122.0/24', '10.8.0.2'),
                                ('192.168.222.0/24', '10.8.0.31'),
                                ('10.168.222.0/24', '10.8.0.31'),
                            ],
                        },
                    },
                },
            },
        }
        swi = 0
        for name, sw in topo['switches'].iteritems():
            sw['_name'] = 's%d' % swi
            swi += 1
            self.addSwitch(sw['_name'], failMode='standalone')
        hi = 0
        for name, h in topo['hosts'].iteritems():
            h['_name'] = 'h%d' % hi
            hi += 1
            self.addHost(h['_name'], ip=None, routes=h.get('routes'))
            params1={
                'ip': h['ip'],
                'routes': h.get('routes'),
            }
            self.addLink(h['_name'], topo['switches'][h['switch']]['_name'], params1=params1)
        ri = 0
        for name, r in topo['routers'].iteritems():
            r['_name'] = 'r%d' % ri
            ri += 1
            self.addNode(r['_name'], cls=LinuxRouter, ip=None, sysctls=r.get('sysctls'))
            for portname, port in r['ports'].iteritems():
                params1 = {
                    'ip': port['ip'],
                    'routes': port.get('routes'),
                    'masquerade': port.get('masquerade'),
                }
                self.addLink(r['_name'], topo['switches'][port['switch']]['_name'], params1=params1)

        with open('devenv.json', 'w') as fout:
            fout.write(json.dumps(topo, indent=2))


def run():
    "Test linux router"
    topo = NetworkTopo()
    net = Mininet( topo=topo, intf=RoutesIntf, listenPort=6654, controller=[])
    net.start()
    info( '*** Routing Table on Router:\n' )
    info( net[ 'r0' ].cmd( 'route -n' ) )
    info( net[ 'r1' ].cmd( 'route -n' ) )
    CLI( net )
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    run()
