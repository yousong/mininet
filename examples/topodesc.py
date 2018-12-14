topodesc = {
    'switches': {
        'office_switch': {},
        'office_vm_switch': {},
        'unicom_switch': {},
        'unicom_wan_switch': {},
        'openvpn_switch': {},
        'east_switch0': {},
        'east_switch1': {},
        'east_switch2': {},
        'east_switch3': {},
        'east_switch4': {},
        'east_switch5': {},
    },
    'hosts': {
        'office_air': {
            'ports': {
                'eth0': {
                    'ip': '192.168.122.107/24',
                    'switch': 'office_switch',
                    'routes': [
                        ('0.0.0.0/0', '192.168.122.1'),
                    ],
                },
            },
        },
        'office_vm_titan': {
            'ports': {
                'eth0': {
                    'ip': '10.168.222.136/24',
                    'switch': 'office_vm_switch',
                    'routes': [
                        ('0.0.0.0/0', '10.168.222.1'),
                    ],
                },
            },
        },
        'unicom_gateway': {
            'kwargs': {
                'inNamespace': False,
            },
            'ports': {
                'eth0': {
                    'ip': '198.18.64.1/24',
                    'switch': 'unicom_wan_switch',
                    'iptables': [
                        'iptables -t nat -A PREROUTING -i <intf> -d 198.18.64.1 -p tcp -m multiport --dports 8080,6379 -j DNAT --to-destination 10.168.26.196',
                        'iptables -t nat -A POSTROUTING -s 198.18.64.0/24 -o br0 -j MASQUERADE',
                    ],
                },
            },
        },
        'home_yousong': {
            'ports': {
                'eth0': {
                    'ip': '10.8.0.36/24',
                    'switch': 'openvpn_switch',
                    'routes': [
                        ('192.168.222.0/24', '10.8.0.31'),
                        ('192.168.122.0/24', '10.8.0.2'),
                        ('10.168.222.0/24', '10.8.0.1'),
                        ('0.0.0.0/0', '10.8.0.1'),
                    ],
                },
            },
        },
        'west222': {
            'ports': {
                'eth0': {
                    'ip': '192.168.222.99/24',
                    'switch': 'unicom_switch',
                    'routes': [
                        ('192.168.122.0/24', '192.168.222.100'),
                        ('10.168.222.0/24', '192.168.222.90'),
                        ('172.16.0.0/16', '192.168.222.171'),
                        ('10.8.0.0/24', '192.168.222.171'),
                        ('0.0.0.0/0', '192.168.222.1'),
                    ],
                },
            },
        },
        'west19818': {
            'ports': {
                'eth0': {
                    'ip': '198.18.64.99/24',
                    'switch': 'unicom_wan_switch',
                    'routes': [
                        ('192.168.122.0/24', '192.168.222.100'),
                        ('10.168.222.0/24', '192.168.222.90'),
                        ('172.16.0.0/16', '198.18.64.3'),
                        ('10.8.0.0/24', '198.18.64.3'),
                        ('0.0.0.0/0', '198.18.64.1'),
                    ],
                },
            },
        },
        'east1': {
            'ports': {
                'eth0': {
                    'ip': '172.16.1.99/24',
                    'switch': 'east_switch1',
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
        },
        'east2': {
            'ports': {
                'eth0': {
                    'ip': '172.16.2.99/24',
                    'switch': 'east_switch2',
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
        },
        'east3': {
            'ports': {
                'eth0': {
                    'ip': '172.16.3.99/24',
                    'switch': 'east_switch3',
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
        },
        'east4': {
            'ports': {
                'eth0': {
                    'ip': '172.16.4.99/24',
                    'switch': 'east_switch4',
                    'routes': [
                        ('0.0.0.0/0', '172.16.4.1'),
                    ],
                },
            },
        },
        'east5': {
            'ports': {
                'eth0': {
                    'ip': '172.16.5.99/24',
                    'switch': 'east_switch5',
                    'routes': [
                        ('0.0.0.0/0', '172.16.5.1'),
                    ],
                },
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
                'east_core': {
                    'ip': '172.16.0.1/24',
                    'switch': 'east_switch0',
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
        'east1': {
            'ports': {
                'east0': {
                    'ip': '172.16.0.2/24',
                    'switch': 'east_switch0',
                    'routes': [
                        ('172.16.2.0/24', '172.16.0.3'),
                        ('172.16.4.0/24', '172.16.0.4'),
                        ('0.0.0.0/0', '172.16.0.1'),
                    ],
                },
                'east1': {
                    'ip': '172.16.1.1/24',
                    'switch': 'east_switch1',
                    'routes': [
                        ('172.16.3.0/24', '172.16.1.2'),
                        ('172.16.5.0/24', '172.16.1.2'),
                    ],
                },
            },
        },
        'eastx2': {
            'ports': {
                'east1': {
                    'ip': '172.16.1.2/24',
                    'switch': 'east_switch1',
                    'routes': [
                        ('0.0.0.0/0', '172.16.1.1'),
                    ],
                },
                'east3': {
                    'ip': '172.16.3.2/24',
                    'switch': 'east_switch3',
                    'routes': [
                        ('172.16.2.0/24', '172.16.3.3'),
                        ('172.16.5.0/24', '172.16.3.1'),
                    ],
                },
            },
        },
        'eastx3': {
            'ports': {
                'east2': {
                    'ip': '172.16.2.2/24',
                    'switch': 'east_switch2',
                    'routes': [
                        ('172.16.0.0/24', '172.16.2.1'),
                        ('172.16.1.0/24', '172.16.2.1'),
                        ('172.16.4.0/24', '172.16.2.1'),
                        ('0.0.0.0/0', '172.16.2.1'),
                    ],
                },
                'east3': {
                    'ip': '172.16.3.3/24',
                    'switch': 'east_switch3',
                    'routes': [
                        ('172.16.5.0/24', '172.16.3.1'),
                    ],
                },
            },
        },
        'east3': {
            'ports': {
                'east3': {
                    'ip': '172.16.3.1/24',
                    'switch': 'east_switch3',
                    'routes': [
                        ('172.16.0.0/24', '172.16.3.2'),
                        ('172.16.1.0/24', '172.16.3.2'),
                        ('172.16.2.0/24', '172.16.3.3'),
                        ('172.16.4.0/24', '172.16.3.3'),
                        ('0.0.0.0/0', '172.16.3.3'),
                    ],
                },
                'east5': {
                    'ip': '172.16.5.1/24',
                    'switch': 'east_switch5',
                },
            },
        },
        'east2': {
            'ports': {
                'east0': {
                    'ip': '172.16.0.3/24',
                    'switch': 'east_switch0',
                    'routes': [
                        ('172.16.1.0/24', '172.16.0.2'),
                        ('172.16.4.0/24', '172.16.0.4'),
                        ('0.0.0.0/0', '172.16.0.1'),
                    ],
                },
                'east2': {
                    'ip': '172.16.2.1/24',
                    'switch': 'east_switch2',
                    'routes': [
                        ('172.16.3.0/24', '172.16.2.2'),
                        ('172.16.5.0/24', '172.16.2.2'),
                    ],
                },
            },
        },
        'east4': {
            'ports': {
                'east0': {
                    'ip': '172.16.0.4/24',
                    'switch': 'east_switch0',
                    'routes': [
                        ('172.16.1.0/24', '172.16.0.2'),
                        ('172.16.2.0/24', '172.16.0.3'),
                        ('172.16.3.0/24', '172.16.0.3'),
                        ('172.16.5.0/24', '172.16.0.2'),
                        ('0.0.0.0/0', '172.16.0.1'),
                    ],
                },
                'east4': {
                    'ip': '172.16.4.1/24',
                    'switch': 'east_switch4',
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
