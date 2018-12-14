#!/usr/bin/env python
"""
topofac uses mininet to build a network topology described in json.

TODO

 - make 'iptables' a host-level parameter instead of port-level
 - run commands in tmux
 - initial flow rules for switches
"""

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Host, OVSBridge
from mininet.link import Intf
from mininet.log import setLogLevel
from mininet.cli import CLI

class LinuxHost(Host):

    def config( self, **params ):
        r = super( LinuxHost, self).config( **params )
        self.prependParams(params, 'sysctls', [
            'net.ipv4.icmp_ratelimit=0',
        ])
        self.setParam(r, 'setSysctls', sysctls=params.get('sysctls', []))
        return r

    def prependParams(self, params, key, prepends):
        old = params.get(key)
        if not old:
            params[key] = prepends
        else:
            params[key] = prepends + list(old)

    def setSysctls(self, *sysctls):
        result = ''
        for sysctl in sysctls:
            result += self.cmd('sysctl %s' % sysctl)
        return result


class LinuxRouter(LinuxHost):

    def config( self, **params ):
        self.prependParams(params, 'sysctls', [
            'net.ipv4.ip_forward=1',
            'net.ipv4.conf.all.rp_filter=2',
        ])
        r = super( LinuxRouter, self).config( **params )
        return r


class RoutesIntf(Intf):

    def config(self, **params):
        r = super(RoutesIntf, self).config(**params)
        self.setParam(r, 'setRoutes', routes=params.get('routes'))
        self.setParam(r, 'setIptables', iptables=params.get('iptables'))
        return r

    def setIptables(self, *iptables):
        result = ''
        for cmd in iptables:
            cmd = cmd.replace('<intf>', self.name)
            result += self.cmd(cmd)
        return result

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

    def delete(self):
        super(RoutesIntf, self).delete()
        if not self.node.inNamespace:
            iptables = self.params.get('iptables')
            if iptables:
                for cmd in iptables:
                    cmd = cmd.replace('<intf>', self.name)
                    cmd = cmd.replace(' -A ', ' -D ', 1)
                    self.cmd(cmd)

class NetworkTopo( Topo ):

    def __init__(self, *args, **kwargs):
        self.desc = kwargs.pop('desc')
        super(NetworkTopo, self).__init__(*args, **kwargs)

    def build( self, *args, **kwargs ):
        desc = self.desc

        swi = 0
        for name, sw in desc['switches'].iteritems():
            sw['_name'] = 's%d' % swi
            sw['__name'] = name
            swi += 1
            self.addSwitch(sw['_name'], failMode='standalone')

        hi = 0
        for name, h in desc['hosts'].iteritems():
            h['_name'] = 'h%d' % hi
            h['__name'] = name
            hi += 1
            self.addHost(h['_name'], ip=None, desc=h, routes=h.get('routes'), **h.get('kwargs', {}))
            self.addLinks(h)

        ri = 0
        for name, r in desc['routers'].iteritems():
            r['_name'] = 'r%d' % ri
            r['__name'] = name
            ri += 1
            self.addNode(r['_name'], cls=LinuxRouter, ip=None, sysctls=r.get('sysctls'))
            self.addLinks(r)

    def addLinks(self, desc):
        for portname, port in desc['ports'].iteritems():
            switch = self.desc['switches'][port['switch']]
            params1 = {
                'ip': port['ip'],
                'routes': port.get('routes'),
                'iptables': port.get('iptables'),
            }
            self.addLink(desc['_name'], switch['_name'], params1=params1)

def run():
    from topodesc import topodesc
    topo = NetworkTopo(desc=topodesc)
    # two ways to make the ovs switch operate in standalone fail_mode.
    #
    #  - use switch=OVSBridge
    #  - use controller=None or controller=[]
    #
    net = Mininet( topo=topo, switch=OVSBridge, host=LinuxHost, intf=RoutesIntf, listenPort=6654)
    net.start()
    CLI( net )
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    run()
