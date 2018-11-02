#!/usr/bin/python

import json

import mininet
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node, Host
from mininet.link import Intf
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.util import quietRun

class LinuxHost(Host):

    def config( self, **params ):
        r = super( LinuxHost, self).config( **params )
        self.setParam(r, 'setSysctls', sysctls=params.get('sysctls'))
        self.setParam(r, 'setSysctls', sysctls=['net.ipv4.icmp_ratelimit=0'])
        self.setParam(r, 'setSysctls', sysctls=['net.ipv4.conf.all.rp_filter=2'])
        return r

    def setSysctls(self, *sysctls):
        result = ''
        for sysctl in sysctls:
            result += self.cmd('sysctl %s' % sysctl)
        return result

    def runAgent(self):
        desc = self.params.get('desc', {})
        if not desc.get('runAgent', True):
            return
        __name = desc.get('__name', self.name)
        __ip = desc['ip'].split('/')[0]
        __switch = desc.get('switch', 'DUM_SWITCH')

        __monenv = [
            'MON_MASTER_HOST=198.18.64.1',
            'MON_MASTER_PORT=8080',
            'MON_WHO_AM_I={name}',
            'MON_WHO_AM_I_IP=' + __ip,
            'MON_WHO_AM_I_NETCARD=' + self.intf().name,
            'MON_WHO_AM_I_SWITCH=' + __switch,
        ]
        __monenv = ';'.join('export ' + var for var in __monenv).format(name=__name)

        def run(sess, wdir, cmd):
            wndcmd = [
                'tmux', 'new-window', '-d', '-t', sess, "-n", __name, "-c", wdir,
                'mnexec', '-a', str(self.pid),
                'bash', '-c',
                '{__monenv}; {cmd}; PS1="{name}> " bash --rcfile /dev/null'.format(__monenv=__monenv, cmd=cmd, name=__name),
            ]
            return quietRun(wndcmd)

        def runRegister(wdir, cmd):
            onecmd = [
                'mnexec', '-a', str(self.pid),
                'bash', '-c',
                '{__monenv}; cd {wdir}; {cmd};'.format(__monenv=__monenv, wdir=wdir, cmd=cmd),
            ]
            return quietRun(onecmd)

        runRegister('/opt/sys_net_monitor/agent/tcp_ping', 'python inner_monitor.py -r same')
        run('hebping', '/opt/sys_net_monitor/agent/tcp_ping', 'celery worker -A inner_monitor -l info -Q {name}_run -n {name}_run -c 1'.format(name=__name))
        run('hebtrace', '/opt/sys_net_monitor/agent/trace', 'celery worker -A inner_monitor -l info -Q {name}_trace -n {name}_trace -c 1'.format(name=__name))


class LinuxRouter(LinuxHost):

    def config( self, **params ):
        r = super( LinuxRouter, self).config( **params )
        # Enable forwarding on the router
        self.setParam(r, 'setSysctls', sysctls=['net.ipv4.ip_forward=1'])
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

    def build( self, **_opts ):

        topo = {
            'switches': {
                'office_switch': {},
                'office_vm_switch': {},
                'unicom_switch': {},
                'unicom_wan_switch': {},
                'openvpn_switch': {},
                'right_switch0': {},
                'right_switch1': {},
                'right_switch2': {},
                'right_switch3': {},
                'right_switch4': {},
                'right_switch5': {},
            },
            'hosts': {
                'office_air': {
                    'ip': '192.168.122.107/24',
                    'switch': 'office_switch',
                    'link_params': {
                        'routes': [
                            ('0.0.0.0/0', '192.168.122.1'),
                        ],
                    },
                },
                'office_vm_titan': {
                    'ip': '10.168.222.136/24',
                    'switch': 'office_vm_switch',
                    'link_params': {
                        'routes': [
                            ('0.0.0.0/0', '10.168.222.1'),
                        ],
                    },
                },
                'unicom_gateway': {
                    'ip': '198.18.64.1/24',
                    'switch': 'unicom_wan_switch',
                    'runAgent': False,
                    'host_params': {
                        'inNamespace': False,
                    },
                    'link_params': {
                        'iptables': [
                            'iptables -t nat -A PREROUTING -i <intf> -d 198.18.64.1 -p tcp -m multiport --dports 8080,6379 -j DNAT --to-destination 10.168.26.196',
                            'iptables -t nat -A POSTROUTING -s 198.18.64.0/24 -o br0 -j MASQUERADE',
                        ],
                        'routes': [
                            ('0.0.0.0/0', '198.18.64.1'),
                        ],
                    },
                },
                'home_yousong': {
                    'ip': '10.8.0.36/24',
                    'switch': 'openvpn_switch',
                    'link_params': {
                        'routes': [
                            ('192.168.222.0/24', '10.8.0.31'),
                            ('192.168.122.0/24', '10.8.0.2'),
                            ('10.168.222.0/24', '10.8.0.1'),
                            ('0.0.0.0/0', '10.8.0.1'),
                        ],
                    },
                },
                'west222': {
                    'ip': '192.168.222.99/24',
                    'switch': 'unicom_switch',
                    'link_params': {
                        'routes': [
                            ('192.168.122.0/24', '192.168.222.100'),
                            ('10.168.222.0/24', '192.168.222.90'),
                            ('172.16.0.0/16', '192.168.222.171'),
                            ('10.8.0.0/24', '192.168.222.171'),
                            ('0.0.0.0/0', '192.168.222.1'),
                        ],
                    },
                },
                'east1': {
                    'ip': '172.16.1.99/24',
                    'switch': 'right_switch1',
                    'link_params': {
                        'routes': [
                            ('172.16.0.0/24', '172.16.1.1'),
                            ('172.16.2.0/24', '172.16.1.2'),
                            ('172.16.3.0/24', '172.16.1.2'),
                            ('172.16.4.0/24', '172.16.1.1'),
                            ('172.16.5.0/24', '172.16.1.2'),
                            ('0.0.0.0/0', '172.16.1.1'),
                        ],
                    },
                },
                'east2': {
                    'ip': '172.16.2.99/24',
                    'switch': 'right_switch2',
                    'link_params': {
                        'routes': [
                            ('172.16.0.0/24', '172.16.2.1'),
                            ('172.16.1.0/24', '172.16.2.2'),
                            ('172.16.3.0/24', '172.16.2.2'),
                            ('172.16.4.0/24', '172.16.2.1'),
                            ('172.16.5.0/24', '172.16.2.2'),
                            ('0.0.0.0/0', '172.16.2.1'),
                        ],
                    },
                },
                'east3': {
                    'ip': '172.16.3.99/24',
                    'switch': 'right_switch3',
                    'link_params': {
                        'routes': [
                            ('172.16.0.0/24', '172.16.3.2'),
                            ('172.16.1.0/24', '172.16.3.2'),
                            ('172.16.3.0/24', '172.16.3.3'),
                            ('172.16.4.0/24', '172.16.3.2'),
                            ('172.16.5.0/24', '172.16.3.1'),
                            ('0.0.0.0/0', '172.16.3.3'),
                        ],
                    },
                },
                'east4': {
                    'ip': '172.16.4.99/24',
                    'switch': 'right_switch4',
                    'link_params': {
                        'routes': [
                            ('0.0.0.0/0', '172.16.4.1'),
                        ],
                    },
                },
                'east5': {
                    'ip': '172.16.5.99/24',
                    'switch': 'right_switch5',
                    'link_params': {
                        'routes': [
                            ('0.0.0.0/0', '172.16.5.1'),
                        ],
                    },
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
                            'routes': [
                                ('10.168.222.0/24', '192.168.222.90'),
                                ('0.0.0.0/0', '192.168.222.1'),
                            ],
                            'iptables': [
                                'iptables -t nat -A POSTROUTING -o <intf> -j MASQUERADE',
                            ],
                        },
                        'openvpn': {
                            'ip': '10.8.0.2/24',
                            'switch': 'openvpn_switch',
                            'routes': [
                                ('172.16.0.0/16', '10.8.0.1'),
                            ],
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
                                ('172.16.0.0/16', '10.8.0.1'),
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
                                ('172.16.0.0/16', '192.168.222.171'),
                                ('192.168.122.0/24', '192.168.222.171'),
                                ('0.0.0.0/0', '192.168.222.1'),
                            ],
                            'iptables': [
                                'iptables -t nat -A POSTROUTING -o <intf> -d 10.0.0.0/8 -j RETURN',
                                'iptables -t nat -A POSTROUTING -o <intf> -d 172.16.0.0/12 -j RETURN',
                                'iptables -t nat -A POSTROUTING -o <intf> -d 192.168.0.0/16 -j RETURN',
                                'iptables -t nat -A POSTROUTING -o <intf> -j MASQUERADE',
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
                        'wan': {
                            'ip': '198.18.64.3/24',
                            'switch': 'unicom_wan_switch', #
                            'routes': [
                                ('0.0.0.0/0', '198.18.64.1'),
                            ],
                            'iptables': [
                                'iptables -t nat -A POSTROUTING -o <intf> -d 10.0.0.0/8 -j RETURN',
                                'iptables -t nat -A POSTROUTING -o <intf> -d 172.16.0.0/12 -j RETURN',
                                'iptables -t nat -A POSTROUTING -o <intf> -d 192.168.0.0/16 -j RETURN',
                                'iptables -t nat -A POSTROUTING -o <intf> -j MASQUERADE',
                            ],
                        },
                        'right_core': {
                            'ip': '172.16.0.1/24',
                            'switch': 'right_switch0',
                            'routes': [
                                ('172.16.1.0/24', '172.16.0.2'),
                                ('172.16.2.0/24', '172.16.0.3'),
                                ('172.16.3.0/24', '172.16.0.3'),
                                ('172.16.4.0/24', '172.16.0.4'),
                                ('172.16.5.0/24', '172.16.0.2'),
                            ],
                        },
                    },
                },
                'right1': {
                    'ports': {
                        'right0': {
                            'ip': '172.16.0.2/24',
                            'switch': 'right_switch0',
                            'routes': [
                                ('172.16.2.0/24', '172.16.0.3'),
                                ('172.16.4.0/24', '172.16.0.4'),
                                ('0.0.0.0/0', '172.16.0.1'),
                            ],
                        },
                        'right1': {
                            'ip': '172.16.1.1/24',
                            'switch': 'right_switch1',
                            'routes': [
                                ('172.16.3.0/24', '172.16.1.2'),
                                ('172.16.5.0/24', '172.16.1.2'),
                            ],
                        },
                    },
                },
                'rightx2': {
                    'ports': {
                        'right1': {
                            'ip': '172.16.1.2/24',
                            'switch': 'right_switch1',
                            'routes': [
                                ('0.0.0.0/0', '172.16.1.1'),
                            ],
                        },
                        'right3': {
                            'ip': '172.16.3.2/24',
                            'switch': 'right_switch3',
                            'routes': [
                                ('172.16.2.0/24', '172.16.3.3'),
                                ('172.16.5.0/24', '172.16.3.1'),
                            ],
                        },
                    },
                },
                'rightx3': {
                    'ports': {
                        'right2': {
                            'ip': '172.16.2.2/24',
                            'switch': 'right_switch2',
                            'routes': [
                                ('172.16.0.0/24', '172.16.2.1'),
                                ('172.16.1.0/24', '172.16.2.1'),
                                ('172.16.4.0/24', '172.16.2.1'),
                                ('0.0.0.0/0', '172.16.2.1'),
                            ],
                        },
                        'right3': {
                            'ip': '172.16.3.3/24',
                            'switch': 'right_switch3',
                            'routes': [
                                ('172.16.5.0/24', '172.16.3.1'),
                            ],
                        },
                    },
                },
                'right3': {
                    'ports': {
                        'right3': {
                            'ip': '172.16.3.1/24',
                            'switch': 'right_switch3',
                            'routes': [
                                ('172.16.0.0/24', '172.16.3.2'),
                                ('172.16.1.0/24', '172.16.3.2'),
                                ('172.16.2.0/24', '172.16.3.3'),
                                ('172.16.4.0/24', '172.16.3.3'),
                                ('0.0.0.0/0', '172.16.3.3'),
                            ],
                        },
                        'right5': {
                            'ip': '172.16.5.1/24',
                            'switch': 'right_switch5',
                        },
                    },
                },
                'right2': {
                    'ports': {
                        'right0': {
                            'ip': '172.16.0.3/24',
                            'switch': 'right_switch0',
                            'routes': [
                                ('172.16.1.0/24', '172.16.0.2'),
                                ('172.16.4.0/24', '172.16.0.4'),
                                ('0.0.0.0/0', '172.16.0.1'),
                            ],
                        },
                        'right2': {
                            'ip': '172.16.2.1/24',
                            'switch': 'right_switch2',
                            'routes': [
                                ('172.16.3.0/24', '172.16.2.2'),
                                ('172.16.5.0/24', '172.16.2.2'),
                            ],
                        },
                    },
                },
                'right4': {
                    'ports': {
                        'right0': {
                            'ip': '172.16.0.4/24',
                            'switch': 'right_switch0',
                            'routes': [
                                ('172.16.1.0/24', '172.16.0.2'),
                                ('172.16.2.0/24', '172.16.0.3'),
                                ('172.16.3.0/24', '172.16.0.3'),
                                ('172.16.5.0/24', '172.16.0.2'),
                                ('0.0.0.0/0', '172.16.0.1'),
                            ],
                        },
                        'right4': {
                            'ip': '172.16.4.1/24',
                            'switch': 'right_switch4',
                        },
                    },
                },
                'routerunicom': {
                    'ports': {
                        'lan': {
                            'ip': '192.168.222.1/24',
                            'switch': 'unicom_switch',
                        },
                        'wan': {
                            'ip': '198.18.64.2/24',
                            'switch': 'unicom_wan_switch',
                            'routes': [
                                ('0.0.0.0/0', '198.18.64.1'),
                            ],
                            'iptables': [
                                'iptables -t nat -A POSTROUTING -o <intf> -d 10.0.0.0/8 -j RETURN',
                                'iptables -t nat -A POSTROUTING -o <intf> -d 172.16.0.0/12 -j RETURN',
                                'iptables -t nat -A POSTROUTING -o <intf> -d 192.168.0.0/16 -j RETURN',
                                'iptables -t nat -A POSTROUTING -o <intf> -j MASQUERADE',
                            ],
                        },
                    },
                },
            },
        }
        swi = 0
        for name, sw in topo['switches'].iteritems():
            sw['_name'] = 's%d' % swi
            sw['__name'] = name
            swi += 1
            self.addSwitch(sw['_name'], failMode='standalone')
        hi = 0
        for name, h in topo['hosts'].iteritems():
            h['_name'] = 'h%d' % hi
            h['__name'] = name
            hi += 1
            self.addHost(h['_name'], ip=None, desc=h, routes=h.get('routes'), **h.get('host_params', {}))
            params1={
                'ip': h['ip'],
            }
            params1.update(h.get('link_params', {}))
            self.addLink(h['_name'], topo['switches'][h['switch']]['_name'], params1=params1)
        ri = 0
        for name, r in topo['routers'].iteritems():
            r['_name'] = 'r%d' % ri
            r['__name'] = name
            ri += 1
            self.addNode(r['_name'], cls=LinuxRouter, ip=None, sysctls=r.get('sysctls'))
            for portname, port in r['ports'].iteritems():
                params1 = {
                    'ip': port['ip'],
                    'routes': port.get('routes'),
                    'iptables': port.get('iptables'),
                }
                self.addLink(r['_name'], topo['switches'][port['switch']]['_name'], params1=params1)

        with open('devenv.json', 'w') as fout:
            fout.write(json.dumps(topo, indent=2))


def run():
    "Test linux router"
    topo = NetworkTopo()
    net = Mininet( topo=topo, host=LinuxHost, intf=RoutesIntf, listenPort=6654, controller=[])
    net.start()
    quietRun('tmux new-session -d -s hebtrace')
    quietRun('tmux new-session -d -s hebping')
    for h in net.values():
        if h.__class__ == LinuxHost:
            h.runAgent()
    CLI( net )
    net.stop()
    quietRun('tmux kill-session -t hebtrace')
    quietRun('tmux kill-session -t hebping')

if __name__ == '__main__':
    setLogLevel( 'info' )
    run()
