"""
"""

import json
import re
import glob
import os
import alexlibs.cdp as cdp
from ciscoconfparse import CiscoConfParse
from netaddr import IPAddress, IPNetwork

_KEYS_L3_INT = {
    'name': r'^interface',
    'desc': r'^\s*description',
    'subint': r'^interface\s*[^\.]*.(\d*)$',
    'vrf': r'vrf\s*forwarding',
    'status': r'\s*(shutdown)',
    'access_list': r'\s*ip\s*access-group',
    'ipv4': r'ip\s*address\s*(\d*\.\d*\.\d*\.\d*\s*\d*\.\d*\.\d*\.\d*)\s*$',
    'ipv4_sec': r'ip\s*address\s*(\d*\.\d*\.\d*\.\d*\s*\d*\.\d*\.\d*\.\d*)\s*secondary',
    'hsrp_num': r'^\s*standby\s*(\d*)\s*ip\s*(.*)',
    'hsrp_ip': r'^\s*standby\s*\d*\s*ip\s*(.*)',
    'hsrp_pri': r'^\s*standby\s*\d*\s*priority\s*(.*)',
    'ip_helper': r'^\s*ip helper-address',
}

_KEYS_L2_INT = {
    'name': r'^interface',
    'desc': r'^\s*description',
    'mode': r'^\s*switchport\s*mode',
    'status': r'^\s*(shutdown)',
    'access_vlan': r'^\s*switchport\s*access\s*vlan',
    'trunk_allowed': r'^\s*switchport\s*trunk\s*allowed\s*vlan',
    'channel_group': r'^\s*channel-group\s*(\d*)',
    'channel_mode': r'^\s*channel-group\s*\d*',
    'span_tree': r'^\s*spanning-tree',
    'speed': r'^\s*speed',
}

_KEYS_VLAN = {
    'vlan': r'^vlan',
    'name': r'^\s*name',
}


class L3Interface():
    """[Class L3Interface]

    Returns:
        [type] -- [description]
    """

    def __init__(self):
        self.name = ""
        self.desc = ""
        self.subint = ""
        self.status = ""
        self.ipv4 = ""
        self.ipv4_sec = ""
        self.net = ""
        self.hsrp_num = ""
        self.hsrp_ip = ""
        self.hsrp_pri = ""
        self.ip_helper = ""
        self.access_list = ""
        self.vrf = ""

    @property
    def dict(self):
        ipv4_w_prf = f'{self.ipv4.split()[0].strip()}/{IPAddress(self.ipv4.split()[1].strip()).netmask_bits()}'
        resp = {
            'name': self.name,
            'desc': self.desc,
            'subint': self.subint,
            'status': self.status,
            'ipv4': f'{ipv4_w_prf}',
            'ipv4_net': f'{IPNetwork(ipv4_w_prf).network}/{IPAddress(self.ipv4.split()[1].strip()).netmask_bits()}',
            'ipv4_sec': self.ipv4_sec,
            'net': self.net,
            'hsrp_num': self.hsrp_num,
            'hsrp_ip': self.hsrp_ip,
            'hsrp_pri': self.hsrp_pri,
            'ip_helper': self.ip_helper,
            'access_list': self.access_list,
            'vrf': self.vrf,

        }
        return resp

    @property
    def json(self):
        return json.dumps(self.dict)

    @staticmethod
    def _extract_keys(pattern, string):
        res = re.search(r'{}\s?(.*)'.format(pattern), string)
        if res:
            return res.group(1).split(',')[0].strip()
        return ""

    def get_all_properties(self, block):
        for key, val in _KEYS_L3_INT.items():
            ret = self._extract_keys(val, block)
            if ret is not "":
                # print(f'Key: {key:15s} Val: {ret}')
                if self.__dict__[key] is "":
                    self.__dict__[key] = ret
                else:
                    self.__dict__[key] += f', {ret}'


class L2Interface():
    """[Class L3Interface]

    Returns:
        [type] -- [description]
    """

    def __init__(self):
        self.name = None
        self.desc = None
        self.mode = None
        self.status = None
        self.access_vlan = None
        self.trunk_allowed = None
        self.channel_group = None
        self.channel_mode = None
        self.span_tree = None
        self.speed = None

    @property
    def dict(self):
        resp = {
            'name': self.name,
            'desc': self.desc,
            'mode': self.mode,
            'status': self.status,
            'access_vlan': self.access_vlan,
            'trunk_allowed': self.trunk_allowed,
            'channel_group': self.channel_group,
            'channel_mode': self.channel_mode,
            'span_tree': self.span_tree,
            'speed': self.speed,
        }
        return resp

    @property
    def json(self):
        return json.dumps(self.dict)

    @staticmethod
    def _extract_keys(pattern, string):
        res = re.search(r'{}\s?(.*)'.format(pattern), string, re.DOTALL)
        if res:
            return res.group(1).strip()
        return None

    def get_all_properties(self, block):
        for key, val in _KEYS_L2_INT.items():
            ret = self._extract_keys(val, block)
            if ret is not None:
                print(f'Key: {key:15s} Val: {ret}')
                self.__dict__[key] = ret


class Vlan():
    """[Class Vlan]

    Returns:
        [type] -- [description]
    """

    def __init__(self):
        self.vlan = None
        self.name = None

    @property
    def dict(self):
        name = self.name
        if self.name is None:
            name = ""
        resp = {
            'vlan': self.vlan,
            'name': name,
        }
        return resp

    @property
    def json(self):
        return json.dumps(self.dict)

    @staticmethod
    def _extract_keys(pattern, string):
        res = re.search(r'{}\s?(.*)'.format(pattern), string, re.DOTALL)
        # print(f'string: {string}')
        if res:
            return res.group(1).strip()
            # .split(',')[0].strip()
        return None

    def get_all_properties(self, block):
        for key, val in _KEYS_VLAN.items():
            ret = self._extract_keys(val, block)
            if ret is not None:
                if key == 'vlan':
                    ret = int(ret)
                self.__dict__[key] = ret
                # print(f'Key: {key:15s} Val: {self.__dict__[key]}')


class CiscoDevice():
    """[Class CiscoDevice]

    Returns:
        [type] -- [description]
    """

    def __init__(self, file_input, hostname=None, flag_l3_int=False, flag_vlans=False, flag_l2_int=False):
        self.hostname = hostname
        self.l3_int_entries = []
        self.vlan_entries = []
        self.l2_int_entries = []
        self.file_input = file_input
        if flag_l3_int:
            self._get_all_l3_int_entries()
        if flag_vlans:
            self._get_all_vlans_entries()
        if flag_l2_int:
            self._get_all_l2_int_entries()

    def _get_all_l3_int_entries(self):
        parse = CiscoConfParse(self.file_input)
        self.hostname = parse.re_match_iter_typed(r'^hostname\s+(\S+)', default='None')
        for obj in parse.find_objects_w_child(r'^interface', r'^\s*ip address'):
            cisco = L3Interface()
            cisco.get_all_properties(obj.text)
            for obj_child in obj.children:
                cisco.get_all_properties(obj_child.text)
            self.l3_int_entries.append(cisco)

    def _get_all_l2_int_entries(self):
        parse = CiscoConfParse(self.file_input)
        self.hostname = parse.re_match_iter_typed(r'^hostname\s+(\S+)', default='None')
        for obj in parse.find_objects_wo_child(r'^interface', r'^\s*(no)?\s*ip address'):
            print(f'Hostname: {self.hostname}  Interface: {obj.text}')
            cisco = L2Interface()
            cisco.get_all_properties(obj.text)
            for obj_child in obj.children:
                cisco.get_all_properties(obj_child.text)
            self.l2_int_entries.append(cisco)

    def _get_all_vlans_entries(self):
        parse = CiscoConfParse(self.file_input)
        self.hostname = parse.re_match_iter_typed(r'^hostname\s+(\S+)', default='None')
        for obj in parse.find_objects(r'^vlan\s*\d+'):
                # print('*'*80)
            if re.search(r'[,-]', obj.text):
                lst = obj.text.split()[1]
                for vl in lst.split(','):
                    if vl.isdigit():
                        cisco = Vlan()
                        cisco.get_all_properties(f'vlan {vl}')
                        self.vlan_entries.append(cisco)
                    else:
                        (ib, ie) = list(vl.strip().split('-'))
                        for jj in range(int(ib), int(ie) + 1):
                            cisco = Vlan()
                            cisco.get_all_properties(f'vlan {jj}')
                            self.vlan_entries.append(cisco)
            else:
                cisco = Vlan()
                cisco.get_all_properties(obj.text)
                for obj_child in obj.children:
                    cisco.get_all_properties(obj_child.text)
                self.vlan_entries.append(cisco)

    @property
    def l3_int_dict(self):
        resp = [l3_int_entries.dict for l3_int_entries in self.l3_int_entries]
        print(resp)
        return resp


class ListDevices():
    """[Class CiscoDevice]

    Returns:
        [type] -- [description]
    """

    def __init__(self, path_to_config, path_to_cdp=None, flag_l3_int=True, flag_vlans=False, flag_l2_int=False):
        self.hostnames = []
        self.hostnames_cdp = []
        self.l3_networks_groups = dict()
        self.flag_l3_int = flag_l3_int
        self.flag_l2_int = flag_l2_int
        self.flag_vlans = flag_vlans
        self.path_to_config = f'{path_to_config}'
        self.path_to_cdp = f'{path_to_cdp}'
        self.files_of_config = list(glob.glob(self.path_to_config))
        if path_to_cdp is not None:
            self.files_of_cdp = list(glob.glob(self.path_to_cdp))
            # print(f'CDP Files: {self.files_of_cdp}')
            for file_cdp in self.files_of_cdp:
                with open(file_cdp) as input_f:
                    cdp_file = input_f.read()
                rr = re.match(r'^([^#]*)#.*\s*', cdp_file)
                if rr:
                    hostname = rr.group(1)
                dev = cdp.Device(cdp_file, hostname=hostname)
                self.hostnames_cdp.append(dev)
                # print(f'hostname cdp: {dev.hostname}')
        for file_cfg in self.files_of_config:
            cisco = CiscoDevice(file_cfg, flag_l3_int=self.flag_l3_int, flag_vlans=self.flag_vlans, flag_l2_int=self.flag_l2_int)
            # print(f'Hostname: {cisco.hostname:15s} File: {file_cfg} ')
            self.hostnames.append(cisco)

    def create_csv_vlans(self, out_dir="output"):
        self._check_exit_dir(out_dir)
        for cisco in self.hostnames:
            # print(f'{cisco.hostname}')
            if cisco.vlan_entries:
                with open(f'{out_dir}/{cisco.hostname}_vlans.csv', 'w') as fs:
                    fs.write(f'Vlan;Name\n')
                    for ent in cisco.vlan_entries:
                        # print(f"VLAN: {ent.vlan} = {name}")
                        fs.write('{vlan};{name}\n'.format_map(ent.dict))

    def create_csv_vlans_all(self, out_dir="output"):
        self._check_exit_dir(out_dir)
        with open(f'{out_dir}/all_vlans.csv', 'w') as fs:
            fs.write(f'Vlan;Name;Hosname\n')
            for cisco in self.hostnames:
                # print(f'{cisco.hostname}')
                if cisco.vlan_entries:
                    for ent in cisco.vlan_entries:
                        fs.write('{vlan};{name}'.format_map(ent.dict) + f';{cisco.hostname}\n')

    def create_csv_l3_int(self, out_dir="output"):
        self._check_exit_dir(out_dir)
        for cisco in self.hostnames:
            # print(f'{cisco.hostname}')
            if cisco.l3_int_entries:
                with open(f'{out_dir}/{cisco.hostname}_l3_int.csv', 'w') as fs:
                    fs.write(f'NameInt;Desc;Vrf;SubInt;IPv4;IPv4Sec;Status;HSRP_Num;HSRP_IP;HSRP_Pri;IP_Helper\n')
                    for ent in cisco.l3_int_entries:
                        # print(f"VLAN: {ent.name} = {ent.ipv4}")
                        fs.write('{name};{desc};{vrf};{subint};{ipv4};{ipv4_sec};{status};{hsrp_num};{hsrp_ip};{hsrp_pri};{ip_helper}\n'.format_map(ent.dict))

    def create_csv_l3_int_all(self, out_dir="output"):
        self._check_exit_dir(out_dir)
        with open(f'{out_dir}/all_l3_int.csv', 'w') as fs:
            fs.write(f'Hostname;NameInt;Desc;Vrf;SubInt;IPv4;IPv4Sec;IPV_Net;Status;AccessList;HSRP_Num;HSRP_IP;HSRP_Pri;IP_Helper\n')
            for cisco in self.hostnames:
                # print(f'{cisco.hostname}')
                fs.write(f'=====;;;;;;;;;;;;;\n')
                if cisco.l3_int_entries:
                    for ent in cisco.l3_int_entries:
                        fs.write(f'{cisco.hostname};' + '{name};{desc};{vrf};{subint};{ipv4};{ipv4_sec};{ipv4_net};{status};{access_list};{hsrp_num};{hsrp_ip};{hsrp_pri};{ip_helper}\n'.format_map(ent.dict))

    def create_csv_l3_int_network(self, out_dir="output"):
        self._check_exit_dir(out_dir)
        # l3_network_groups = dict()
        for cisco in self.hostnames:
            # print(f'{cisco.hostname}')
            if cisco.l3_int_entries:
                for ent in cisco.l3_int_entries:
                    # print(f'{ent.dict["ipv4_net"]}')
                    desc_int = dict()
                    desc_int['name'] = f'{cisco.hostname}'
                    desc_int['ip'] = ent.dict['ipv4']
                    desc_int['int'] = ent.dict['name']
                    desc_int['desc'] = ent.dict['desc']
                    if f'{ent.dict["ipv4_net"]}' not in self.l3_networks_groups:
                        self.l3_networks_groups[f'{ent.dict["ipv4_net"]}'] = list()
                    self.l3_networks_groups[f'{ent.dict["ipv4_net"]}'].append(desc_int)
        with open(f'{out_dir}/all_net_l3_int.csv', 'w') as fs:
            fs.write(f'Networks;Hostname;Interface;IP_Address;Desc\n')
            for net in sorted(self.l3_networks_groups):
                # print(f'{net}')
                fs.write(f'{net}\n')
                for net_int in self.l3_networks_groups[net]:
                    fs.write(';{name};{int};{ip};{desc}\n'.format_map(net_int))

    def create_csv_l2_int(self, out_dir="output"):
        self._check_exit_dir(out_dir)
        for cisco in self.hostnames:
            # print(f'{cisco.hostname}')
            if cisco.l2_int_entries:
                with open(f'{out_dir}/{cisco.hostname.lower()}_l2_int.csv', 'w') as fs:
                    fs.write(f'NameInt;Desc;status;mode;access_vlan;trunk_allowed;channel_group;channel_mode;span_tree;speed\n')
                    for ent in cisco.l2_int_entries:
                        # print(f"VLAN: {ent.name} = {ent.ipv4}")
                        fs.write('{name};{desc};{status};{mode};{access_vlan};{trunk_allowed};{channel_group};{channel_mode};{span_tree};{speed}\n'.format_map(ent.dict))

    def create_csv_l2_int_all(self, out_dir="output"):
        self._check_exit_dir(out_dir)
        with open(f'{out_dir}/all_l2_int.csv', 'w') as fs:
            fs.write(f'HostName;NameInt;Desc;status;mode;access_vlan;trunk_allowed;channel_group;channel_mode;span_tree;speed\n')
            for cisco in self.hostnames:
                # print(f'{cisco.hostname}')
                if cisco.l2_int_entries:
                    for ent in cisco.l2_int_entries:
                        fs.write(f'{cisco.hostname.upper()};' + '{name};{desc};{status};{mode};{access_vlan};{trunk_allowed};{channel_group};{channel_mode};{span_tree};{speed}\n'.format_map(ent.dict))

    def create_csv_cdp(self, out_dir="output"):
        self._check_exit_dir(out_dir)
        for cisco in self.hostnames_cdp:
            # print(f'{cisco.hostname}')
            if cisco.dict:
                with open(f'{out_dir}/{cisco.hostname}_cdp.csv', 'w') as fs:
                    fs.write(f'LocalName;LocalPort;RemoteName;RemotePort;RemotePlatform;RemoteIP\n')
                    for ent in cisco.dict:
                        # print(f"VLAN: {ent.name} = {ent.ipv4}")
                        fs.write(f'{cisco.hostname};' + '{local_port};{device_id};{remote_port};{platform};{ip_address}\n'.format_map(ent))

    def create_csv_cdp_all(self, out_dir="output"):
        self._check_exit_dir(out_dir)
        with open(f'{out_dir}/all_cdp.csv', 'w') as fs:
            fs.write(f'LocalName;LocalPort;RemoteName;RemotePort;RemotePlatform;RemoteIP\n')
            for cisco in self.hostnames_cdp:
                # print(f'{cisco.hostname}')
                if cisco.dict:
                    for ent in cisco.dict:
                        fs.write(f'{cisco.hostname};' + '{local_port};{device_id};{remote_port};{platform};{ip_address}\n'.format_map(ent))

    def _check_exit_dir(self, path_dir):
        if not os.path.exists(f'{path_dir}'):
            os.makedirs(f'{path_dir}')
