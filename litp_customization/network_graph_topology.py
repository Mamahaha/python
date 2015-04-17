#!/usr/bin/env python

'''
@copyright: Ericsson AB
@since:     September 2012
@author:    Ray Brady
@summary:   Support for a IP Network Graphs or Topology Diagrams
            CXP 902 1403:  Network graphs
            Agile:         STORY-2878
'''

# import sys
from os import path as os_path
import re

#pylint: disable=R0911,R0912,R0915,C0302

import pydot
from pygraph.classes.digraph import digraph  # pylint: disable=E0611

from core.litp_resource import LitpResource
from core import LitpSite, LitpCluster, LitpNode, LitpInventory

from litp_ng_items.ng_props import NGBaseProps

from litp_graphs.network_graph_consts import NetworkGraphConsts
from litp_graphs.network_graph_props import NetworkGraphProps

from hardware.generic_system import GenericSystem
from hardware.generic_system_pool import GenericSystemPool
from operatingsystem.generic_os import GenericOS

from litp_common.logger.litp_log import createLitpLogger
logger = createLitpLogger(NetworkGraphConsts.logger_id)


class NetworkTopology(LitpResource):

    def allowed_children(self):
        '''
        Method to create a list of the allowed Children class names
        @return: List of the allowed Children class names
        @rtype: List of strings
        '''
        return [NetworkGraphConsts.KLASS_NG_ITEMS]

    def allowed_parents(self):
        '''
        Method to create a list of the allowed Parent class names
        @return: List of the allowed Parent class names
        @rtype: List of strings
        '''

        return [NetworkGraphConsts.KLASS_INV,
                NetworkGraphConsts.KLASS_SITE]

    def is_configurable(self):
        '''
        Method to determine if objects of this class are configurable
        ie if they produce data for the Configuration manager
        @return: True if Configurable, False otherwise
        @rtype: Boolean
        '''

        return False

    def allowed_properties(self):
        '''
        Method to collate the set of allowed properties for
        objects of this class
        @return: Full set of properties
        @rtype: Dictionary
        '''

        super_props = super(NetworkTopology, self).allowed_properties()
        my_props = NetworkGraphProps().get_allowed_properties()
        ap = dict(super_props.items() + my_props.items())
        return ap

    def _validate(self, parameters=None):
        '''
        Protected method to validate Network Topology properties
        @param parameters: Input parameters - defaults to None
        @type parameters: Dictionary
        @return: Dictionary containing key
                 L{NetworkGraphConsts.SUCCESS} on success or
                 L{NetworkGraphConsts.FAILURE} on failure
        @rtype: Dictionary
        '''

        if parameters is None:
            parameters = dict()

        preamble = self.__class__.__name__ + "._validate: "

        try:
            result = super(NetworkTopology, self)._validate(parameters)
            logger.debug('mmhh17-- validate OK: ' + str(parameters))

            if NetworkGraphConsts.SUCCESS in result:
                return self.process_properties()
            else:
                return {NetworkGraphConsts.FAILURE:
                        preamble + 'Validation error: ' + str(result)}

        except Exception as e:
            msg = (preamble + "Validate failed for %s with exception: %s") % \
                  (self.get_vpath(), str(e))
            logger.debug(msg)
            return {NetworkGraphConsts.FAILURE: msg}

    def nullify_graph_attrs(self):
        '''
        Simple utility method to nullify Digraph Dot complex attributes
        '''

        if self.nullify_each_time:
            self.the_digraph = None
            self.the_dot_graph = None

    def __init__(self):

        self.nullify_each_time = True
        '''
        @ivar: Instance variable to govern if the (complex)
               PyDot attributes should be nuked each time
               APIs are called or if they can be allowed
               persist
        @type: Boolean
        '''

        self.vtype_pattern = NetworkGraphConsts.EXP_LINE_START_ANCHR + \
                             NetworkGraphConsts.EXP_GROUP_OPEN + \
                             NetworkGraphConsts.EXP_LOGICAL_OR.join( \
                                    NetworkGraphConsts.SUPP_VERTX_STYPES) + \
                             NetworkGraphConsts.EXP_GROUP_CLOSE + \
                             '_'
        '''
        @ivar: Instance variable for Vertex type RE pattern
        @type: String
        '''

        self.props_klass = NetworkGraphProps()
        '''
        @ivar: Helper class to manage shared Definition/Inventory properties
        @type: NetworkGraphProps
        '''

        self.the_dot_graph = None
        '''
        @ivar: Instance variable for the Dot Graph
        @type: pydot.Graph
        '''

        self.dot_node_names = []
        '''
        @ivar: Instance variable for the list of Node names
        @type: List of Strings
        '''

        self.vertex_counts = None
        '''
        @ivar: Instance variable to track the edges count to/from Vertices
        @type: Dictionary
        '''

        self.the_digraph = None
        '''
        @ivar: Instance variable for the Digraph
        @type: pygraph.classes.digraph.digraph
        '''

        self.indent_count = 0
        '''
        @ivar: Instance variable for managing width of
               indentation of generated XML in gen_xml() method
        @type: Integer
        '''

        super(NetworkTopology, self).__init__()

        self.properties[NetworkGraphProps.PROP_GRAPH_NAME] = None
        self.properties[NetworkGraphProps.PROP_DIGRAPH_FNAME] = None
        self.properties[NetworkGraphProps.PROP_DIGRAPH_DATA] = None

    @property
    def vtype_re(self):
        '''
        Instance variable for Vertex type regular expression
        '''
        return re.compile(self.vtype_pattern)

    def process_properties(self):
        '''
        After object is instantiated & properties populated,
        utilize those properties: ie. process the input Dot data
        @return: Dictionary keyed on success|error
        @rtype: Dictionary
        '''

        preamble = self.__class__.__name__ + '.process_properties: '

        self.the_dot_graph = None

        response = self.process_net_graph_topology_data()

        self.nullify_graph_attrs()

        logger.debug((preamble + \
                      "Response from process_net_graph_topology_data: %s") % \
                      repr(response))

        return response

    def process_net_graph_topology_data(self):
        '''
        Utility worker method to process the Digraph Dot data
        @return: Dictionary keyed on success|error
        @rtype: Dictionary
        '''

        preamble = self.__class__.__name__ + \
                   '.process_net_graph_topology_data: '

        logger.debug(preamble + \
                     "Will import digraph data from File")

        import_file_result = self._import_digraph_file()

        if NetworkGraphConsts.FAILURE in import_file_result:
            return import_file_result

        elif NetworkGraphConsts.SKIPPED in import_file_result:

            logger.debug(preamble + \
                         "Will import digraph data from Property")
            import_data_result = self._process_digraph_data()

            if NetworkGraphConsts.FAILURE in import_data_result:
                return import_data_result

            elif NetworkGraphConsts.SKIPPED in import_data_result:

                logger.debug(preamble + \
                             "Will import digraph data from Children")
                import_kids_result = self._process_graph_kids()

                if NetworkGraphConsts.FAILURE in import_kids_result:
                    return import_kids_result

        if not self.the_dot_graph:
            self.nullify_graph_attrs()
            return {NetworkGraphConsts.SUCCESS: preamble + "Nothing to do"}
        else:
            strip_char = NetworkGraphConsts.EXP_DOUBLE_QUOTE
            graph_name = self.the_dot_graph.get_name().strip(strip_char)
            prop = NetworkGraphProps.PROP_GRAPH_NAME
            self.properties[prop] = graph_name

            graph_type = self.the_dot_graph.get_type()

            if graph_type != NetworkGraphConsts.SUPP_GRAPH_TYPE:
                err_str = preamble + "Unsupported Graph type " + graph_type
                logger.debug(err_str)
                return {NetworkGraphConsts.FAILURE: err_str}
            else:
                logger.debug((preamble + \
                              "Graph '%s' type: '%s'") % \
                             (graph_name, graph_type))

            (convert_result, self.the_digraph, self.dot_node_names) = \
                       self.convert_input_format_to_digraph(self.the_dot_graph)

            if NetworkGraphConsts.FAILURE in convert_result:
                return convert_result

        return {NetworkGraphConsts.SUCCESS: preamble + "success"}

    def _vld8_node(self, dot_node, dot_node_name):
        '''
        Utility method to validate the Vertex
        @param dot_node: Vertex (node)
        @type dot_node: pydot.Node
        @param dot_node_name: Vertex name tuple
        @type dot_node_name: String
        @return: Dictionary keyed on L{NetworkGraphConsts.FAILURE} on error,
                 keyed on L{NetworkGraphConsts.SUCCESS} on success
        @rtype: Dictionary
        '''

        preamble = self.__class__.__name__ + '._vld8_node: '

#       logger.debug("Will vld8 '%s'" % dot_node_name)

        stype = None

        try:
            (stype, _) = dot_node_name.split()
        except ValueError:
            err_str = preamble + 'Invalid vertex ' + dot_node_name
            logger.debug(err_str)
            return {NetworkGraphConsts.FAILURE: err_str}

        if not stype.lower() in NetworkGraphConsts.SUPP_VERTX_STYPES:
            err_str = (preamble + \
                       "Unsupported type '%s'. " + \
                       "Supported types are '%s' only") % \
                      (stype, ', '.join(NetworkGraphConsts.SUPP_VERTX_STYPES))
            logger.debug(err_str)
            return {NetworkGraphConsts.FAILURE: err_str}

        modes = NetworkGraphConsts.SUPP_BOND_MODES.keys() + \
                NetworkGraphConsts.SUPP_BOND_MODES.values()

        bootprotos = NetworkGraphConsts.SUPP_BOOTPROTOS

        attr_matrix = { \
          NetworkGraphConsts.VERTX_STYPE_NET: { \
                       NetworkGraphConsts.SUPP_NET_ATTR_TIPC: None,
                       NetworkGraphConsts.SUPP_NET_ATTR_TIPC_INTERNAL: None,
                       NetworkGraphConsts.SUPP_NET_ATTR_VCS_LLT: None,
                       NetworkGraphConsts.SUPP_NET_ATTR_VCS_LPR: None,
                       NetworkGraphConsts.SUPP_NET_ATTR_IP_OPTIONAL: None,
                       NetworkGraphConsts.SUPP_NET_ATTR_BOOT: None,
                       NetworkGraphConsts.SUPP_NET_ATTR_BOOTPROTO: bootprotos},
          NetworkGraphConsts.VERTX_STYPE_BOND: { \
                             NetworkGraphConsts.SUPP_BOND_ATTR_MODE: modes, NetworkGraphConsts.SUPP_BOND_ATTR_PRIMARY: None}}

        attrs = dot_node.get_attributes()
        if attrs:
            if stype in (NetworkGraphConsts.VERTX_STYPE_BOND,
                         NetworkGraphConsts.VERTX_STYPE_NET):

                allowed_attrs = attr_matrix[stype]

                logger.debug(preamble + "Attrs for %s: %s" % \
                             (dot_node_name, attrs))
                clean_attrs = self._process_dot_attrs(attrs)

                for c_key in clean_attrs:
                    c_val = clean_attrs[c_key]
                    #added for new attribute : primary
                    if c_key == NetworkGraphConsts.SUPP_BOND_ATTR_PRIMARY:
                        logger.debug('Ignore checking primary attribute for:' + str(attrs))
                        continue
                    #ended for new attribute : primary
                    if c_key in allowed_attrs:
                        allowed_vals = allowed_attrs[c_key]
                        logger.debug((preamble + \
                                      "Allowed values for '%s': '%s'") % \
                                      (c_key, allowed_vals))
                        if c_val and \
                           (not allowed_vals or (c_val not in allowed_vals)):
                            err_str = (preamble + \
                                       "Invalid attribute value '%s' " + \
                                       "on vertex '%s'") % \
                                       (c_val, dot_node_name)
                            logger.debug(err_str)
                            return {NetworkGraphConsts.FAILURE: err_str}
                    else:
                        err_str = (preamble + \
                                   "Invalid attribute '%s' on vertex '%s'") % \
                                   (c_key, dot_node_name)
                        logger.debug(err_str)
                        return {NetworkGraphConsts.FAILURE: err_str}
            else:
                # At time of writing no other Vertex type
                # is allowed have attributes
                err_str = (preamble + \
                           "No attributes allowed for Vertex " + \
                           "type '%s': '%s'") % \
                           (stype, dot_node_name)
                logger.debug(err_str)
                return {NetworkGraphConsts.FAILURE: err_str}

        return {NetworkGraphConsts.SUCCESS: 'success'}

    def convert_input_format_to_digraph(self, the_dot_graph):
        '''
        Utility method to map a Input Format (Dot) graph to a Digraph
        @param the_dot_graph: The loaded DOT graph
        @type the_dot_graph: pydot.Graph
        @return: 3-tuple:
                 1. Dictionary keyed on L{NetworkGraphConsts.FAILURE} on error,
                    keyed on L{NetworkGraphConsts.SUCCESS} on success
                 2. Populated Digraph
                 3. List of Graph nodes
        @rtype: 3-typle: Dictionary, pygraph.classes.digraph, List
        '''

        preamble = self.__class__.__name__ + \
                   '.convert_input_format_to_digraph: '

        if the_dot_graph == None:
            return ({NetworkGraphConsts.FAILURE:
                     preamble + 'No Dot graph imported'}, None, None)

        the_digraph = digraph()
        err_str = None
        dot_node_names = []
        dot_nodes = the_dot_graph.get_nodes()
        strip_char = NetworkGraphConsts.EXP_DOUBLE_QUOTE

        for dot_node in dot_nodes:
            dot_node_name = dot_node.get_name().strip(strip_char)
            logger.debug('mmhh12-- dot node name: ' + dot_node_name)
            vld8_result = self._vld8_node(dot_node, dot_node_name)
            if NetworkGraphConsts.FAILURE in vld8_result:
                return (vld8_result, None, None)
            else:
                the_digraph.add_node(dot_node_name)
                dot_node_names.append(dot_node_name)

        net = NetworkGraphConsts.VERTX_STYPE_NET
        vlan = NetworkGraphConsts.VERTX_STYPE_VLAN
        brdg = NetworkGraphConsts.VERTX_STYPE_BRDG
        bond = NetworkGraphConsts.VERTX_STYPE_BOND
        nic = NetworkGraphConsts.VERTX_STYPE_NIC

        # Matrix of allowed before/after relationships per vertex type.
        edge_matrix = {net: {'before': [],
                             'after': [vlan, brdg, bond, nic]},
                       vlan: {'before': [net, brdg],
                              'after': [brdg, bond, nic]},
                       brdg: {'before': [net, vlan],
                              'after': [vlan, bond, nic]},
                       bond: {'before': [net, vlan, brdg],
                              'after': [nic]},
                       nic: {'before': [net, vlan, brdg, bond],
                             'after': []}
                      }
        dot_edges = the_dot_graph.get_edges()

        logger.debug((preamble + "dot_edges %s") % \
                          dot_edges)

        for dot_edge in dot_edges:
            edge_src = dot_edge.get_source().strip(strip_char)
            edge_dst = dot_edge.get_destination().strip(strip_char)
            if not edge_src in dot_node_names:
                err_str = "Invalid source vertex '%s' in relationship" % \
                          edge_src
                break
            elif not edge_dst in dot_node_names:
                err_str = "Invalid destination vertex '%s' in relationship" % \
                          edge_dst
                break
            logger.debug('mmhh--edge src: ' + edge_src)
            logger.debug('mmhh--edge dst: ' + edge_dst)
            (src_type, _) = edge_src.split(' ', 1)
            (dst_type, _) = edge_dst.split(' ', 1)

            logger.debug((preamble + "Src: %s  Dst: %s") % \
                         (src_type, dst_type))

            logger.debug((preamble + "relationship %s -> %s") % \
                          (edge_src, edge_dst))

            if dst_type not in edge_matrix[src_type]['after']:
                err_str = "Invalid child in relationship %s -> %s" % \
                          (edge_src, edge_dst)
                break
            elif src_type not in edge_matrix[dst_type]['before']:
                err_str = "Invalid parent in relationship %s -> %s" % \
                          (edge_src, edge_dst)
                break
            else:
                the_digraph.add_edge((edge_src, edge_dst))

        if err_str:
            msg = preamble + err_str
            logger.debug(msg)
            return ({NetworkGraphConsts.FAILURE: msg}, None, None)
        else:
            return ({NetworkGraphConsts.SUCCESS: 'success'},
                    the_digraph,
                    dot_node_names)

    def _vld8_file_digraph_data(self, file_name):
        '''
        Private method to validate the contents of an input digraph (DOT) file
        @param file_name: The input file name
        @type file_name: String
        @return: Error msg if error, None otherwise
        @rtype: String
        '''

        err_msg = None
        file_data = None

        try:
            with open(file_name, 'r') as file_handle:
                file_data = file_handle.read()
        except IOError as ioe:
            return "Error opening & reading '%s': %s" % \
                   (file_name, str(ioe))

        prop_name = NetworkGraphProps.PROP_DIGRAPH_DATA
        regex = self.props_klass.get_prop_re(prop_name)

        matcher = re.compile(regex)

        if not matcher.match(file_data):
            err_msg = "File data does not match Digraph regular expression"

        return err_msg

    def gen_graph_from_file(self, file_name):
        '''
        Helper method to generate the Digraph instance
        from the named input file
        @param file_name: Input (absolute) file name
        @type file_name: String
        @return Digraph instance
        @rtype: pydot.Graph
        '''
        return pydot.graph_from_dot_file(file_name)

    def _import_digraph_file(self):
        '''
        Utility method to read in the contents of the file
        named in the L{NetworkGraphProps.PROP_DIGRAPH_FNAME} property
        @return: Dictionary keyed on L{NetworkGraphConsts.FAILURE} on error,
                 keyed on L{NetworkGraphConsts.SUCCESS} on success
        @rtype: Dictionary
        '''

        preamble = self.__class__.__name__ + '._import_digraph_file: '

        result = {}
        err_str = None

        prop = NetworkGraphProps.PROP_DIGRAPH_FNAME
        if self.properties[prop] != None:

            self.the_dot_graph = None
            abs_file_name = self.properties[prop]
            logger.debug(preamble + "About to stat digraph file: " + \
                         abs_file_name)

            if os_path.exists(abs_file_name) and os_path.isfile(abs_file_name):

                error = self._vld8_file_digraph_data(abs_file_name)

                if error:
                    msg = preamble + error
                    result[NetworkGraphConsts.FAILURE] = msg
                    logger.debug(msg)
                else:
                    self.the_dot_graph = self.gen_graph_from_file( \
                                                                abs_file_name)

                    if self.the_dot_graph == None or \
                       not isinstance(self.the_dot_graph, pydot.Graph):
                        err_str = "Error loading dot file: " + abs_file_name
                    else:
                        logger.debug(preamble + \
                                     "Successfully loaded file: " + \
                                     abs_file_name)
            else:
                err_str = "File does not exist: " + abs_file_name
        else:
            msg = preamble + "skipped"
            logger.debug(msg)
            return {NetworkGraphConsts.SKIPPED: msg}

        if err_str:
            msg = preamble + err_str
            result[NetworkGraphConsts.FAILURE] = msg
            logger.debug(msg)
        else:
            result[NetworkGraphConsts.SUCCESS] = preamble + "Success"

        return result

    def _process_digraph_data(self):
        '''
        Utility method to process the text block as specified in the
        L{NetworkGraphProps.PROP_DIGRAPH_DATA} property
        @return: Dictionary keyed on L{NetworkGraphConsts.FAILURE} on error,
                 keyed on L{NetworkGraphConsts.SUCCESS} on success
        @rtype: Dictionary
        '''

        preamble = self.__class__.__name__ + '._process_digraph_data: '

        result = {}
        err_str = None

        prop_name = NetworkGraphProps.PROP_DIGRAPH_DATA
        prop_value = self.properties[prop_name]
        if prop_value != None:
            self.the_dot_graph = pydot.graph_from_dot_data(str(prop_value))

            if self.the_dot_graph == None or \
               not isinstance(self.the_dot_graph, pydot.Graph):
                err_str = "Error reading '%s' data: '%s'" % \
                          (prop_name, prop_value)
            else:
                logger.debug(preamble + \
                          "Successfully processed prop_name: " + \
                          prop_name + '; prop_value: ' + prop_value)
#               sys.stderr.write("the_dot_graph: %s" % \
#                                self.the_dot_graph.to_string())
        else:
            logger.debug(preamble + 'skipped prop_name: ' + prop_name)
            result[NetworkGraphConsts.SKIPPED] = \
                                         preamble + "No digraph data available"

        if err_str:
            msg = preamble + err_str
            result[NetworkGraphConsts.FAILURE] = msg
            logger.debug(msg)
        else:
            result[NetworkGraphConsts.SUCCESS] = preamble + "Success"

        return result

    def _process_csl_edges(self, item_id, csl, place_item_first=True):
        '''
        Utility method to split a comma-separated-list of
        item identifiers, remove extraneous leading or trailing whitespace
        and create DOT "edge" statements
        @param item_id: Source vertex Item id
        @type item_id: String
        @param csl: Comma-separated-list to be parsed
        @type csl: String
        @param place_item_first: Which should be printed 1st:
                                 CSL value(s) or Item Id?
        @type place_item_first: Boolean
        @return: List of DOT Edge statements, or None
        @rtype: List of Strings
        '''

        preamble = self.__class__.__name__ + '._process_csl_edges: '

        edges = None
        if csl != '':
            logger.debug((preamble + "Item: '%s', CSL: '%s'") % \
                         (item_id, csl))

            tokens = csl.split(',')

            for token in tokens:
                dep = self._prep_item_id(token.lstrip().rstrip())
                if place_item_first:
                    edge = '"%s" -> "%s";' % (item_id, dep)
                else:
                    edge = '"%s" -> "%s";' % (dep, item_id)

                logger.debug(preamble + 'Edge: ' + edge)

                if not edges:
                    edges = []
                edges.append(edge)

        return edges

    def _prep_item_id(self, item_id):
        '''
        Utility method to pre-process an Item identifier
        @param item_id: Raw Item identifier
        @type item_id: String
        @return: Post processed Item id
        @rtype: String
        '''
        return item_id.replace('_', ' ', 1)

    def get_bond_children(self, bond_name):
        '''
        Utility method to get the set of children of the bond iface
        @return: list of nic bonded to this bond interface name
        @rtype: List
        '''
        preamble = self.__class__.__name__ + '.get_bond_children2: '

        ifaces = []

        if self.the_digraph == None:
            response = self.process_net_graph_topology_data()
            if NetworkGraphConsts.FAILURE in response:
                logger.debug(preamble + repr(response))

        # check the tag
        from litp_netconf.linux_net_config import LinuxNetConf
        sz_bond_tag = len(LinuxNetConf.BOND_TAG)
        # just return the empty list in case the tags don't match
        if bond_name[:sz_bond_tag] != LinuxNetConf.BOND_TAG:
            return ifaces
        bond_net_name = bond_name[:sz_bond_tag] + " " + bond_name[sz_bond_tag:]

        nic_type = NetworkGraphConsts.VERTX_STYPE_NIC

        nics = self.get_vrtx_neighbor_by_type(bond_net_name, nic_type)
        for nic in nics:
            iface = self._get_nic_iface(nic["name"])
            log_msg = "Direct (NIC) i/face name: %s" % iface
            logger.debug(preamble + log_msg)
            ifaces.append(iface)
        self.nullify_graph_attrs()
        return ifaces

    def _process_graph_kids(self):
        '''
        Utility method to process the set of children NG items
        @return: Dictionary keyed on L{NetworkGraphConsts.FAILURE} on error,
                 keyed on L{NetworkGraphConsts.SUCCESS} on success
        @rtype: Dictionary
        '''

        preamble = self.__class__.__name__ + '._process_graph_kids: '

        result = {}

        from litp_ng_items.ng_base import NGBase

        # Get list of immediate children that are NGBase extensions
        ng_items = [i for i in self.get_children() if \
            isinstance(i, NGBase)]

        for ng_item in ng_items:
            if not self.vtype_re.match(ng_item.id):
                msg = "Invalid NG Item id '%s'" % ng_item.id
                logger.debug(preamble + msg)
                result[NetworkGraphConsts.FAILURE] = preamble + msg
                return result

        graph_body = ''
        for ng_item in ng_items:
            attrs = ''

            logger.debug(preamble + "Processing " + ng_item.id)

            if ng_item.type == NetworkGraphConsts.VERTX_ITYPE_BOND:
                bond_attrs = ''
                for sb_attr in NetworkGraphConsts.SUPP_BOND_ATTRS:
                    logger.debug('mmhh16-- add attr: ' + str(sb_attr) + '; value: ' + str(ng_item.properties))
                    if sb_attr in ng_item.properties and \
                       ng_item.properties[sb_attr] != None:

                        sb_attr_val = ng_item.properties[sb_attr]

# Put this in when > 1 supported Bond attribute
#                           if bond_attrs != '':
#                               bond_attrs += ','

                        bond_attrs += '%s="%s"' % (sb_attr, sb_attr_val)

                if bond_attrs != '':
                    attrs = ' [' + bond_attrs + ']'

            elif ng_item.type == NetworkGraphConsts.VERTX_ITYPE_NET:
                this_net_attrs = ''
                allowed_attrs = NetworkGraphConsts.SUPP_NET_ATTRS
                for allowed_attr in allowed_attrs:
                    if allowed_attr in ng_item.properties and \
                        ng_item.properties[allowed_attr] != None:

                        if ng_item.properties[allowed_attr].lower() == 'true':
                            if this_net_attrs != '':
                                this_net_attrs += ','
                            this_net_attrs += allowed_attr
                        elif allowed_attr == \
                                    NetworkGraphConsts.SUPP_NET_ATTR_BOOTPROTO:
                            if this_net_attrs != '':
                                this_net_attrs += ','
                            val = ng_item.properties[allowed_attr].lower()
                            this_net_attrs += '%s=%s' % \
                                              (allowed_attr, val)

                if this_net_attrs != '':
                    attrs = ' [' + this_net_attrs + ']'

            graph_addage = '  "%s"%s;\n' % \
                           (self._prep_item_id(ng_item.id), attrs)
            logger.debug(preamble + "Will add to graph:  " + graph_addage)

            graph_body += graph_addage

        # --- Children first ---
        kids_found = False
        kids_edges = []
        for ng_item in ng_items:

            if NGBaseProps.PROP_KIDS in ng_item.properties and \
               ng_item.properties[NGBaseProps.PROP_KIDS] != None:

                logger.debug(preamble + "Children value: " + \
                             ng_item.properties[NGBaseProps.PROP_KIDS])

                kids_found = True

                item_id = self._prep_item_id(ng_item.id)
                kids_csl = str(ng_item.properties[NGBaseProps.PROP_KIDS])
                edges = self._process_csl_edges(item_id, kids_csl)
                if edges:
                    kids_edges += edges

        # --- Parents next ---
        parents_edges = []
        for ng_item in ng_items:

            if NGBaseProps.PROP_PARENTS in ng_item.properties and \
               ng_item.properties[NGBaseProps.PROP_PARENTS] != None:

                logger.debug(preamble + "Parents value: " + \
                             ng_item.properties[NGBaseProps.PROP_PARENTS])

                item_id = self._prep_item_id(ng_item.id)
                parents_csl = str(ng_item.properties[NGBaseProps.PROP_PARENTS])
                edges = self._process_csl_edges(item_id, parents_csl, False)
                if edges:
                    parents_edges += edges

        # --- Confirm Children match parents
        if kids_found:

            kids_edges.sort()
            parents_edges.sort()

            if cmp(kids_edges, parents_edges) != 0:
                logger.debug((preamble + "From Children: %s") % kids_edges)
                logger.debug((preamble + "From Parents: %s") % parents_edges)

                msg = "Inconsistent parent & children relationship properties"
                logger.debug(preamble + msg)
#               result[NetworkGraphConsts.FAILURE] = preamble + msg
#               return result

            # Pick one set of edges ... and generate Graph body
            for edge in kids_edges:
                graph_body += "  %s\n" % edge

            graph_text = str('digraph "From NG Items" {\n' + \
                             graph_body + \
                             '}')

            logger.debug(preamble + "Generated from NG Items: " + graph_text)
            self.the_dot_graph = pydot.graph_from_dot_data(graph_text)

#           Re-instate when this is possible
#           if self.the_dot_graph == None or \
#              not isinstance(self.the_dot_graph, pydot.Graph):
#               err_str = "Error loading generated NG items data"
#               logger.debug(err_str + (": '%s'" % graph_text))
#               result[NetworkGraphConsts.FAILURE] = preamble + err_str
#           else:
            logger.debug(preamble + "Successfully processed NG Items")
            result[NetworkGraphConsts.SUCCESS] = preamble + "Success"
        else:
            err_str = preamble + "No relationship data apparent"
            logger.debug(err_str)
            result[NetworkGraphConsts.SUCCESS] = err_str
        return result

    def _map_neighbours_to_peers(self, neighbors):
        '''
        Simple utility method to convert basic Digraph "neighbour"
        elements into richer Response items
        @param neighbors: List of Digraph directly accessible neighbours
        @type neighbors: List
        @return: List of dictionary descriptors;
                 empty list if no (valid) neighbours
        @rtype: List of dictionaries
        '''

        vertices = []

        for neighbor in neighbors:
            vertex = self.map_node_to_vertex(neighbor)
            if vertex:
                vertices.append(vertex)

        return vertices

    def map_node_to_vertex(self, node, itype=None):
        '''
        Utility method to map a simple Node label
        into a richer / more verbose Vertex description
        @param node: The Digraph node string
        @type String
        @param itype: Optional integer Type
        @type itype: Integer
        @return: Dictionary describing Node / Vertex
        @rtype: Dictionary
        '''

        stype = None
        name = None

        try:
            (stype, name) = node.split()
        except ValueError:
            logger.debug("Invalid vertex name: '%s'" % node)
            return None

        stype_l = stype.lower()

        if itype == None:
            if stype_l in NetworkGraphConsts.SUPP_VERTX_TYPES_MAP:
                itype = NetworkGraphConsts.SUPP_VERTX_TYPES_MAP[stype_l]
            else:
                itype = -1   # Unknown

        return {'itype': itype,
                'name': name,
                'value': node,
                'stype': stype_l}

    def get_vertex_peers(self, vertex_name):
        '''
        Public method to fetch the set of connected / peer vertices
        adjacent to a particular vertex
        @param vertex_name: Vertex name (Tuple of type & name)
        @type vertex_name: String
        @return: List of dictionaries, describing adjacent vertices
        @rtype: List of dictionaries
        '''

        preamble = self.__class__.__name__ + '.get_vertex_peers: '

        if self.the_digraph == None:
            response = self.process_net_graph_topology_data()
            if NetworkGraphConsts.FAILURE in response:
                logger.debug(preamble + repr(response))

        vertices = []
        log_msg = ''

        if self.the_digraph == None:
            log_msg = 'No Digraph available'
        else:
            if not vertex_name in self.dot_node_names:
                log_msg = 'Invalid vertex: ' + vertex_name
            else:
                neighbors = self.the_digraph.neighbors(vertex_name)
                vertices = self._map_neighbours_to_peers(neighbors)
                log_msg = 'Neighboring Peer Vertices retrieved'

        logger.debug(preamble + log_msg)

        self.nullify_graph_attrs()

        return vertices

    def get_vertices_by_type(self, vtype):
        '''
        Public method to fetch a set of Vertex nodes based on
        one of the 5 supported Vertex types.
        @param vtype: Vertex enumerated type
        @type vtype: Integer
        @return: List of dictionaries describing Vertices
        @rtype: List of dictionaries
        '''

        preamble = self.__class__.__name__ + '.get_vertices_by_type: '

        if self.the_digraph == None:
            response = self.process_net_graph_topology_data()
            if NetworkGraphConsts.FAILURE in response:
                logger.debug(preamble + repr(response))

        vertices = []
        log_msg = ''

        if self.the_digraph == None:
            log_msg = 'No Digraph available'
        else:
            if vtype not in NetworkGraphConsts.SUPP_VERTX_ITYPES:
                log_msg = 'Unsupported vertex type: ' + str(vtype)
            else:
                vtype_str = NetworkGraphConsts.SUPP_VERTX_TYPES_MAP[vtype]

                log_msg = 'Will fetch all nodes of type ' + vtype_str

                dot_nodes = self.the_dot_graph.get_nodes()

                strip_char = NetworkGraphConsts.EXP_DOUBLE_QUOTE
                for dot_node in dot_nodes:
                    dot_node_name = dot_node.get_name().strip(strip_char)

                    if dot_node_name.startswith(vtype_str):
                        vertix = self.map_node_to_vertex(dot_node_name, vtype)
                        if vertix:
                            vertices.append(vertix)

        logger.debug(preamble + log_msg)

        self.nullify_graph_attrs()

        return vertices

    def _setup_vertex_counts(self):
        '''
        Utility method to calculate the current Vertex counts
        '''

        if self.vertex_counts != None:
            return

        self.vertex_counts = {}
        for dot_node in self.dot_node_names:
            if dot_node not in self.vertex_counts:
                self.vertex_counts[dot_node] = {'src': 0, 'dst': 0}

        strip_char = NetworkGraphConsts.EXP_DOUBLE_QUOTE

        dot_edges = self.the_dot_graph.get_edges()
        for dot_edge in dot_edges:
            edge_src = dot_edge.get_source().strip(strip_char)
            edge_dst = dot_edge.get_destination().strip(strip_char)
            self.vertex_counts[edge_src]['src'] += 1
            self.vertex_counts[edge_dst]['dst'] += 1

    def _get_vertices_wrkr(self, anchor, stype=None):
        '''
        Utility method to fetch a set of Vertex nodes that are the
        starting/terminating peripheral leaves on the Digraph
        @param anchor: Headmost or Hindmost vertices requested
        @type anchor: String
        @param stype: Filter {hind|head} most vertices by (string) type
        @type stype: String
        @return: List of dictionaries describing Vertices
        @rtype: List of dictionaries
        '''

        preamble = self.__class__.__name__ + '._get_vertices_wrkr: '

        if self.the_digraph == None:
            response = self.process_net_graph_topology_data()
            if NetworkGraphConsts.FAILURE in response:
                logger.debug(preamble + repr(response))

        vertices = []

        if self.the_digraph == None:
            logger.debug(preamble + 'No Digraph available')
            return vertices

        if anchor == NetworkGraphConsts.GRAPH_ANCHOR_HEAD:
            periphery = 'src'
            opposite_periphery = 'dst'
        elif anchor == NetworkGraphConsts.GRAPH_ANCHOR_HIND:
            periphery = 'dst'
            opposite_periphery = 'src'
        else:
            logger.debug(preamble + ("Unsupported anchor '%s'" % anchor))
            return vertices

        self._setup_vertex_counts()

        for dot_node in self.vertex_counts:
            if self.vertex_counts[dot_node][opposite_periphery] == 0 and \
               self.vertex_counts[dot_node][periphery] > 0:

                vertix = None
                if stype:
                    if dot_node.startswith(stype):
                        vertix = self.map_node_to_vertex(dot_node)
                else:
                    vertix = self.map_node_to_vertex(dot_node)

                if vertix:
                    vertices.append(vertix)

        self.nullify_graph_attrs()

        return vertices

    def _get_starting_vertices_wrkr(self, stype=None):
        '''
        Utility method to fetch a set of Vertex nodes that are the
        starting peripheral leaves on the Digraph.
        @param stype: Filter {hind|head} most vertices by (string) type
        @type stype: String
        @return: List of dictionaries describing Starting Vertices
        @rtype: List of dictionaries
        '''

        preamble = self.__class__.__name__ + '._get_starting_vertices_wrkr: '

        if stype and stype not in NetworkGraphConsts.SUPP_VERTX_STYPES:
            logger.debug(preamble + 'Unsupported vertex type: ' + stype)
            return []

        return self._get_vertices_wrkr(NetworkGraphConsts.GRAPH_ANCHOR_HEAD,
                                       stype)

    def get_starting_vertices(self):
        '''
        Public method to fetch a set of Vertex nodes that are the
        starting or peripheral leaves on the Digraph.
        @return: List of dictionaries describing Vertices
        @rtype: List of dictionaries
        '''

        return self._get_starting_vertices_wrkr()

    def get_terminating_nic_vertices(self):
        '''
        Public method to fetch a set of Vertex nodes that are the
        terminating or peripheral leaves on the Digraph,
        which are all of type 'nic'
        @return: List of dictionaries describing nic Vertices
        @rtype: List of dictionaries
        '''

        return self._get_vertices_wrkr(NetworkGraphConsts.GRAPH_ANCHOR_HIND,
                                       NetworkGraphConsts.VERTX_STYPE_NIC)

    def _process_dot_attrs(self, attrs):
        '''
        Private method to process the Vertex attributes before
        returning them to the caller
        @param attrs: The 'raw' (DOT) attributes
        @type attrs: Dictionary
        @return: The post-processed attributes
        @rtype: Dictionary
        '''

        new_attrs = {}
        for key in attrs:

            new_key = key.strip(NetworkGraphConsts.EXP_DOUBLE_QUOTE)

            if key in attrs and attrs[key] != None:
                orig_val = attrs[key]
                new_val = orig_val.strip(NetworkGraphConsts.EXP_DOUBLE_QUOTE)
            else:
                new_val = None

            if new_key == NetworkGraphConsts.SUPP_BOND_ATTR_MODE:
                if new_val in NetworkGraphConsts.SUPP_BOND_MODES.values():
                    pass
                elif new_val in NetworkGraphConsts.SUPP_BOND_MODES:
                    new_val = NetworkGraphConsts.SUPP_BOND_MODES[new_val]

            new_attrs[new_key] = new_val

        return new_attrs

    def get_vertex_attrs(self, vertex_name):
        '''
        @param vertex_name: Vertex name (Tuple of type & name)
        @type vertex_name: String
        @return: None on error, Dictionary of Vertex attributes on success
        @rtype: Dictionary
        '''

        preamble = self.__class__.__name__ + '.get_vertex_attrs: '
        logger.debug('mmhh4-- vertex name: ' + vertex_name)
        return_attrs = None

        if self.the_digraph == None:
            response = self.process_net_graph_topology_data()
            if NetworkGraphConsts.FAILURE in response:
                logger.debug(preamble + repr(response))

        if self.the_dot_graph == None:
            logger.debug(preamble + 'No Dot data available')
            return None
        elif not vertex_name in self.dot_node_names:
            logger.debug(preamble + 'Invalid vertex: ' + vertex_name)
        else:
            full_name = NetworkGraphConsts.EXP_DOUBLE_QUOTE + \
                        vertex_name + \
                        NetworkGraphConsts.EXP_DOUBLE_QUOTE

            node_list = self.the_dot_graph.get_node(full_name)

            attrs = node_list[0].get_attributes()
            logger.debug(preamble + "Attrs for %s: %s" % \
                         (vertex_name, attrs))
            if attrs:
                clean_attrs = self._process_dot_attrs(attrs)
                logger.debug(preamble + "Cleaned Attrs for %s: %s" % \
                             (vertex_name, clean_attrs))
                return_attrs = clean_attrs

        self.nullify_graph_attrs()

        return return_attrs

    def get_vrtx_neighbor_by_type(self, vertex_name, neighbor_type):
        '''
        Helper method to get vertices of a particular type
        that neighbour a specific Vertex
        @param vertex_name: Vertex name
        @type vertex_name: String
        @param neighbor_type: Neighbour(s) type
        @type neighbor_type: String
        @return: List of (filtered) Vertices
        @rtype: List of dictionaries
        '''

        preamble = self.__class__.__name__ + '.get_vrtx_neighbor_by_type: '

        all_neighbors = self.the_digraph.neighbors(vertex_name)

        filtered_neighbors = []
        for neighbor in all_neighbors:
            if neighbor.startswith(neighbor_type):
                filtered_neighbors.append(neighbor)

        vertices = self._map_neighbours_to_peers(filtered_neighbors)

        log_msg = "Found '%s' vertices %s neighbors of %s" % \
                  (neighbor_type, repr(vertices), vertex_name)

        logger.debug(preamble + log_msg)

        return vertices

    def traverse_net_for_ifaces(self, net_name):
        '''
        Private helper method to walk/traverse a Network
        generating the possible (Level 2) Interface names
        @param net_name: Network name
        @type net_name: String
        @return: List of Interface name
        @rtype: List of Strings
        '''

        preamble = self.__class__.__name__ + '.traverse_net_for_ifaces: '

        vlan_type = NetworkGraphConsts.VERTX_STYPE_VLAN
        brd_type = NetworkGraphConsts.VERTX_STYPE_BRDG
        bnd_type = NetworkGraphConsts.VERTX_STYPE_BOND
        nic_type = NetworkGraphConsts.VERTX_STYPE_NIC

        logger.debug((preamble + \
                      "Looking for Type %s neighbor of %s") % \
                     (NetworkGraphConsts.VERTX_STYPE_VLAN, net_name))

        ifaces = []

        vlans = self.get_vrtx_neighbor_by_type(net_name, vlan_type)
        for vlan in vlans:

            logger.debug((preamble + \
                          "Looking for Type %s neighbor of %s") % \
                         (brd_type, vlan['value']))
            brgs = self.get_vrtx_neighbor_by_type(vlan['value'], brd_type)
            if brgs:
                for brg in brgs:
                    iface = "br%s.%s" % (brg['name'], vlan['name'])
                    log_msg = "Bridged VLAN i/face name: '%s'" % iface
                    logger.debug(preamble + log_msg)
                    ifaces.append(iface)

            logger.debug((preamble + \
                          "Looking for Type %s neighbor of %s") % \
                         (bnd_type, vlan['value']))
            bnds = self.get_vrtx_neighbor_by_type(vlan['value'], bnd_type)
            if bnds:
                for bnd in bnds:
                    iface = "bond%s.%s" % (bnd['name'], vlan['name'])
                    log_msg = "Bonded VLAN i/face name: %s" % iface
                    logger.debug(preamble + log_msg)
                    ifaces.append(iface)

            logger.debug((preamble + \
                          "Looking for Type %s neighbor of %s") % \
                         (nic_type, vlan['value']))
            nics = self.get_vrtx_neighbor_by_type(vlan['value'], nic_type)
            if nics:
                for nic in nics:
                    iface = "%s.%s" % (self._get_nic_iface(nic['name']),
                                       vlan['name'])
                    log_msg = "Direct VLAN i/face name: %s" % iface
                    logger.debug(preamble + log_msg)
                    ifaces.append(iface)

        logger.debug((preamble + \
                      "Looking for Type %s neighbor of %s") % \
                     (brd_type, net_name))
        brgs = self.get_vrtx_neighbor_by_type(net_name, brd_type)
        for brg in brgs:
            iface = "br%s" % brg['name']
            log_msg = "Bridged i/face name: %s" % iface
            logger.debug(preamble + log_msg)
            ifaces.append(iface)

        logger.debug((preamble + \
                      "Looking for Type %s neighbor of %s") % \
                     (bnd_type, net_name))
        bnds = self.get_vrtx_neighbor_by_type(net_name, bnd_type)
        for bnd in bnds:
            iface = "bond%s" % bnd['name']
            log_msg = "Bonded i/face name: %s" % iface
            logger.debug(preamble + log_msg)
            ifaces.append(iface)

        logger.debug((preamble + \
                      "Looking for Type %s neighbor of %s") % \
                     (nic_type, net_name))
        nics = self.get_vrtx_neighbor_by_type(net_name, nic_type)
        for nic in nics:
            iface = self._get_nic_iface(nic["name"])
            log_msg = "Direct (NIC) i/face name: %s" % iface
            logger.debug(preamble + log_msg)
            ifaces.append(iface)

        return ifaces

    def get_interfaces_by_network_name(self, net_name):
        '''
        Public method to fetch an Interface name for a NetGraph
        given a Network name
        @param net_name: Network Name
        @type net_name: String
        @return: List of Interfaces
        @rtype: List of Strings
        '''

        preamble = self.__class__.__name__ + \
                   '.get_interfaces_by_network_name: '

        ifaces = []

        if self.the_digraph == None:
            response = self.process_net_graph_topology_data()
            if NetworkGraphConsts.FAILURE in response:
                logger.debug(preamble + repr(response))

        if self.the_digraph == None:
            logger.debug(preamble + 'No Digraph data available')
        elif net_name not in self.dot_node_names:
            log_msg = 'Invalid Network vertex: ' + net_name
            logger.debug(preamble + log_msg)
        else:
            log_msg = "Will gen. Interface for Network '%s'" % net_name
            logger.debug(preamble + log_msg)
            ifaces = self.traverse_net_for_ifaces(net_name)

        self.nullify_graph_attrs()
        return ifaces

    @staticmethod
    def get_network_topology(item):
        '''
        Static public method to retrieve the NetworkTopology
        @param item: The item in the Landscape to start the search from
        @type item: LitpItem extension
        @return: List of NetworkTopology instances
        @rtype: List of NetworkTopology objects
        '''

        from litp_netconf.linux_net_config import LinuxNetConf

        preamble = 'NetworkTopology.get_network_topology: '

        type1 = 'hardware.generic_system.GenericSystem'
        type2 = 'hardware.generic_system_pool.GenericSystemPool'
        type3 = 'core.litp_node.LitpNode'
        type4 = 'core.litp_site.LitpSite'
        type5 = 'core.litp_inventory.LitpInventory'

        search_types = []
        if isinstance(item, LinuxNetConf):
            search_types = [('upward', type1),
                            ('across', type2),
                            ('upward', type3),
                            ('upward', type4),
                            ('upward', type5)]
        elif isinstance(item, GenericSystem):
            search_types = [('here', None),
                            ('across', type2),
                            ('upward', type3),
                            ('upward', type4),
                            ('upward', type5)]
        elif isinstance(item, GenericOS):
            search_types = [('downward', type1),
                            ('across', type2),
                            ('upward', type3),
                            ('upward', type4),
                            ('upward', type5)]
        elif isinstance(item, LitpNode):
            search_types = [('downward', type1),
                            ('across', type2),
                            ('here', None),
                            ('upward', type4),
                            ('upward', type5)]
        elif isinstance(item, LitpCluster):
            search_types = [('upward', type4),
                            ('upward', type5)]
        elif isinstance(item, LitpSite):
            search_types = [('here', None),
                            ('upward', type5)]
        elif isinstance(item, LitpInventory):
            search_types = [('here', None)]
        elif isinstance(item, GenericSystemPool):
            search_types = [('here', None),
                            ('upward', type5)]

        if search_types == []:
            logger.debug((preamble + \
                          "Type '%s' not supported for Network " + \
                          "Topology name retrieval") %
                         item.__class__.__name__)
            return []

        logger.debug(preamble + \
                     "--- Searching from item of type " + \
                     item.__class__.__name__ + \
                     ' ---')

        nett_type = NetworkGraphConsts.KLASS_NETG_TOP.split('.')[-1]

        sys_pool = None
        the_netts = []
        inv_item = None
        pools = None

        for (direction, i_type) in search_types:

            nett_list = None

            if direction == 'across':
                if inv_item == None:
                    inv_item = item._lookup_parents(types=type5)

                if inv_item and sys_pool:
                    pools = inv_item._lookup_children(types=i_type,
                                                      names=sys_pool)
                if pools:
                    search_item = inv_item.get_item_by_path(pools[0])

            elif direction == 'upward':
                logger.debug(preamble + "Searching for parents " + i_type)
                search_item = item._lookup_parents(types=i_type)

            elif direction == 'downward':
                logger.debug(preamble + "Searching for kids " + i_type)
                children = item._lookup_children(types=i_type)
                if not children or len(children) != 1:
                    logger.debug((preamble + \
                                  "Indeterminate number of '%s' found") % \
                                  i_type)
                    return []
                else:
                    search_item = item.get_item_by_path(children[0])

            elif direction == 'here':
                search_item = item

            if search_item:
                if isinstance(search_item, GenericSystem):
                    if 'pool' in search_item.properties:
                        sys_pool = search_item.properties['pool']

                logger.debug((preamble + \
                              "Will fetch %s from Item of type %s") % \
                              (nett_type, search_item.__class__.__name__))

                # Get list of NetworkTopology immediate children
                nett_list = [i for i in search_item.get_children() if \
                    isinstance(i, NetworkTopology)]

            if nett_list:
                the_netts = nett_list
                break
            else:
                logger.debug((preamble + "No '%s' found") % nett_type)

        return the_netts

    def get_typed_interfaces_by_network_attr(self, vertex_type, attr_name):
        '''
        Public method to fetch the NetGraph Interfaces
        for networks tagged with a specific Attribute
        @param attr_name: Attribute name
        @type attr_name: String
        @return: List of Interfaces
        @rtype: List of Strings
        '''

        preamble = self.__class__.__name__ + \
                   '.get_typed_interfaces_by_network_attr: '

        ifaces = {}

        if attr_name in NetworkGraphConsts.SUPP_NET_ATTRS:
            net_vertices = self.get_vertices_by_type(vertex_type)
            for net_vertex in net_vertices:

                network = net_vertex['value']

                attrs = self.get_vertex_attrs(network)
                if attrs and (attr_name in attrs):
                    logger.debug((preamble + \
                                  "Successfully found '%s' attribute " + \
                                  "on Network '%s'") % \
                                  (attr_name, network))

                    ifs = self.get_interfaces_by_network_name(network)

                    logger.debug((preamble + \
                                  "Network: '%s' Interfaces: '%s'") % \
                                 (network, ifs))
                    if network in ifaces:
                        ifaces[network].append(ifs)
                    else:
                        ifaces[network] = ifs

            if len(ifaces) == 0:
                prop = NetworkGraphProps.PROP_GRAPH_NAME
                logger.debug((preamble + \
                              "Attribute '%s' not found on NetGraph '%s'") % \
                              (attr_name, self.properties[prop]))
        else:
            logger.debug((preamble + "Attribute '%s' not supported") % \
                         attr_name)

        return ifaces

    def gen_indent(self):
        '''
        Helper method to generate an indent (whitespace) string
        @return: Multiple whitespace string
        @rtype: String
        '''
        return ' ' * self.indent_count

    def gen_relationship_xml(self, vertex, tag, match_edge):
        '''
        Helper method to process the PyDot "arrow" or "->"
        relationships (parent|children)
        @param vertex: Dictionary of Vertex data
        @type vertex: Dictionary
        @param tag: XML tag for generated XMl data
        @type tag: String
        @param match_edge: Indicator of relation type src|dst
        @type match_edge: String
        @return: XML for src|dst relationship
        @rtype: String
        '''

        the_csl = None
        xml = ''

        dot_edges = self.the_dot_graph.get_edges()

        strip_char = NetworkGraphConsts.EXP_DOUBLE_QUOTE

        for dot_edge in dot_edges:
            src_edge = dot_edge.get_source().strip(strip_char)
            dst_edge = dot_edge.get_destination().strip(strip_char)

            if match_edge == 'src':
                the_edge = src_edge
                other_edge = dst_edge
            else:
                the_edge = dst_edge
                other_edge = src_edge

            (edge_type, edge_name) = the_edge.split()

            if edge_type == vertex['stype'] and \
               edge_name == vertex['name']:
                if the_csl:
                    the_csl += ','
                else:
                    the_csl = ''
                the_csl += other_edge.replace(' ', '_')

        if the_csl:
            self.indent_count += 2
            indent = self.gen_indent()
            xml = (indent + '<%s>' + the_csl + '</%s>\n') % (tag, tag)
            self.indent_count -= 2

        return xml

    def gen_kids_xml(self, vertex):
        '''
        Helper method to generate the data for the
        "children" XML tag
        @param vertex: Dictionary of Vertex data
        @type vertex: Dictionary
        @return: XML for "children" tag
        @rtype: String
        '''
        return self.gen_relationship_xml(vertex, 'children', 'src')

    def gen_parents_xml(self, vertex):
        '''
        Helper method to generate the data for the
        "parents" XML tag
        @param vertex: Dictionary of Vertex data
        @type vertex: Dictionary
        @return: XML for "parents" tag
        @rtype: String
        '''
        return self.gen_relationship_xml(vertex, 'parents', 'dst')

    def gen_attrs_xml(self, vertex, xml_attrs):
        '''
        Helper method to generate the data for the
        various Vertex attributes.
        @param vertex: Dictionary of Vertex data
        @type vertex: Dictionary
        @param xml_attrs: Dictionary of XML attributes
        @type xml_attrs: Dicntionary
        @return: None
        '''

        xml = ''
        if vertex['stype'] not in (NetworkGraphConsts.VERTX_STYPE_BOND,
                                   NetworkGraphConsts.VERTX_STYPE_NET):
            return xml

        attrs = self.get_vertex_attrs(vertex['value'])
        if attrs:

            self.indent_count += 2
            indent = self.gen_indent()

            for attr in attrs.keys():
                val = 'True'
                if attrs[attr]:
                    val = attrs[attr]

                xml_attrs[attr] = indent + ('<%s>%s</%s>\n' % \
                                  (attr, val, attr))

            self.indent_count -= 2

    def gen_xml(self, net_id, version, for_definition=True):
        '''
        Public helper method to generate XML for the Digraph
        @return: XML String
        @rtype: String
        '''

        preamble = self.__class__.__name__ + '.gen_xml: '

        if not self.the_digraph or \
           not self.the_dot_graph:
            response = self.process_net_graph_topology_data()
            if NetworkGraphConsts.FAILURE in response:
                logger.debug(preamble + repr(response))
                return None

        tags = {}

        def_appendage = ''
        if for_definition:
            def_appendage = '-def'

        ng_top_tag = 'net-graph-topology' + def_appendage

        xml = ('<litp:%s ' % (ng_top_tag)) + \
              'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" ' + \
              'xmlns:litp="http://www.ericsson.com/litp" ' + \
              'xsi:schemaLocation="http://www.ericsson.com/litp ' + \
              ('litp.xsd" id="%s" version="%s">\n' % (net_id, version))

        self.indent_count = 2

        strip_char = NetworkGraphConsts.EXP_DOUBLE_QUOTE
        graph_name = self.the_dot_graph.get_name().strip(strip_char)

        xml += "  <graph_name>%s</graph_name>\n" % graph_name

        indent = self.gen_indent()

        for dot_type in NetworkGraphConsts.SUPP_VERTX_STYPES:
            if dot_type == NetworkGraphConsts.VERTX_STYPE_BRDG:
                tag_type = 'brdg'
            else:
                tag_type = dot_type

            tags[dot_type] = "ng-%s%s" % (tag_type, def_appendage)

        for stype in NetworkGraphConsts.SUPP_VERTX_STYPES:
            for dot_name in self.dot_node_names:
                vertex = self.map_node_to_vertex(dot_name)
                if vertex['stype'] == stype:
                    tag = tags[vertex['stype']]

                    vertex_id = dot_name.replace(' ', '_')
                    xml += (indent + '<litp:%s id="%s">\n') % (tag, vertex_id)

                    xml_block = {}
                    xml_block['children'] = self.gen_kids_xml(vertex)
                    xml_block['parents'] = self.gen_parents_xml(vertex)
                    self.gen_attrs_xml(vertex, xml_block)
                    xml_block['require'] = indent + '  <require></require>\n'
                    #xml_block['primary'] = indent + '  <primary></primary>\n'

                    for key in sorted(xml_block.iterkeys()):
                        xml += xml_block[key]

                    xml += indent + ('</litp:%s>\n' % tag)

        xml += '</litp:%s>\n' % ng_top_tag
        logger.debug('mmhh11-- xml content: ' + xml)
        return xml

    def _get_last_state(self):
        """
        overridable method that returns the ultimate state for objects
        of this class

        @rtype:  string
        @return: status where objects from this class will be at ehe end
        of their lifecycle
        """
        return "Initial"

    @staticmethod
    def _get_nic_iface(index):
        """
        Return the interface name, e.g. eth4 from the index name.
        If the index name of the NIC is not numeric, then use it
        directly as: iface = '<name>', e.g. 'p4p1'
        @param index: Interface index name
        @type index: String
        @return: Interface name
        @rtype: String
        """
        from litp_netconf.linux_net_config import LinuxNetConf

        if index.isdigit():
            iface = LinuxNetConf.NIC_TAG + index
        else:
            iface = index
        return iface
