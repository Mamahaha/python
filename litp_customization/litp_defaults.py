"""
COA 252 352 / CXC 173 4106: LITP Common Properties definitions.
FUNCTIONALITY
    1. Defines an initial Python dictionary with default property definitions
       for each of the litp base properties used in litp/Landscape
       object definitions:
        - the dictionary is indexed by the property name;
        - the property name maps to another dictionary object:
        - indexed by the initial list of attribute names, where
          appropriate:
            - default
            - help
            - optional
            - regexp
            - type
        - the attribute names map to the initial default values of the
          attributes.
    2. Provides methods for creating properties of specific types.

USAGE
Provides a standard library for defining and accessing:
    - the initial list of attributes for a property;
    - a property definitions (such as regular expressions defining hostnames

      and MAC addresses).

Created on 27 Apr 2012

    @author: Declan Halpin
    @author: Pavel Smirnov
    @author: Marco Pietri

"""
from litp_common.validators.validator import *

"""
Default method parameters
"""
default_parameters = {
    'phase': {'help': 'Regex to filter only specified "phase" values',
              'type': 'str',
              'regexp': '^[\w\n]+$'},
    'id': {'help': 'Regex to filter only specified subtree identifiers',
           'type': 'str',
           'regexp': '^[\w\n]+$'},
    'type': {'help': 'Regex to filter only specified class names',
             'type': 'str',
             'regexp': '^[\w\n]+$'},
    'status': {'help': 'Regex to filter only specified "status" ' +
                       'property values',
               'type': 'str',
               'regexp': '^(Initial)|(Allocated)' +
                         '|(Available)|(Configured)|(Applying)|(Applied)' +
                         '|(Verified)|(Failed)$'},
    # Type for this is very tricky, e.g. propertyname=valid_regexp_string
    'properties': {'help': 'List of property=regex to filter based ' +
                           'on property names and values',
                   'type': 'dict(regexp)'}}
"""
Default litp properties
"""
litp_properties = dict()

"""
Default properties for litp item
"""
litp_properties['litp_item'] = ['name', 'require', 'type']
litp_properties['litp_resource'] = ['name', 'require', 'type', 'pool']

"""
Default for "name" property
"""
litp_properties['name'] = {
    'help': 'Item name, can be different from object identifier',
    'type': 'str',
    'regexp': '^[a-zA-Z0-9\-\._]*$',
    'optional': True}

"""
Default for properties which refer to item ids
"""
litp_properties['litp_id'] = {
    'help': 'Item id',
    'type': 'str',
    'regexp': '^[a-zA-Z0-9_]+$',
    'optional': True}

"""
Default for properties which refer to litp item paths
"""
litp_properties['litp_path'] = {
    'help': 'Path to Litp Item',
    'type': 'str',
    'regexp': '^[a-zA-Z0-9_/]+$',
    'optional': True}


"""
Default for "require" property
"""
litp_properties['require'] = {
     'help': 'Dependency reference to another ' +
             'item within the tree',
     'type': 'str',
     'regexp': '^[0-9a-zA-Z_ ,]*$',
     'optional': True,
     'default': ''}

"""
Default for "macaddress" property
"""
litp_properties['macaddress'] = {
    'help': 'MAC address for the local system',
    'type': 'str',
    'regexp': macaddr_regexp,
    'optional': False}

"""
Default for "hostname" property
"""
litp_properties['hostname'] = {
    'help': 'Host name for the local system',
    'type': 'str',
    'regexp': "^%s$" % hostname_regexp,
    'optional': False}

"""
Default for "domain" property
"""
litp_properties['domain'] = {
    'help': 'Domain name for the local system',
    'type': 'str',
    'regexp': "^(%s)?$" % hostname_regexp,
    'default': '',
    'optional': True}

"""
Default for "bridge_enabled" property
"""
litp_properties['bridge_enabled'] = {
    'help': 'If this property is set to true ' +
            'bridging is enabled on its network interfaces',
    'type': 'str',
    'optional': False,
    'default': 'False',
    'regexp': '^(True|False)$'}

"""
Default for "stack" property - IPAddress
"""
litp_properties['stack'] = {
    'help': 'This is the stack id. It can be 4 or 6',
    'type': 'str',
    'optional': False,
    'regexp': '^(4|6|both|none)$'}

"""
Default for "subnet" property - IPAddress
"""
litp_properties['subnet'] = {
    'help': 'This is the network address of\
                the represented IP address',
    'type': 'str',
    'optional': False,
    'regexp': '^[\d\.:/]+$'}

"""
Default for "netmask" property - IPAddress
"""
litp_properties['netmask'] = {
    'help': 'This is the network mask of\
                the represented IP address',
    'type': 'str',
    'optional': False,
    'regexp': "^%s$" % ipv4_regexp}

"""
Default for "gateway" property - IPAddress
"""
litp_properties['gateway'] = {
    'help': 'This is the IP address of the network \
                router or gateway device (if any) ',
    'type': 'str',
    'optional': True,
    'regexp': "^(%s|'')+$" % ipv4_regexp}

"""
Default for "address" property - IPAddress
"""
litp_properties['address'] = {
    'help': 'This is where the IP address is stored',
    'type': 'str',
    'optional': False,
    'regexp': ip_regexp}

"""
Default for "bootproto" property - IPAddress
"""
litp_properties['bootproto'] = {
    'help': 'This is the boot-time protocol to be used',
    'type': 'str',
    'optional': False,
    'regexp': '^[\w\n\.:]+$'}

"""
Default for "ipv6_autocon" property - IPAddress
"""
litp_properties['ipv6_autocon'] = {
    'help': 'This is a random identifier generated' +
                ' during first initialization',
    'type': 'str',
    'optional': False,
    'default': 'True',
    'regexp': '^(True|False)$'}

"""
Default for "vlan" property - IPAddress
"""
litp_properties['vlan'] = {
    'help': 'This is a random identifier generated during ' +
                'first initialization',
    'type': 'str',
    'optional': True,
    'default': '',
    'regexp': vlan_regexp}  # '^([\n\.:]|'')+$'

"""
Default for "broadcast" property - IPAddress
"""
litp_properties['broadcast'] = {
    'help': 'This is the broadcast address for this IP address',
    'type': 'str',
    'optional': False,
    'regexp': ip_regexp}

"""
Default for "cidr" property - IPAddress
"""
litp_properties['cidr'] = {
    'help': 'This is the subnet id represented in CIDR format',
    'type': 'str',
    'optional': False,
    'regexp': cidr_regexp}

"""
Default for "prefixlen" property - IPAddress
"""
litp_properties['prefixlen'] = {
    'help': 'This is the Prefix Length for an IP address',
    'type': 'str',
    'optional': True,
    'regexp': prefixlen}

"""
Default for "network" property - IPAddress
"""
litp_properties['network'] = {
    'help': 'This is the network address',
    'type': 'str',
    'optional': False,
    'regexp': ip_regexp}

"""
Default for "fsexport" property
"""
litp_properties['fsexport'] = {
    'help': 'The pass in which the mount is checked.',
    'type': 'str',
    'optional': False,
    'regexp': '^[\w\n]+$'}

"""
Default for "server" property associated with share
"""
litp_properties['server'] = {
    'help': 'Server associated with share',
    'type': 'str',
    'optional': False,
    'regexp': '^[\w\n]+$'}

"""
Default for "share" property
"""
litp_properties['share'] = {
    'help': 'The shared resource.',
    'type': 'str',
    'optional': False,
    'regexp': '^[\w\n]+$'}

"""
Default for "mountpoint" property
"""
litp_properties['mountpoint'] = {
    'help': 'The mountpoint directory.',
    'type': 'str',
    'optional': False,
    'regexp': '\/[\w\n]+(\/[\w\n]+)+'}

#"""
#Default for "share" property - NFS export
#"""
#litp_properties['share'] = {
#    'help': 'Share to be exported.',
#    'type': 'str',
#    'optional': False,
#    'regexp': '\/[\w\n]+(\/[\w\n]+)+'
#}

"""
Default for "options" property - NFS export
"""
litp_properties['options'] = {
    'help': 'Share options',
    'type': 'str',
    'optional': False,
    'default': '',
    'regexp': '^[\w\n]+$'}

"""
Default for "guest" property - NFS export
"""
litp_properties['guest'] = {
    'help': 'Guest for NFS export',
    'type': 'str',
    'optional': False,
    'default': '',
    'regexp': '^[\w\n]+$'}

"""
Default for "nodetype" property - CMW node type
"""
litp_properties['nodetype'] = {
    'help': 'Node type for CMW nodes',
    'type': 'str',
    'optional': True,
    'default': None,
    'regexp': '^(control|payload|management|sfs|nfs)$'}


"""
Default for "nodename" property - CMW node name
"""
litp_properties['nodename'] = {
    'help': 'Node name for CMW nodes',
    'type': 'str',
    'regexp': '^[\w\n]+$',
    'default': '',
    'optional': False}

"""
Default for "primary" property - indicates if CMW node is
the primary controller
"""
litp_properties['primarynode'] = {
    'help': 'Indicates if CMW node is the primary controller',
    'type': 'str',
    'optional': True,
    'default': 'false',
    'regexp': '^(true|false)$'}


"""
Default for "bundle_name" property for CMW campaign
"""
litp_properties['bundle_name'] = {
    'help': 'install bundle name',
    'type': 'str',
    'optional': False,
    'regexp': '^[\w\n-._]+$'}

"""
Default for "bundle_type" property for CMW campaign
"""
litp_properties['bundle_type'] = {
    'help': 'install bundle type',
    'type': 'str',
    'optional': True,
    'default': 'sdp',
    'regexp': '^[\w\n-._]+$'}

"""
Default for "install_name" property for CMW campaign
"""
litp_properties['install_name'] = {
    'help': 'install campaign name',
    'type': 'str',
    'optional': False,
    'default': '',
    'regexp': '^[\w\n-._]*$'}

"""
Default for "version" property for CMW campaign
"""
litp_properties['version'] = {
     'help': 'campaign version number',
     'type': 'str',
     'regexp': '^([A-Za-z_\./\d]+)$',
     'optional': True}

"""
Default for "vmhost" property - HostAssignment
"""
litp_properties['vmhost'] = {
    'help': 'vpath to a vmService / hypervisor',
    'type': 'str',
    'optional': False,
    'regexp': '^/[a-zA-Z0-9_-]+(/[a-zA-Z0-9_-]+)+$'}

"""
Default for "vmhost" property - GuestAssignment
"""
litp_properties['vmguest'] = {
    'help': 'vpath to the VM',
    'type': 'str',
    'optional': False,
    'regexp': '^/[a-zA-Z0-9_-]+(/[a-zA-Z0-9_-]+)+$'}

"""
Default for "mac_start" property for VM pool
"""
litp_properties['mac_start'] = {
    'help': 'Start MAC Address',
    'type': 'str',
    'optional': False,
    'regexp': macaddr_regexp}

"""
Default for "mac_end" property for VM pool
"""
litp_properties['mac_end'] = {
    'help': 'End MAC Address',
    'type': 'str',
    'optional': False,
    'regexp': macaddr_regexp}

"""
Default for "vmpath" property for VM pool
"""
litp_properties['vmpath'] = {
    'help': 'Path to the image used by VMs in this pool',
    'type': 'str',
    'optional': True,
    'regexp': '^/[a-zA-Z0-9_-]+(/[a-zA-Z0-9_-]+)+$'}

"""
Default for "bridge" property for VM system
"""
litp_properties['bridge'] = {
    'help': 'bridge',
    'type': 'str',
    'optional': False,
    'default': 'br0',
    'regexp': '^[\w\d]+$'}

"""
Default for "path" property for VM system
"""
litp_properties['path'] = {
    'help': 'path for virt image',
    'type': 'str',
    'optional': False,
    'default': '/var/lib/libvirt/images',
    'regexp': '^/[\w]+(/[\w]+)+$'}

"""
Default for "ram" property for VM system
"""
litp_properties['ram'] = {
    'help': 'ram',
    'type': 'str',
    'optional': False,
    'default': '1024',
    'regexp': '^[\w\d]+$'}

"""
Default for "disk" property for VM system
"""
litp_properties['disk'] = {
    'help': 'disk',
    'type': 'str',
    'optional': False,
    'default': '20',
    'regexp': '^[\w\d]+$'}

"""
Default for "cpus" property for VM system
"""
litp_properties['cpus'] = {
    'help': 'Number of CPUs to be given to VM',
    'type': 'str',
    'optional': True,
    'default': '1',
    'regexp': '^[\d]+$'}

"""
Default for "vmware" property for VM system
"""
litp_properties['vmware'] = {
    'help': 'True if the system is a VMware and ' +
                'not real hardware',
    'type': 'str',
    'optional': False,
    'default': 'True',
    'regexp': '^[True|False]+$'}

"""
Default for "posix_name" POSIX property
"""
litp_properties['posix_name'] = {
    'help': 'POSIX User Account Name',
    'type': 'str',
    'optional': False,
    'regexp': '^[A-Za-z0-9_][A-Za-z0-9_-]{0,30}$',
}

"""
Default for "posix_comment" POSIX property
"""
litp_properties['posix_comment'] = {
    'help': 'POSIX User Account Description (e.g. full name)',
    'type': 'str',
    'optional': True,
    'regexp': '.'}

"""
Default for "posix_home" POSIX property
"""
litp_properties['posix_home'] = {
    'help': 'POSIX User Account Home directory',
    'type': 'str',
    'optional': True,
    'regexp': '^/[\S \n]*$'}

"""
Default for "posix_uid" POSIX property
"""
litp_properties['posix_uid'] = {
    'help': 'POSIX User Account Id',
            'type': 'str',
            'optional': True,
            'regexp': '^[1-9][0-9]*$'}

"""
Default for "posix_gid" POSIX property
"""
litp_properties['posix_gid'] = {
    'help': 'Primary Group Id',
    'type': 'str',
    'optional': True,
    'regexp': '^([A-Za-z0-9_][A-Za-z0-9_-]{0,30}' + \
              '([A-Za-z0-9_-]?|(\\\\\\$)?)|[0-9][0-9]*)$'}

"""
Default for "posix_umask" POSIX property
"""
litp_properties['posix_umask'] = {
    'help': 'Users default umask',
    'type': 'str',
    'optional': True,
    'regexp': '^0[027]{3}|[027]{1,3}$'}

"""
Default for "posix_groups" POSIX property
"""
litp_properties['posix_groups'] = {
    'help': 'POSIX User Account Group memberships (comma separated)',
    'type': 'str',
    'optional': True,
    'regexp': '^([A-Za-z0-9_][A-Za-z0-9_-]{0,30}' + \
                      '([A-Za-z0-9_-]?|(\\\\\\$)?))' + \
             '(,([A-Za-z0-9_][A-Za-z0-9_-]{0,30}' + \
             '([A-Za-z0-9_-]?|(\\\\\\$)?)))*$'}

"""
Default for "posix_seluser" POSIX property
"""

litp_properties['posix_seluser'] = {'help': 'SELinux user type',
            'type': 'str', 'optional': True,
            'regexp': '^[a-zA-Z_]*$'}

litp_properties['posix_seluser']['help'] = 'SELinux user type'

"""
Default for "posix_password" POSIX property
"""
litp_properties['posix_password'] = {
    'help': 'Users password',
    'type': 'str',
    'optional': False,
    'regexp': '^.*$'}


"""
Default properties for File Resource
"""
litp_properties['file_path_str'] = {
    'help': 'Fully specified file / directory / link name',
    'type': 'str', 'optional': True, 'default': '/dev/null',
    'regexp': '^[A-Za-z0-9/_\-\s\.]+$'}

litp_properties['file_paths_comma_separated'] = {
    'help': 'Comma separated list of file paths',
    'type': 'str', 'optional': True,
    'regexp': '^[A-Za-z0-9/_\-\s\.,]+$'}

litp_properties['file_ensure'] = {
    'help': 'Enforcement action on this resource',
    'type': 'str', 'optional': True,
    'regexp': '^(absent)|(present)|(file)|(directory)|(link)$'}

litp_properties['file_mode'] = {
    'help': 'File mode mask in Unix standard notation, e.g. 0755',
    'type': 'str', 'optional': True,
    'regexp': '^[0-7]?[0-7][0-7][0-7]$'}

"""
File properties
"""
litp_properties['file_path_string'] = {
    'help': 'Nix style file path',
    'type': 'str', 'optional': True,
    'regexp': '^[A-Za-z0-9/_#\-\s\.]+$'}

litp_properties['file_mode_string'] = {
    'help': 'Nix style file mode',
    'type': 'str', 'optional': True,
    'regexp': '[0-7]?[0-7][0-7][0-7]'}

litp_properties['file_system_size'] = {
    'help': 'Nix style file size',
    'type': 'str', 'optional': True,
    'regexp': '^[0-9]+[M|G|T]$'}

"""
User properties
"""
litp_properties['account_name_string'] = {
    'help': 'Nix style account name',
    'type': 'str', 'optional': True,
    'regexp': '^[a-zA-Z0-9_][a-zA-Z0-9_-]{0,30}[A-Za-z9-9_$-]?$'}

"""
Network properties
"""
litp_properties['ipv4_ipaddress_string'] = {
    'help': 'IPV4 IP Address',
    'type': 'str', 'optional': True,
    'regexp': "^%s$" % ipv4_regexp}

litp_properties['ip_ipaddress_string'] = {
    'help': 'IP v4 or v6 Address',
    'type': 'str', 'optional': True,
    'regexp': "^%s$" % ip_regexp}

litp_properties['nic_device_name'] = {
    'help': 'Name of NIC device',
    'type': 'str', 'optional': True,
    'regexp': '^[a-zA-Z][a-zA-Z0-9_\-\.]+$'}

litp_properties['valid_port'] = {
    'help': 'Port number inside valid range',
    'type': 'str', 'optional': True,
    'regexp': '^(6553[0-5]|655[0-2][0-9]|65[0-4][0-9]{2}|6[0-4][0-9]{3}|' +
    '[1-5][0-9]{4}|[1-9][0-9]{0,3}|0)$'
  }


"""
Generic properties
"""
litp_properties['basic_string'] = {
    'help': 'Character value',
    'type': 'str', 'optional': True,
    'regexp': '^.*$', 'default': None}

litp_properties['basic_string_no_default'] = {
    'help': 'Character value',
    'type': 'str', 'optional': True,
    'regexp': '^.*$'}

litp_properties['basic_integer'] = {
    'help': 'Integer value',
    'type': 'str', 'optional': True,
    'regexp': '^[0-9]+$'}


litp_properties['basic_name_string'] = {
    'help': 'Named value (alphanumeric, underscores and dots)',
    'type': 'str', 'optional': True,
    'regexp': '^[a-zA-Z0-9\-_\.]+$'}

litp_properties['password_string'] = {
    'help': 'password string',
    'type': 'str', 'optional': True,
    'regexp': '^.*$'}

litp_properties['basic_boolean'] = {
    'help': 'Boolean value (true or false)',
    'type': 'str', 'optional': True, 'default': 'false',
    'regexp': '^(true|false)$'}

litp_properties['basic_python_bool'] = {
    'help': 'Boolean value (True or False)',
    'type': 'str', 'optional': True, 'default': 'false',
    'regexp': '^(True|False)$'}

litp_properties['boolean_string'] = {
    'help': 'Boolean value (0 or 1)',
    'type': 'str', 'optional': True, 'default': '0',
    'regexp': '^(0|1)$'}

litp_properties['basic_yesno_string'] = {
    'help': 'Boolean value (yes or no)',
    'type': 'str', 'optional': True, 'default': 'no',
    'regexp': '^(yes|no)$'}

litp_properties['basic_enum'] = {
    'type': 'str', 'optional': True,
}

litp_properties['add_to_cobbler'] = {
     'help': 'String (True or False) that states whether the node is added to '
     'cobbler profiles or not ',
    'type': 'str', 'optional': 'False', 'default': 'True',
    'regexp': '^(True|False)$'}

litp_properties['version_string'] = {
    'help': 'Version of this item (Miajor.Minor.Micro.Patch-BuildText)',
    'type': 'str', 'optional': 'True',
    'regexp': '^[0-9]+(\.[0-9]+(\.[0-9]+(\.[a-zA-Z0-9_\-]+)?)?)?$',
}

litp_properties['restricted_version_string'] = {
    'help': 'Version of this item (Miajor.Minor.Micro.Patch-BuildText)',
    'type': 'str', 'optional': 'True',
    'regexp': '^([0-9]+)(\.[0-9]+){2}(\.[a-zA-Z0-9\-]+\-[a-zA-Z0-9\-]+)?$',
}

litp_properties['method'] = {
    'help': 'method to be executed',
    'type': 'str', 'optional': 'False',
    'regexp': '^[a-zA-Z0-9_\-]+$',
}

litp_properties['uri'] = {
    'help': 'path of the object whose method is executed',
    'type': 'str', 'optional': 'False',
    'regexp': '^[a-zA-Z0-9/\-_.]+$',
}

litp_properties['params'] = {
    'help': 'params to be passed to the method',
    'type': 'str', 'optional': 'True',
    'default': str(tuple()),
    'regexp': '^[a-zA-Z0-9_\-]+$',
}

litp_properties['kwargs'] = {
    'help': 'kwargs to be passed to the method',
    'type': 'str', 'optional': 'True',
    'default': '{}',
    'regexp': '^[a-zA-Z0-9_\-]+$',
}

litp_properties['retry_timeout'] = {
    'help': 'amount of time(seconds) between failed attempt and the ' \
        'next attempt',
    'type': 'str', 'optional': 'False', 'default': '30',
    'regexp': '^[0-9]+$',
}

litp_properties['retry_timeout_no_default'] = {
    'help': 'amount of time(seconds) between failed attempt and the ' \
        'next attempt',
    'type': 'str', 'optional': 'False',
    'regexp': '^[0-9]+$',
}

litp_properties['retries'] = {
    'help': 'number of retries to be attempted',
    'type': 'str', 'optional': 'False', 'default': '0',
    'regexp': '^[0-9]+$',
}

litp_properties['estimated_duration'] = {
    'help': 'estimated time of task duration(seconds)',
    'type': 'str', 'optional': 'False', 'default': '60',
    'regexp': '^[0-9]+$',
}

litp_properties['jdbc_url'] = {
    'help': 'JDBC URL string',
    'type': 'str',
#    'regexp': '^(jdbc)(:[a-zA-Z]*)?:\/\/(a-zA-Z0-9_\.)+(:[0-9]*)?\/(.*)$',
    'regexp': '^.*$',
}

litp_properties['anything'] = {
    'type': 'str',
    'regexp': '^.*$',
    'optional': True,
}

litp_properties["uid"] = {"help": "Unique ID of the LUN", "type": "str",
                          "optional": False,
                          "regexp": "^([a-fA-F0-9]{2}:){15}[a-fA-F0-9]{2}$"}

litp_properties['HA_manager'] = {
    'help': 'Cluster HA manager',
    'type': 'str',
    'optional': True,
    'default': None,
    'regexp': '^(CMW|VCS|None)$'}

litp_properties['primary'] = {
    'help': 'Primary Slave',
    'type': 'str',
    'regexp': '[a-zA-Z0-9\-\._]*',
     'default': None,
    'optional': True,
}

def create_str_property(property_type, overrides=None):
    """
    FUNTIONALITY
    Returns a new dictionary, comprising:
        1. the default litp_properties dictionary, for the property specified
         by "property_type".
        2. a new attribute "_type" with initial value set to "property_type".
        3. the dict values, if any, specified in the overrides parameter.

    @type property_type: an litp Property name
    @param property_type: the name of the property to be added to the
    dictionary.
    @type overrides:  dict
    @param overrides: an additional dictionary of attributes, if any, to add
    to the final properties dict.
    @rtype: dict
    @return: an litp properties dict entry.
    """
    overrides = overrides or dict()
    properties = litp_properties[property_type].copy()
    properties['_type'] = property_type
    if property_type == 'password_string':
        properties['type'] = 'secure'
    properties.update(overrides)
    return properties


def create_enum_property(choices, overrides=None):
    """
    FUNTIONALITY
    Returns an updated litp_properties "basic_enum" dictionary entry, setting
    the regexp attribute according to the parameter "choices".


    @type choices: List of characters
    @param choices: characters to be included in "regexp" attribute values.
    @type overrides:  dict
    @param overrides: an additional dictionary of attributes, if any, to add
    to the final properties dict.
    @rtype: dict
    @return: an litp properties dict entry.
    """
    choices = choices or []
    overrides = overrides or dict()
    properties = litp_properties['basic_enum'].copy()
    properties.update(overrides)
    properties['regexp'] = '^(' + \
        "|".join(["(%s)" % (c,) for c in choices]) + ')$'
    return properties


def create_list_property(property_type, overrides=None):
    """
    FUNTIONALITY
    Returns a new list, comprising:
        1. the default litp_properties dictionary, for the property specified
         by "property_type".
        2. a new attribute "_type" with initial value set to "property_type".
        3. the list values, if any, specified in the overrides parameter.

    @type property_type: an litp Property name
    @param property_type: the name of the property to be added to the
    list.
    @type overrides:  list
    @param overrides: an additional list of attributes, if any, to add
    to the final properties list.
    @rtype: list
    @return: an litp properties list entry.
    """
    overrides = overrides or list()
    properties = list(litp_properties[property_type])
    properties.extend(overrides)
    return properties
