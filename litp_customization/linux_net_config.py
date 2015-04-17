#!/usr/bin/env python

"""
@copyright: Ericsson AB
@since:     Sept 2012
@author:    Niall OByrnes
@summary:
            Agile:        STORY-2878
"""

#pylint: disable=R0912,R0915

from core.litp_resource import LitpResource
from litp_graphs.network_graph_props import NetworkGraphProps
from litp_graphs.network_graph_consts import NetworkGraphConsts
from litp_graphs.network_graph_topology import NetworkTopology
from litp_common.logger.litp_log import createLitpLogger
from svc_aliases.alias_ctrl import AliasCtrl
logger = createLitpLogger('litp.network')


class LinuxNetConf(LitpResource):
    """
    Extracts networking information from NetworkTopology and pools to
    provide config data for the puppet module:
    U{https://github.com/blkperl/puppet-module-network}
    litp /definition/os/system/linuxnetconf create litp_netconf.LinuxNetConf
    Limitations
        1. Host config still handled by RHELOS
        2. Extra additional config of networks not implemented, eg stp for
            bridge, (mandatory values are hardcoded)
        3. No validation on NetworkTopology logic
        4. Expects Topology hierarchy: Network, Vlan, Bridge, Bond, Nic,
            however not all elements are needed except network
        5. Limitation: All NetworkTopologies should have net at the top
        6. Limitation: No capability to produce a running network, if eth0
            is created in the Topology
        7. Limitation: There can be only one child of a network.  This does
            not support the creation of 2 subinterfaces from the same network
    """

    VLAN_TAG = 'vlan'
    """
    @cvar: Name for vlan used in puppet and network config files
    @type: String
    """

    BRIDGE_TAG = 'br'
    """
    @cvar: Name for bridge used in puppet and network config files
    @type: String
    """

    BOND_TAG = 'bond'
    """
    @cvar: Name for bond used in puppet and network config files
    @type: String
    """

    NIC_TAG = 'eth'
    """
    @cvar: Name for nic used in puppet and network config files
    @type: String
    """

    NETCLASS = 'litp_graphs.network_graph_topology.NetworkTopology'
    """
    @cvar: path to the Network Topology class
    @type: String
    """

    DEFAULT_BONDING_MODE = '1'
    """
    @cvar: Default bonding mode
    @type: String
    """

    DEFAULT_BOOTPROTO = 'static'
    """
    @cvar: Default BOOTPROTO setting
    @type: String
    """

    def __init__(self):
        super(LinuxNetConf, self).__init__()
        self.configuration = list()
        """
        @ivar: The configuration dictionary that configmanager uses to
            create the puppet outout
        @type: Dictionary
        """

        self.current_ifaces = list()
        """
        @ivar: List of currently configured interfaces
        @type: List
        """

    def is_configurable(self):
        """
        If topo_framework is non-existant or "on" then produce config.
        else if topo_framework is found and off then return False
        """

        node = self._get_my_node()
        if not node:
            logger.debug("Failed to find LitpNode")
            return False

        address = node._lookup_children( \
                    types='^(operatingsystem.rhel.RHELOS)$')
        if address:
            rhel_obj = self.get_item_by_path(address[0])
            topo_prop = rhel_obj.get_prop("topo_framework")
            if topo_prop == 'off':
                logger.debug("topo_framework set to off, no config produced")
                return False
        msg = "topo_framework not found or set to 'on' => config produced"
        logger.debug(msg)
        return True

    def allowed_properties(self):
        ap = super(LinuxNetConf, self).allowed_properties()
        return ap

    def _format_iface(self, iface_type, iftag):
        """
        Small helper method to return the interface name, given the type
        and the tag (The identifier from the Netgraph)
        """
        #iftag is validated from the netgraph
        return "%s%s" % (iface_type, iftag.split()[1])

    def _get_my_node(self):
        """
        Function to get the parent node
        @return: LitpNode Instance
        """
        return self._lookup_parents(types="core.litp_node.LitpNode")

    def _get_my_nett(self):
        """
        Method to find the 'most applicable' topology if one exists.
        The most applicable topology, follows the following priority
            1. Topology hanging off System
            2. Topology hanging off the Pool class
               or maybe Pool of Pools
            3. Topology hanging of this Node
            4a. Topology off the next highest tree level above Node ie Site
            4b. Topology on cluster
            4c. Topology on deployment
            5. Try Inventory

        @return: 3-Tuple: NetworkTopology instance, Key, Error-msg
        @rtype: 3-Tuple: NetworkTopology, String, String
        """

        netts = NetworkTopology.get_network_topology(self)
        if not netts:
            return (None, 'error',
                    'No applicable Network Topology found')
        elif len(netts) > 1:
            return (None, 'error',
                    'Ambiguous number of %d NetGraphs found' % len(netts))
        else:
            nett = netts[0]
            msg = "%s to node %s" % (nett.get_vpath(), self.get_vpath())
            logger.debug("Applying netgraph at location " + msg)
            return (nett, 'success', 'Ok')

    def _configure_loopback(self):
        i_name = 'lo'
        i_params = {'name': i_name,
                    'device': i_name,
                    'ipaddr': '127.0.0.1',
                    'netmask': '255.0.0.0',
                    'network': '127.0.0.0',
                    'broadcast': '127.255.255.255',
                    'bootproto': 'static',
                    'onboot': 'yes',
                    'nozeroconf': 'yes',
                    'userctl': 'no',
                    'ensure': 'present'}

        self._config_insert(i_name, i_params)

    def _configure(self, parameters=None):
        """
        Accumulate the configuration info to configure the network
        """

        preamble = self.__class__.__name__ + '._configure: '

        if parameters == None:
            parameters = dict()

        if parameters and "deconfigure" in parameters:
            return {'error':
                    'This item type does not support deconfigure'}

        node = self._get_my_node()
        if not node:
            return {'error': preamble + 'No LitpNode found'}

        preamble += 'Node ' + node.id + ': '

        child0_vpath = None
        for child_type in ["litp_netconf.linux_net_config.LinuxNetConf",
                           "hardware.generic_system.GenericSystem"]:
            kids = node._lookup_children(types=child_type)
            if not kids or len(kids) != 1:
                msg = (preamble + \
                       "There must be exactly one '%s' " + \
                       "per Node") % child_type
                return {'error': msg}
            else:
                child0_vpath = kids[0]

        # The last child_type searched for is the "System" type
        system = self.get_item_by_path(child0_vpath)

        #Clean the configuration...
        self._config_drop()

        (nett, key, msg) = self._get_my_nett()
        if not nett:
            return {key: preamble + msg}

        (ok, msg) = self._validate_nett(nett)
        if not ok:
            return {'error': preamble + msg}

        #(ok, msg) = self._validate_net_names(nett, self._get_my_node())
        #if not ok:
        #    return {'error': msg}

        type_net = NetworkGraphConsts.VERTX_ITYPE_NET
        type_vlan = NetworkGraphConsts.VERTX_ITYPE_VLAN
        type_brdg = NetworkGraphConsts.VERTX_ITYPE_BRDG
        type_bond = NetworkGraphConsts.VERTX_ITYPE_BOND
        type_nic = NetworkGraphConsts.VERTX_ITYPE_NIC

        #startingvertices = nett.get_starting_vertices()
        nets = nett.get_vertices_by_type(type_net)
        logger.debug((preamble + "%s") % nets)

        pocs_created = 0
        for net in nets:
            with_poc = self._configure_network(nett, node.id, net)
            if with_poc:
                pocs_created += 1

        #Configure all the vertices except networks
        for vlan in nett.get_vertices_by_type(type_vlan):
            self._configure_vlan(nett, node.id, vlan['value'])

        for bridge in nett.get_vertices_by_type(type_brdg):
            self._configure_bridge(nett, node.id, bridge['value'])

        for bond in nett.get_vertices_by_type(type_bond):
            self._configure_bond(nett, node.id, bond['value'])

        for nic in nett.get_vertices_by_type(type_nic):
            self._configure_nic(nett, node.id, nic['value'], system)

        #Generate list of current interfaces
        self.current_ifaces = [i['id'] for i in self.configuration]

        #Comment out this if testing
        self._configure_restart()

        #Add in the loopback interface
        self._configure_loopback()

        if (pocs_created > 0):
            logger.debug((preamble + \
                          "%d POCs were created ... " + \
                          "will configure Alias Slave") % \
                          pocs_created)

            child_type = "svc_aliases.alias_slave.AliasSlave"
            kids = node._lookup_children(types=child_type)
            if kids and len(kids) == 1:
                kid_slave_path = kids[0]
                logger.debug((preamble + \
                              "(Re)configuring Alias Slave '%s'") % \
                              kid_slave_path)
                kid_slave = node.get_item_by_path(kid_slave_path)
                kid_slave.int_configure()
            else:
                logger.debug((preamble + \
                              "Indeterminate count of '%s' items") % \
                             child_type)

        return {'success': preamble + 'Configured OK',
                'item': 'LinuxNetConf'}

    def _verify(self, parameters=None):
        '''
        Verify all members of the most applicable network graph
        @param parameters: Input parameters - defaults to None
        @type parameters: Dictionary
        @return: Dictionary containing key 'success|error'
        @rtype: Dictionary
        '''
        if parameters is None:
            parameters = dict()

        preamble = self.__class__.__name__ + ':_verify '

        node = self._get_my_node()
        if not node:
            return {'error': preamble + 'No LitpNode found'}

        preamble += 'Node ' + node.id + ': '

        (nett, key, msg) = self._get_my_nett()
        if not nett:
            return {key: msg}

        name = NetworkGraphProps.PROP_GRAPH_NAME
        logger.debug((preamble + "Digraph %s found at %s") % \
                     (nett.get_prop(name), nett.get_vpath()))

        #Execute an ifconfig on the node
        (rc, stdout, stderr) = self.execute(["ifconfig"], timeout=10)

        msg1 = (preamble + "ifconfig: rc:'%s' stderr:%s") % (rc, stderr)
        logger.debug(msg1)
        msg2 = (preamble + "ifconfig: stdout:%s") % stdout
        logger.debug(msg2)

        if rc == 255:
            msg = preamble + "Failed: cannot contact Node via SSH"
            logger.debug(msg)
            return {'error': msg}

        failed_dev = list()

        #Verify NICs
        nics = nett.get_vertices_by_type(NetworkGraphConsts.VERTX_ITYPE_NIC)
        for iftag in [i['value'] for i in nics]:
            iface = NetworkTopology._get_nic_iface(iftag.split()[1])
            #the space after iface important, to distinguish between subtags
            if iface + ' ' not in stdout:
                failed_dev.append("%s" % iface)

        #Verify VLANs
        vlans = nett.get_vertices_by_type(NetworkGraphConsts.VERTX_ITYPE_VLAN)
        for iftag in [i['value'] for i in vlans]:
            iface = self._get_vlan_child_tag(nett, iftag)
            #the space after iface important, to distinguish between subtags
            if iface + ' ' not in stdout:
                failed_dev.append("VLAN %s " % iface)

        #Verify Bridges
        brdgs = nett.get_vertices_by_type(NetworkGraphConsts.VERTX_ITYPE_BRDG)
        for iftag in [i['value'] for i in brdgs]:
            iface = self._format_iface(LinuxNetConf.BRIDGE_TAG, iftag)
            #the space after iface important, to distinguish between subtags
            if iface + ' ' not in stdout:
                failed_dev.append("BRIDGE %s " % iface)

        #Verify Bonds
        bonds = nett.get_vertices_by_type(NetworkGraphConsts.VERTX_ITYPE_BOND)
        for iftag in [i['value'] for i in bonds]:
            iface = self._format_iface(LinuxNetConf.BOND_TAG, iftag)
            #the space after iface important, to distinguish between subtags
            if iface + ' ' not in stdout:
                failed_dev.append("BOND %s " % iface)

            #Verify Bonded slaves
            (ok, msg) = self._verify_bonded_slaves(nett, iftag)
            if not ok:
                failed_dev.append("SLAVES %s " % msg)

        #Verify Networks (verifys IPv6 only)
        (ok, msg) = self._verify_networks(nett)
        if not ok:
            failed_dev.append("NETWORK %s " % msg)

        if len(failed_dev) > 0:
            devs = ", ".join(failed_dev)
            return {'error': (preamble + "Failed: %s") % devs}

        return {'success': preamble + 'Ok'}

    def _lnc_self_execute(self, cmd):
        rc, stdout, stderr = self.execute(cmd, timeout=10)
        msg = "%s: rc=%s stdout=%s stderr=%s" % (cmd, rc, stdout, stderr)
        logger.debug(msg)
        if rc == 255:
            return (False, "Could not shell to node")
        else:
            return (True, stdout)

    def _verify_networks(self, nett):
        """
        Verify the ipv6 address if it exists for each network
        ipv4 will be effectively verified on the self.execute.
        """

        node = self._get_my_node()
        if not node:
            return (False, "Failed to find LitpNode")

        fail = list()
        nets = nett.get_vertices_by_type(NetworkGraphConsts.VERTX_ITYPE_NET)
        for net in [i['value'] for i in nets]:

            #Check for ipv6 under node for each network
            ipv6 = node.get_ip_address_v2(net, 'IPv6')
            if ipv6:
                #ping6 the node
                if ipv6.startswith('fe80'):
                    #Get the interface name where the IPs are inserted
                    iface = self._gen_network_iface(nett, net)
                    cmd = ['ping6', '-I', iface, ipv6]
                else:
                    cmd = ['ping6', ipv6]

                ok, msg = self._lnc_self_execute(cmd)
                if not ok:
                    return (False, msg)
                elif 'ping ok' not in msg:
                    fail.append(ipv6)

        if len(fail) > 0:
            return (False, "Failed IPv6: %s" % ", ".join(fail))
        else:
            return (True, 'ok')

    def _verify_bonded_slaves(self, nett, iftag):
        """
        Verify bond
        """

        #Ensure correct slaves for the bond
        iface = self._format_iface(LinuxNetConf.BOND_TAG, iftag)
        cmd = ["cat", "/proc/net/bonding/%s" % iface]
        r, stdout2, stderr2 = self.execute(cmd, timeout=10)
        msg = "%s: rc=%s stdout=%s stderr=%s" % (cmd, r, stdout2, stderr2)
        logger.debug(msg)

        children = nett.get_vertex_peers(iftag)
        slaves = [i['value'] for i in children
                  if i['itype'] == NetworkGraphConsts.VERTX_ITYPE_NIC]
        logger.debug('Verifying %s has slaves: %s' % (iface, slaves))

        for slave in slaves:
            nic = NetworkTopology._get_nic_iface(slave.split()[1])
            check = "Slave Interface: %s\nMII Status: up" % nic
            if check not in stdout2:
                msg = "Verify Failed, %s not bonded to %s" % (nic, iftag)
                return (False, msg)

        #Ensure correct mode setup on bond
        mode_int = self._get_bonding_mode(nett, iftag)
        proctxt = translate_bonding_opts(mode_int)

        #This should never really happen
        if not proctxt:
            msg = "Network Verify Failed: Bonding mode " + \
                                        "untested or not in Netgraph"
            return (False, msg)

        if proctxt not in stdout2:
            msg = "Verify Failed, %s mode should be %s" % (iftag, proctxt)
            return (False, msg)

        return (True, 'ok')

    def _validate_net_names(self, nett, node):
        #Ensure Every node has a mgmt network ip
        if not node.get_ip_address_v2('mgmt', 'IPv4') and \
           not node.get_ip_address_v2('mgmt', 'IPv6'):
            return (False, "Cannot find an IP for network mgmt")

        #Ensure at least one ip per network name on every node
        found_nets = False
        nets = nett.get_vertices_by_type(NetworkGraphConsts.VERTX_ITYPE_NET)
        for net in nets:
            net_name = net['name']
            found_nets = True
            if not node.get_ip_address_v2(net_name, 'IPv4') and \
               not node.get_ip_address_v2(net_name, 'IPv6'):
                return (False, "IPv4 or IPv6 not found for net " + net_name)

        if found_nets:
            return (True, 'ok')
        else:
            return (False, 'No Networks found')

    def _validate_nett(self, nett):
        valerr = "NetTopology Validation Failed"
        #Network should only have one child--this might change
        #depending on subinterfaces

        nets = nett.get_vertices_by_type(NetworkGraphConsts.VERTX_ITYPE_NET)
        for net in nets:
            children = nett.get_vertex_peers(net['value'])
            if len(children) == 0:
                msg = "Network %s has no children" % net['name']
                return False, "%s %s" % (valerr, msg)
            elif len(children) > 1:
                msg = "More than one child of network %s" % net['name']
                return False, "%s %s" % (valerr, msg)

        #Vlan can only have one child for now
        vlans = nett.get_vertices_by_type(NetworkGraphConsts.VERTX_ITYPE_VLAN)
        for vlan in vlans:
            children = nett.get_vertex_peers(vlan['value'])
            if len(children) == 0:
                msg = "Vlan %s has no children" % vlan['value']
                return False, "%s %s" % (valerr, msg)
            elif len(children) > 1:
                msg = "More than one child of vlan %s " % vlan['value']
                return False, "%s %s" % (valerr, msg)

        #Pavel: WE ONLY SUPPORT NICS REALLY ?!!
        #Not really looks like we will have to suport bonds too
        brdgs = nett.get_vertices_by_type(NetworkGraphConsts.VERTX_ITYPE_BRDG)
        for bridge in brdgs:
            #Bond needs to find his downstream targets & config all of them
            children = nett.get_vertex_peers(bridge['value'])
            bonds = [i['name'] for i in children
                     if i['itype'] == NetworkGraphConsts.VERTX_ITYPE_BOND]
            nics = [i['name'] for i in children
                    if i['itype'] == NetworkGraphConsts.VERTX_ITYPE_NIC]
            vlans = [i['name'] for i in children
                    if i['itype'] == NetworkGraphConsts.VERTX_ITYPE_VLAN]

            if ((len(nics) != len(children)) and \
                (len(vlans) != len(children)) and \
                (len(bonds) != len(children))):
                msg = "Children of bridge " + bridge['value'] + \
                      " must be exclusively nics or bonds or vlans"
                return False, "%s %s" % (valerr, msg)

        #Pavel: WE ONLY SUPPORT bonding of NICS REALLY ?!!
        bonds = nett.get_vertices_by_type(NetworkGraphConsts.VERTX_ITYPE_BOND)
        for bond in bonds:
            children = nett.get_vertex_peers(bond['value'])

            nics = [i['name'] for i in children
                    if i['itype'] == NetworkGraphConsts.VERTX_ITYPE_NIC]

            if len(nics) != len(children):
                msg = "Bonding only supports NICS see bond %s" % bond['value']
                return False, "%s %s" % (valerr, msg)
        return True, 'ok'

    def _getaddrs(self, node, vtype='IPv4', nwk=''):
        ip = node.get_ip_address_v2(nwk, vtype)
        if not ip:
            return None
        else:
            netmask = node.get_ip_netmask_v2(nwk, vtype)
            gateway = node.get_ip_gateway_v2(nwk, vtype)
            bcast = node.get_ip_broadcast_v2(nwk, vtype)
            return (ip, netmask, gateway, bcast)

    def _gen_network_iface(self, nett, net):
        """
        This generates the name of the iface that the IP will hold the IP
        """

        ifvalue = net['value']

        #Network should only have one child--this might change
        #depending on subinterfaces.
        children = nett.get_vertex_peers(ifvalue)
        child = children[0]

        #Use relevant iface, but if a vlan, get the vlan name using its child
        if child['itype'] == NetworkGraphConsts.VERTX_ITYPE_VLAN:
            iface = self._get_vlan_child_tag(nett, child['value'])
        elif child["itype"] == NetworkGraphConsts.VERTX_ITYPE_NIC:
            iface = NetworkTopology._get_nic_iface(child["name"])
        else:
            iface = "%s%s" % (get_tag_by_itype(child['itype']),
                              child['name'])

        #if the interface already exists, create a new sub-interface
        if self._config_iface_exist(iface):
            iface = self._get_next_subiface(iface)

        return iface

    def _create_alias_poc(self, net_name):
        """
        Creates an alias bean in the tree
        """

        preamble = self.__class__.__name__ + '._create_alias_poc: '
        node = self._get_my_node()
        if not node:
            logger.debug(preamble + "No LitpNode found")
            return False

        addr_obj = node._get_addr_obj(net_name)

        if not addr_obj:
            msg = "No Address obj found for %s" % net_name
            logger.debug(preamble + msg)
            return False

        alias_str = "%s-%s" % \
                    (node.get_hostname(),
                     net_name.replace('_', '-'))

        #Create an Alias property only class in the Landscape.
        #Calls a fire and forget static method on the AliasCtrl
        msg = "Alias POC created by LinuxNetConf: %s %s" % \
              (alias_str, str(addr_obj))
        logger.debug(preamble + msg)
        AliasCtrl.create_alias_poc(addr_obj, alias_str)

        return True

    def _get_bootproto(self, nett, iftag):
        """
        Handles the default for the BOOTPROTO
        """

        attrs = nett.get_vertex_attrs(iftag)
        if attrs == None or attrs.get('bootproto', 'Empty') == 'Empty':
            return str(LinuxNetConf.DEFAULT_BOOTPROTO)
        else:
            return str(attrs['bootproto'])

    def _configure_network(self, nett, node_id, net):
        """
        This handles the config of the ipaddress

        Example Puppet Output
        network_config { "RELEVANT IFACE"
        netmask       => "255.255.255.0",
        broadcast     => "192.168.56.255",
        ipaddr        => "192.168.56.101",
        #domain        => "example.domain.com",
        }
        @rtype: Boolean
        @return: Boolean if an Alias POC was created
        """

        preamble = self.__class__.__name__ + \
                   '._configure_network: Node ' + \
                   node_id + ': '

        logger.debug((preamble + "Attempting to process net- %s") % net)

        iface = self._gen_network_iface(nett=nett, net=net)
        children = nett.get_vertex_peers(net['value'])
        child = children[0]

        ip_created = False

        #Configure IPv4
        addrs_v4 = self._getaddrs(self._get_my_node(), 'IPv4', net['name'])
        if addrs_v4:
            vals = {'ipaddr': addrs_v4[0],
                    'netmask': addrs_v4[1],
                    'gateway': addrs_v4[2],
                    'broadcast': addrs_v4[3]}
            self._config_upsert(child['itype'], iface, vals, exactmatch=1)

            msg = "Network " + net['name'] + " configured with " + \
                  "ipv4=%s, netmask=%s, gateway=%s, broadcast=%s" % addrs_v4
            ip_created = True
            logger.debug(preamble + msg)

        else:
            msg = logger.msgs.warnings.lnc.COULD_NOT_FIND_ADDR
            logger.warning(msg, ipversion='IPv4', network=net['name'])

        #Configure ipV6
        addrs_v6 = self._getaddrs(self._get_my_node(), 'IPv6', net['name'])
        if addrs_v6:
            vals = {'ipv6addr': addrs_v6[0], 'ipv6init': 'yes'}
            if addrs_v6[2]:
                vals['ipv6_defaultgw'] = addrs_v6[2]

            self._config_upsert(child['itype'], iface, vals, exactmatch=1)
            ip_created = True
            msg = "Network %s configured with ipv6=%s, gateway=%s" % \
                  (net['name'], addrs_v6[0], addrs_v6[2])
            logger.debug(preamble + msg)
        else:
            msg = "IPv6 not found for network %s" % net['name']
            logger.debug(preamble + msg)

        #Get the bootproto
        bootproto = self._get_bootproto(nett, 'net ' + net['name'])
        logger.debug("%s bootproto %s for net %s" % \
                                    (preamble, bootproto, net['name']))
        self._config_upsert(child['itype'],
                            iface,
                            {'bootproto': bootproto})

        #Check for the ip_optional tag on the network in the diagraph
        if not ip_created:
            ip_optional = NetworkGraphConsts.SUPP_NET_ATTR_IP_OPTIONAL

            attrs = nett.get_vertex_attrs(iface)

            if attrs and ip_optional in attrs.keys():
                #Create blank interface
                self._config_upsert(child['itype'],
                                    iface,
                                    {'bootproto': bootproto})
                msg = "Interface created without an IP for %s" % iface
                logger.debug(preamble + msg)
                return False
        else:
            #Create an alias property only class in the landscape.
            #Calls a fire and forget static method on the AliasCtrl
            return self._create_alias_poc(net['name'])

    def _configure_restart(self):
        """
        Adds a puppet config to restart the network,
        This is also used by the notify on the devices to genereate
        a restart when a device config changes
        """
        values = {'command': '/etc/init.d/network restart',
                  'logoutput': 'true',
                  'refreshonly': 'true'}
        self.configuration.append({'id': 'linux_net_conf_restart',
                                   'type': 'exec',
                                   'values': values})

    def _configure_vlan(self, nett, node_d, iftag):
        """
        Example Puppet Output:
        network_config { "eth0.2":
        vlan          => "yes",
        }
        """

        iface = self._get_vlan_child_tag(nett, iftag)

        self._config_upsert(NetworkGraphConsts.VERTX_ITYPE_VLAN,
                            iface,
                            {'ensure': 'present',
                             'vlan': 'yes',
                             'onboot': 'yes'})

    def _configure_bridge(self, nett, node_id, iftag):
        """
        Example Puppet output
        network_config { "eth0":
        bridge        => "br0"
        }
        network_config { "br0":
        type          => "Bridge",
        bootproto     => "static",
        stp           => "on",
        }
        """

        iface = self._format_iface(LinuxNetConf.BRIDGE_TAG, iftag)

        #Bond needs to find his downstream targets and config all of them
        children = nett.get_vertex_peers(iftag)

        bonds = [i['name'] for i in children
                 if i['itype'] == NetworkGraphConsts.VERTX_ITYPE_BOND]

        nics = [i['name'] for i in children
                if i['itype'] == NetworkGraphConsts.VERTX_ITYPE_NIC]

        #LITP-2967 Allowing Bridge on top of Vlan
        vlans = [i['name'] for i in children
                 if i['itype'] == NetworkGraphConsts.VERTX_ITYPE_VLAN]

        #Config Extra Bits
        stp = 'off'
        delay = '0'

        if nics:
            #Set up target nics and ensure they exist
            for target in nics:
                #Need to test if nic exists here.
                self._config_upsert(NetworkGraphConsts.VERTX_ITYPE_NIC,
                                    NetworkTopology._get_nic_iface(target),
                                    {'bridge': iface})

        elif bonds:
            for target in bonds:
                self._config_upsert(NetworkGraphConsts.VERTX_ITYPE_NIC,
                                    LinuxNetConf.BOND_TAG + target,
                                    {'bridge': iface})

        #LITP-2967 (CONT): Allowing Bridge on top of Vlan
        #TODO: Niall? to check if there is better way for:
        # LinuxNetConf.NIC_TAG + nic['name'] + '.' + vlan
        elif vlans:
            for vlan in vlans:
                nic_children = nett.get_vertex_peers(
                                            LinuxNetConf.VLAN_TAG + ' ' + vlan)
                if nic_children:
                    for nic in nic_children:
                        new_iface = NetworkTopology._get_nic_iface(
                        nic["name"]) + '.' + vlan
                        self._config_upsert(NetworkGraphConsts.VERTX_ITYPE_NIC,
                                            new_iface,
                                            {'bridge': iface})

        data = {'ensure': 'present',
                'type': 'Bridge',
                'onboot': 'yes',
                'stp': stp,
                'delay': delay,
                'bootproto': self._get_bootproto(nett, iftag)}

        #Set up bridge
        self._config_upsert(NetworkGraphConsts.VERTX_ITYPE_BRDG, iface, data)

        return True, 'ok'

    def _get_bonding_mode(self, nett, iftag):
        """
        Handles the default for the bonding mode
        """

        attrs = nett.get_vertex_attrs(iftag)
        if not attrs:
            bonding_opts = "%s" % LinuxNetConf.DEFAULT_BONDING_MODE
            logger.debug('mmhh2-- _get_bonding_mode no attrs ' + iftag)
        elif attrs.get('mode', 'Empty') == 'Empty':
            bonding_opts = "%s" % LinuxNetConf.DEFAULT_BONDING_MODE
            logger.debug('mmhh2-- _get_bonding_mode empty mode ' + iftag)
        else:
            bonding_opts = "%s" % attrs['mode']
            logger.debug('mmhh2-- _get_bonding_mode got attrs ' + bonding_opts)

        return bonding_opts

    def _get_bonding_primary(self, nett, iftag):
        """
        Handles the default for the bonding mode
        """

        attrs = nett.get_vertex_attrs(iftag)
        if not attrs:
            bonding_opts = ''
            logger.debug('mmhh2-- _get_bonding_primary no attrs ' + iftag)
        elif attrs.get('primary', 'Empty') == 'Empty':
            bonding_opts = ''
            logger.debug('mmhh2-- _get_bonding_primary empty primary ' + iftag)
        else:
            bonding_opts = "%s" % attrs['primary']
            logger.debug('mmhh2-- _get_bonding_primary got attrs ' + bonding_opts)

        return bonding_opts

    def _configure_bond(self, nett, node_id, iftag):
        """
        Puppet output
        network_config { "bond0":
        type          => "Bonding",
        bonding_module_opts => "mode=balance-rr miimon=100",
        }
        network_config { "eth0": master => "bond0", slave => "yes" }
        network_config { "eth2": master => "bond0", slave => "yes" }
        """
        iface = self._format_iface(LinuxNetConf.BOND_TAG, iftag)

        #Bond needs to find his child nics and config all of them
        children = nett.get_vertex_peers(iftag)
        nics = [i['name'] for i in children
                if i['itype'] == NetworkGraphConsts.VERTX_ITYPE_NIC]

        #Configure slaves and ensure they exist
        for slave in nics:
            self._config_upsert(NetworkGraphConsts.VERTX_ITYPE_NIC,
                                NetworkTopology._get_nic_iface(slave),
                                {'master': iface,
                                 'slave': 'yes'})

        #Bonding options
        primary = self._get_bonding_primary(nett, iftag)
        bonding_opts = None
        if primary == None or primary == '':
            bonding_opts = "miimon=100 mode=%s" %(self._get_bonding_mode(nett, iftag))
        else:
            nic_iface = 'eth' + primary.split('_')[1]
            bonding_opts = "miimon=100 mode=%s primary=%s" %(self._get_bonding_mode(nett, iftag), nic_iface)
        logger.debug('mmhh3-- bonding_opts: ' + bonding_opts + '; iftag: ' + iftag + '; primary: ')

        #Configure bond
        self._config_upsert(3, iface,
                            {'ensure': 'present',
                             'bootproto': self._get_bootproto(nett, iftag),
                             'onboot': 'yes',
                             'type': 'Bonding',
                             'bonding_opts': bonding_opts})

    def _configure_nic(self, nett, node_id, iftag, system):
        """
        Generate Configuration for a NIC
        @param iftag: NIC name
        @type iftag: String
        @param system: The System for this Node
        @type system: GenericSystem

        Example Puppet Output
        network_config { 'eth0':
        onboot      => 'yes',
        hwaddr      => 'hwaddr',
        vlan        => 'vlan',   <-- controlled by confgure vlan
        nozeroconf  => 'yes',
        userctl     => 'no'
        }
        """

        preamble = self.__class__.__name__ + \
                   '._configure_nic: ' + \
                   'Node ' + node_id + ': '

        iface = NetworkTopology._get_nic_iface(iftag.split()[1])

        new_config = {'ensure': 'present',
                      'onboot': 'yes',
                      'userctl': 'no',
                      'nozeroconf': "yes"}

        mac = system.get_mac_address_by_nic_id(iface)
        if mac:
            new_config['hwaddr'] = mac
            logger.debug((preamble + "Set MAC to '%s' for NIC (%s) '%s'") % \
                         (mac, iftag, iface))
        else:
            logger.debug(preamble + "No MAC found for NIC " + iface)

        self._config_upsert(4, iface, new_config)

        # Set default bootproto if not already set (by network)
        ids_and_configs = self._get_ids_and_configs_for_ifaces(iface)
        for id, config in ids_and_configs:
            if 'bootproto' not in config:
                logger.debug(preamble + ('Adding bootproto to "%s"' % id))
                config['bootproto'] = LinuxNetConf.DEFAULT_BOOTPROTO

    def get_configured_iface(self):
        return [i['id'] for i in self.configuration]

    def get_configuration(self):
        """
        Returns the call var configuration
        @return: Instance variable configuration
        """
        return self.configuration

    def _get_vlan_child_tag(self, nett, iftag):
        """
        Function returns a formatted vlan name givin its child verted
        @return: vlan tag name
        @rtype: String
        """
        children = nett.get_vertex_peers(iftag)
        if len(children) != 1:
            return False

        if children[0]["itype"] == NetworkGraphConsts.VERTX_ITYPE_NIC:
            vlanchild = NetworkTopology._get_nic_iface(children[0]["name"])
        else:
            vlanchild = get_tag_by_itype(children[0]["itype"]) + \
                        children[0]["name"]
        logger.debug('mmhh20-- nett: ' + str(nett) + '; iftag: ' + str(iftag) + '; vlanchild: ' + str(vlanchild))

        return "%s.%s" % (vlanchild, iftag.split()[1])

    def _config_insert(self, iface, values):
        """
        Insert into config.  Ie append to the config list
        """
        preamble = self.__class__.__name__ + '._config_insert: '

        #Notify the Service, to restart the network when
        #the iface config changes
        values['notify'] = "Exec[linux_net_conf_restart]"

        self.configuration.append({'type': "network_config",
                                   'id': iface,
                                   'values': values})

        vals = ", ".join(["%s=%s" % (k, v) for k, v in values.items()])
        logger.debug((preamble + \
                     "Interface %s added, initial vals %s") % \
                     (iface, vals))
        return

    def _get_ids_and_configs_for_ifaces(self, iface):
        ids_and_configs = []
        for i in self.configuration:
            if i['id'] == iface or i['id'].startswith(iface + '.'):
                ids_and_configs.append((i['id'], i['values']))
        return ids_and_configs

    def _config_upsert(self, itype, iface, values, exactmatch=0):
        """
        When exactmatch is set to 0:
        Upserts by iface, so also updated sub-interfaces
        i.e. it updates nic0 and nic0:0

        When exactmatch is set to 1: only upserts the exact match
        """

        preamble = self.__class__.__name__ + '._config_upsert: '

        msg = "Upserting %s, %s, %s, %s" % (itype, iface, values, exactmatch)
        logger.debug(preamble + msg)

        found = False
        foundbaseiface = False

        for i in self.configuration:
            if (i['id'] == iface) or \
               ((exactmatch == 0) and (i['id'].startswith(iface + ':'))):
                found = True
                for k, v in values.items():
                    i['values'][k] = v

                vals = ", ".join(["%s=%s" % (k, v) for k, v in values.items()])
                logger.debug((preamble + "Updating %s, with vals %s") % \
                             (i['id'], vals))

                if found:
                    if i['id'] == iface:
                        foundbaseiface = True

        #Ensure the iface is created
        if not found or not foundbaseiface:
            self._config_insert(iface, values)
        return

    def _config_iface_exist(self, iface):
        """
        Check if an interface exists:  Does not look for sub-iface
        @return: Booleen giving existance of an interface
        @rtype: Booleen
        """
        for i in self.configuration:
            #exclude subinterfaces
            if i['id'].split(':')[0] == iface:
                return True
        return False

    def _get_next_subiface(self, iface):
        """
        Finds the next available subinterface
        @return: Returns the name of the subinterface
        @rtype: String
        """

        #first sub-interface begins at 1
        enum = 0
        for i in self.configuration:
            if i['id'].split(':')[0] == iface:
                enum += 1
        return "%s:%s" % (iface, enum)

    def _config_drop(self):
        """
        Resets or empties the self.configuration
        """
        self.configuration = list()


def get_tag_by_itype(itype=None):
    """
    Small function to return the appropriate iface tag, given itype
    Note: This will be the name for the ifcfg file, ie ifcfg-<tag>
    @return: Equivalent iface_tag for itype
    @rtype: String
    """

    if itype == NetworkGraphConsts.VERTX_ITYPE_VLAN:
        return LinuxNetConf.VLAN_TAG
    elif itype == NetworkGraphConsts.VERTX_ITYPE_BRDG:
        return LinuxNetConf.BRIDGE_TAG
    elif itype == NetworkGraphConsts.VERTX_ITYPE_BOND:
        return LinuxNetConf.BOND_TAG
    elif itype == NetworkGraphConsts.VERTX_ITYPE_NIC:
        return LinuxNetConf.NIC_TAG
    else:
        return ''


def translate_bonding_opts(bonding_opts=None):
    """
    Small helper to translate the bonding options available in the
    netgraph to the output from the cat /proc/net/bonding/bondn
    """
    val = str(bonding_opts)
    opts = NetworkGraphConsts.SUPP_BOND_MODES
    if val not in opts.values():
        return False
    elif val == '0':
        txt = "Bonding Mode: load balancing (round-robin)"
    elif val == '1':
        txt = "Bonding Mode: fault-tolerance (active-backup)"
    elif val == '2':
        txt = "Bonding Mode: load balancing (xor)"
    elif val == '3':
        txt = "Bonding Mode: fault-tolerance (broadcast)"
    elif val == '4':
        txt = "Bonding Mode: IEEE 802.3ad Dynamic link aggregation"
    elif val == '5':
        txt = "Bonding Mode: transmit load balancing"
    elif val == '6':
        txt = "Bonding Mode: adaptive load balancing"
    else:
        ######NOTHING ELSE TESTED/SUPPORTED
        return False
    return txt
