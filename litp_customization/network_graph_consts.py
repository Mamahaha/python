#!/usr/bin/env python

'''
@copyright: Ericsson AB
@since:     September 2012
@author:    Ray Brady
@summary:   Some useful Network Graph Topology constants
'''


class NetworkGraphConsts(object):
    '''
    Network Graph Topology class providing constants
    '''

    logger_id = 'litp.network'
    '''
    @cvar: Logger Identity
    @type: String
    '''

    package = 'litp_graphs'
    '''
    @cvar: Static string for Package name
    @type: String
    '''

    core_package = 'core'
    '''
    @cvar: Static String for Litpcommon 'core' package
    @type: String
    '''

    core_prefix = core_package + '.litp_'
    '''
    @cvar: Static String for Litpcommon core module prefix
    @type: String
    '''

    KLASS_INV = core_prefix + 'inventory.LitpInventory'
    '''
    @cvar: Static String for Inventory item
    @type: String
    '''

    KLASS_SITE = core_prefix + 'site.LitpSite'
    '''
    @cvar: Static String for Site item
    @type: String
    '''

    KLASS_NETG_TOP = package + '.network_graph_topology.NetworkTopology'
    '''
    @cvar: Static String for Network Graph Topology class name
    @type: String
    '''

    KLASS_NG_ITEMS = 'litp_ng_items.ng_base.NGBase'
    '''
    @cvar: Network-Graph Items type
    @type: String
    '''

    SUPP_GRAPH_TYPE = 'digraph'
    '''
    @cvar: Supported Graph type: digraph
    @type: String
    '''

    VERTX_STYPE_NET = 'net'
    '''
    @cvar: Supported Vertex type 'net': Network
    @type: String
    '''

    VERTX_STYPE_VLAN = 'vlan'
    '''
    @cvar: Supported Vertex type 'vlan': Virtual Local Area Network
    @type: String
    '''

    VERTX_STYPE_BRDG = 'bridge'
    '''
    @cvar: Supported Vertex type 'bridge': Bridge
    @type: String
    '''

    VERTX_STYPE_BOND = 'bond'
    '''
    @cvar: Supported Vertex type 'bond': Bond
    @type: String
    '''

    VERTX_STYPE_NIC = 'nic'
    '''
    @cvar: Supported Vertex type 'nic': network-Interface-Card
    @type: String
    '''

    # Alphabetic order - important for XSD
    SUPP_VERTX_STYPES = [VERTX_STYPE_BOND,
                         VERTX_STYPE_BRDG,
                         VERTX_STYPE_NET,
                         VERTX_STYPE_NIC,
                         VERTX_STYPE_VLAN]
    '''
    @cvar: Set of 5 supported Network element types
    @type: List of Strings
    '''

    VERTX_ITYPE_NET = 0
    '''
    @cvar: Supported Vertex type 'net': Network
    @type: Integer
    '''

    VERTX_ITYPE_VLAN = 1
    '''
    @cvar: Supported Vertex type 'vlan': Virtual Local Area Network
    @type: Integer
    '''

    VERTX_ITYPE_BRDG = 2
    '''
    @cvar: Supported Vertex type 'bridge': Bridge
    @type: Integer
    '''

    VERTX_ITYPE_BOND = 3
    '''
    @cvar: Supported Vertex type 'bond': Bond
    @type: Integer
    '''

    VERTX_ITYPE_NIC = 4
    '''
    @cvar: Supported Vertex type 'nic': network-Interface-Card
    @type: Integer
    '''

    SUPP_VERTX_ITYPES = [VERTX_ITYPE_NET, VERTX_ITYPE_VLAN, VERTX_ITYPE_BRDG,
                         VERTX_ITYPE_BOND, VERTX_ITYPE_NIC]
    '''
    @cvar: Set of 5 supported Network element types
    @type: List of Integers
    '''

    SUPP_VERTX_TYPES_MAP = {VERTX_ITYPE_NET: VERTX_STYPE_NET,   # Int-to-String
                            VERTX_ITYPE_VLAN: VERTX_STYPE_VLAN,
                            VERTX_ITYPE_BRDG: VERTX_STYPE_BRDG,
                            VERTX_ITYPE_BOND: VERTX_STYPE_BOND,
                            VERTX_ITYPE_NIC: VERTX_STYPE_NIC,
                            VERTX_STYPE_NET: VERTX_ITYPE_NET,   # String-to-Int
                            VERTX_STYPE_VLAN: VERTX_ITYPE_VLAN,
                            VERTX_STYPE_BRDG: VERTX_ITYPE_BRDG,
                            VERTX_STYPE_BOND: VERTX_ITYPE_BOND,
                            VERTX_STYPE_NIC: VERTX_ITYPE_NIC}
    '''
    @cvar: Map the 5 Integer Constant References to the String equivalent and
           Map the 5 String Constant References to the Integer equivalent
    @type: Dictionary
    '''

    GRAPH_ANCHOR_HEAD = 'start'
    '''
    @cvar: Indicator of Graph position to seach from
    @type: String
    '''

    GRAPH_ANCHOR_HIND = 'end'
    '''
    @cvar: Indicator of Graph position to search to
    @type: String
    '''

    SUCCESS = 'success'
    '''
    @cvar: The string indicating success / positive outcome
    @type: String
    '''

    FAILURE = 'error'
    '''
    @cvar: The string indicating failure / negative outcome
    @type: String
    '''

    SKIPPED = 'skipped'
    '''
    @cvar: The string indicating action Skipped
    @type: String
    '''

    CARET_CHR = '^'
    '''
    @cvar: The caret ^ character
    @type: String
    '''

    DOLLAR_CHR = '$'
    '''
    @cvar: The dollar $ character
    @type: String
    '''

    PIPE_CHR = '|'
    '''
    @cvar: The pipe | character
    @type: String
    '''

    OPEN_RND_BKT_CHR = '('
    '''
    @cvar: The open-round-bracket ( character
    @type: String
    '''

    CLOS_RND_BKT_CHR = ')'
    '''
    @cvar: The close-round-bracket ) character
    @type: String
    '''

    OPEN_SQR_BKT_CHR = '['
    '''
    @cvar: The open-square-bracket [ character
    @type: String
    '''

    CLOS_SQR_BKT_CHR = ']'
    '''
    @cvar: The close-square-bracket ] character
    @type: String
    '''

    ASTERISK_CHR = '*'
    '''
    @cvar: The asterisk / star character
    @type: String
    '''

    PLUS_CHR = '+'
    '''
    @cvar: The plus character
    @type: String
    '''

    OPEN_PARENTHESIS = '{'
    '''
    @cvar: the open-curly bracket character
    @type: String
    '''

    CLOSE_PARENTHESIS = '}'
    '''
    @cvar: the close-curly bracket character
    @type: String
    '''

    SEMI_COLON_CHR = ';'
    '''
    @cvar: The semi-colon character
    @type: String
    '''

    EXP_DOT_BLOCK_START = '\\' + OPEN_PARENTHESIS
    '''
    @cvar: The DOT Block start character
    @type: String
    '''

    EXP_DOT_BLOCK_END = '\\' + CLOSE_PARENTHESIS
    '''
    @cvar: The DOT Block end character
    @type: String
    '''

    EXP_ZERO_OR_MORE_MLTPLR = ASTERISK_CHR
    '''
    @cvar: The zero-or-more multiplier: asterisk character
    @type: String
    '''

    EXP_ONE_OR_MORE_MLTPLR = PLUS_CHR
    '''
    @cvar: The one-or-more multiplier: plus character
    @type: String
    '''

    EXP_LINE_START_ANCHR = CARET_CHR
    '''
    @cvar: The start-of-line anchor: caret character
    @type: String
    '''

    EXP_LINE_END_ANCHR = DOLLAR_CHR
    '''
    @cvar: The end-of-line anchor: caret character
    @type: String
    '''

    EXP_RANGE_START = OPEN_SQR_BKT_CHR
    '''
    @cvar: The start-of-range : open-square-bracket character
    @type: String
    '''

    EXP_RANGE_END = CLOS_SQR_BKT_CHR
    '''
    @cvar: The end-of-range : close-square-bracket character
    @type: String
    '''

    EXP_LOGICAL_OR = PIPE_CHR
    '''
    @cvar: The logical OR operator: pipe character
    @type: String
    '''

    EXP_GROUP_OPEN = OPEN_RND_BKT_CHR
    '''
    @cvar: The Group Start marker: Open-round-bracket character
    @type: String
    '''

    EXP_GROUP_CLOSE = CLOS_RND_BKT_CHR
    '''
    @cvar: The Group End marker: Close-round-bracket character
    @type: String
    '''

    EXP_DOT_STMNT_END = SEMI_COLON_CHR
    '''
    @cvar: The semicolon end of statement character
    @type: String
    '''

    one_or_more_any_chars_pattern = '.' + EXP_ONE_OR_MORE_MLTPLR
    '''
    @cvar: One or More any (multiple) characters pattern
    @type: String
    '''

    COMMA_CHR = ','
    '''
    @cvar: The comma character
    @type: String
    '''

    EXP_CSV_SEP = COMMA_CHR
    '''
    @cvar: The comma-separated-value separator
    @type: String
    '''

    # ---

    ALPHA = 'a-zA-Z'
    '''
    @cvar: Alphabetic characters
    @type: String
    '''

    ALPHA_NUMERIC = ALPHA + '0-9'
    '''
    @cvar: Alpha-numeric characters
    @type: String
    '''

    ALPHA_NUMERIC_NO_HYPHEN_STR = ALPHA_NUMERIC + '_'
    '''
    @cvar: Alpha-numeric plus underscore characters
    @type: String
    '''

    ALPHA_NUMERIC_STR = ALPHA_NUMERIC_NO_HYPHEN_STR + '-'
    '''
    @cvar: Alpha-numeric plus underscore plus hyphen characters
    @type: String
    '''

    EXP_DOT_EDGE_ARROW = '->'
    '''
    @cvar: DOT language edge syntax
    @type: String
    '''

    EXP_DOUBLE_QUOTE = '"'
    '''
    @cvar: The double-quote character
    @type: String
    '''

    EXP_ASSIGNMENT = '='
    '''
    @cvar: The assignment or equals character
    @type: String
    '''

    EXP_INVERSE_MATCH = CARET_CHR
    '''
    @cvar: Character range inverse match character
    @type: String
    '''

    EXP_ATTRS_START = '\['
    '''
    @cvar: DOT language attributes start character
    @type: String
    '''

    EXP_ATTRS_END = '\]'
    '''
    @cvar: DOT language attributes end character
    @type: String
    '''

    MANDATORY_WHITE_SPACE = ' ' + EXP_ONE_OR_MORE_MLTPLR
    '''
    @cvar: At least one white-space character
    @type: String
    '''

    OPTIONAL_WHITE_SPACE = ' ' + EXP_ZERO_OR_MORE_MLTPLR
    '''
    @cvar: Zero or more white-space characters
    @type: String
    '''

    OPTIONAL_ANY_WHITE_SPACE = '\s' + EXP_ZERO_OR_MORE_MLTPLR
    '''
    @cvar: Zero or more space characters of any kind (tab/newline/space etc)
    @type: String
    '''

    EXP_ALPHA_RANGE = EXP_RANGE_START + ALPHA + EXP_RANGE_END
    '''
    @cvar: The alphabetic character range
    @type: String
    '''

    EXP_ALNUM_RANGE = EXP_RANGE_START + ALPHA_NUMERIC + EXP_RANGE_END
    '''
    @cvar: The alpha-numeric character range
    @type: String
    '''

    EXP_OPTIONAL_ALNUM_STR_RANGE = EXP_RANGE_START + \
                                   ALPHA_NUMERIC_STR + \
                                   EXP_RANGE_END + \
                                   EXP_ZERO_OR_MORE_MLTPLR
    '''
    @cvar: The alpha-numeric plus underscore plus hyphen character range
           - zero or more characters thereof
    @type: String
    '''

    EXP_OPTIONAL_ALNUM_NO_HYPHEN_STR_RANGE = EXP_RANGE_START + \
                                             ALPHA_NUMERIC_NO_HYPHEN_STR + \
                                             EXP_RANGE_END + \
                                             EXP_ZERO_OR_MORE_MLTPLR
    '''
    @cvar: The alpha-numeric plus underscore character range
           - zero or more characters thereof
    @type: String
    '''

    SUPP_NET_ATTR_TIPC = 'tipc'
    '''
    @cvar: The Network TIPC attribute
    @type: String
    '''

    SUPP_NET_ATTR_TIPC_INTERNAL = 'tipc_internal'
    '''
    @cvar: The Network TIPC internal attribute
    @type: String
    '''

    SUPP_NET_ATTR_VCS_LLT = 'vcs_llt'
    '''
    @cvar: The Network VCS Low-Latency-Link attribute
    @type: String
    '''

    SUPP_NET_ATTR_VCS_LPR = 'vcs_lpr'
    '''
    @cvar: The Network VCS Low-Priority-Link attribute
    @type: String
    '''

    SUPP_NET_ATTR_IP_OPTIONAL = 'ip_optional'
    '''
    @cvar: The Network IP Optional attribute
    @type: String
    '''

    SUPP_NET_ATTR_BOOT = 'boot'
    '''
    @cvar: The Network Boot attribute
    @type: String
    '''

    SUPP_NET_ATTR_BOOTPROTO = 'bootproto'
    '''
    @cvar: The Network BootProto attribute
    @type: String
    '''

    SUPP_NET_ATTRS_NO_VALS = [SUPP_NET_ATTR_BOOT,
                              SUPP_NET_ATTR_IP_OPTIONAL,
                              SUPP_NET_ATTR_TIPC,
                              SUPP_NET_ATTR_TIPC_INTERNAL,
                              SUPP_NET_ATTR_VCS_LLT,
                              SUPP_NET_ATTR_VCS_LPR]
    '''
    @cvar: Set of Network Vertex attributes
           without associated values
    @type: List of Strings
    '''

    # Alphabetic order - important for XSD
    SUPP_NET_ATTRS = [SUPP_NET_ATTR_BOOT,
                      SUPP_NET_ATTR_BOOTPROTO,
                      SUPP_NET_ATTR_IP_OPTIONAL,
                      SUPP_NET_ATTR_TIPC,
                      SUPP_NET_ATTR_TIPC_INTERNAL,
                      SUPP_NET_ATTR_VCS_LLT,
                      SUPP_NET_ATTR_VCS_LPR]
    '''
    @cvar: Set of 6 supported Network Vertex attributes
    @type: List of Strings
    '''

    SUPP_BOOTPROTOS = ['dhcp', 'static']
    '''
    @cvar: 'Supported Boot Proto attribute values
    @type: List
    '''

    SUPP_BOND_MODES = {'balance-rr': '0',
                       'active-backup': '1',
                       'balance-xor': '2',
                       'broadcast': '3',
                       '802.3ad': '4',
                       'balance-tlb': '5',
                       'balance-alb': '6'}
    '''
    @cvar: Supported Bond Mode attribute values
    @type: Dictionary
    '''

    SUPP_BOND_ATTR_MODE = 'mode'
    '''
    @cvar: The Bond Mode attribute
    @type: String
    '''

    SUPP_BOND_ATTR_PRIMARY = 'primary'
    '''
    @cvar: The Bond Primary attribute
    @type: String
    '''

    SUPP_BOND_ATTRS = [SUPP_BOND_ATTR_MODE, SUPP_BOND_ATTR_PRIMARY]
    '''
    @cvar: Supported Bond attribute names
    @type: List of Strings
    '''
