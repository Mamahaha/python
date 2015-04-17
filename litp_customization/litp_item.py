"""
COA 252 352 / CXC 173 4106: LITP Tree Item Class supporting REST Framework.

Provides the Landscape resource LitpItem base class:
    - provides access to the CherryPy REST framework;
    - is inherited by all resource classes that appear on the Landscape tree as
      resource types, such as:
        - Constraints
        - Clusters
        - Pools
        - Resources
        - Roles
        - Services
        - Sites
        - etc

    @author: Pavel Smirnov
    @author: Marco Pietri
    @author: Chris Saint-Amand

Allowed children:
    - core.litp_item.LitpItem
"""
from core.litp_threadpool import background
from litp_defaults import create_str_property, default_parameters
from litp_rest_resource import LitpRestResource
from litp_serialize import serialized
from litp_versions import PkgInfo
from time import strftime, gmtime
from topsort import topsort2
from serializer.landscape_serializer import LandscapeSerializer
from core.litp_custom_exceptions import (NotUpgradablePropertyException,
                                         NotUpgradableObjectException,
                                        ConditionalUpgradablePropertyException)
from encryption.encryption import EncryptionRSA, EncryptionAES
import urllib2

import copy
import crypt
import datetime
import itertools
import jsonpickle
import os
import re
import sre_constants
import ast

import logging
"@var logger: Provides mechanism for writing to syslog."
logger = logging.getLogger('litp.LitpItem')


class LitpItem(LitpRestResource):
    """
        Class representing a LITP Landscape Resource item.

        This class is inherited by all LITP Landscape Resource types.

        For example all of the following should inherit to this class:
        Sites, Clusters, Nodes, Roles, Resources, Constraints,
        Services, Pools

        Classes implementing human interfaces can inherit as well:
        CobblerBootManager, PuppetConfigManager, LDAPUserManager,
        PKIManager, DNSManager, DHCPManager, etc...

        Class instance variables include:
        properties: A Dictionary of the object's properties.
        This Dictionary is directly available to REST interface for
        modifications, subject to normal REST authorization controls.

        status:
        Current _configured_ "State" of this Landscape tree object's
        instance. This can be set to
            1. Initial        Set during object initialization
            2. Allocated      Set by the Allocate method (only if new
                                allocation succeeded)
            3. Configured     Set by the Configure method (only if
                                configuration changed)
            4. Applying       Set by the ConfigManager only (as requested from
                                CLI) e.g. Applying to Puppet node definition
            5. Acknowleged    Set by the Feedback method only (can be called
                                externally)
            6. Verified       Set by the Validate method only (can be called
                                externally)
            7. Failed         Set by the Validate,Configure,Apply methods

        phase: This object's orchestration phase (normally derived from
        Definition). Phase can be used to filter out items in either
        Tree, Allocate or Configure recursions.

        configuration: Dictionary of items comprising "Configuration" of
        this object's instance. This dictionary will be parsed by
        ConfigManager class methods in order to get transformed
        into Puppet definitions

    """

    def __init__(self):
        """
        Constructor allows to populate certain internal data structures
        duringthe init time. For example, supported properties and
        methods (for presentation to CLI).
        """
        super(LitpItem, self).__init__()

        self.created = datetime.datetime.now().isoformat(' ')  # Time Created
        """
        @ivar: Object creation time.
        @type: ISO format Time string.
        """

        # Id (MUST BE Python naming compliant) [\a|\d|_]
        self.id = None
        """
        @ivar: the object's <URIname> in the <URIpath>/<URIname>.
        @type: URI String component
        """

        self.path = None           # Parent path in LITP Tree
        """
        @ivar: the object's <URIpath> in the <URIpath>/<URIname> id.
        @type: A URI path
        """

        self.status = "Initial"
        """
        @ivar: Object status:
            - Initial,    value set at object creation.
            - Allocated,  resource allocated from a resource pool.
            - Configured, resource is configured for pushing to Puppet.
            - Applying,    Puppet files created and available for actioning by
                          Puppet.
            - Applied,
                          Configuration files actioned by Puppet.
            - Verified,   manual verification of Puppet configuration
                          successful.
            - Failed,     manual verification of Puppet configuration failed.
        @type: String, with an enumerated set number of values.
        """

        self.status_history = []   # Status history
        """
        @ivar: Records the object status change history.
        @type: dict
        """

        self.phase = "default"     # Phase for orchestration
        """
        @ivar: Provides sequencing of configuration enforcement.
               Not currently used.
        @type: sequence
        """

        self.pool = None           # Pool name if needs pool allocation
        """
        @ivar: Name of the pool from which to obtain pool resources.
        @type: String
        """

        self.service = None        # Service name if needs mapping to service
        """
        @ivar: Name of the pool from which to obtain service resources.
        @type: String
        """

        self.properties = {}       # Properties dictionary
        """
        @ivar: The object's property/value mappings.
        @type: dict
        """

        self.deletable = True  # Is this a deletable item
        """
        @ivar: Whether the object can be deleted.
        @type: Boolean
        """

        self.upgradable = False
        """
        @ivar: Whether the object can be upgraded.
        @type: Boolean
        """

        self.origin = None         # URL of the original entry when allocated
        """
        @ivar: Id of the resource or service pool used to provision object.
        @type: URI String
        """

        self.configuration = []    # Last Configuration detail
        """
        @ivar: Configuration data set by the litp configure command.
        @type: list
        """

        self.configresult = {}     # Last Configuration result code
        """
        @ivar: Result of 'litp configure' command on object.
        @type: dict
        """

        self.default_net_name = None     # Default Network to use
        """
        @ivar: Default network to use if components don't specify
                       a Networ. Used for system wide defaults.
        @type: String
        """

        ########################################
        ## Following items are due for deprecation
        ########################################

        self.allocated = None      # When Allocated (if applicable)
        "@ivar: Deprecated."

        self.applied = None
        "@ivar: Deprecated."

        self.acknowledgement = {}  # Last acknowledgement detail
        "@ivar: Deprecated."

        self.applying = None      # When Last applying Configuration to System
        "@ivar: Deprecated."

        self.verified = None       # When Last Verification Run
        "@ivar: Deprecated."

        self.failed = None         # When Last Failed status has been recorded
        "@ivar: Deprecated."

        self.failure = {}          # Failure details
        "@ivar: Deprecated."

        self.set_prop_defaults()

        self.children = {}

        self.plugin_version = ""

    @staticmethod
    def decryptAES(data):
        """Read LITP key and use it to decrypt data"""
        result = EncryptionAES.readkey("/root/litp_key")
        if not "key" in result:
            return None

        return EncryptionAES.decrypt(result["key"], data)

    def set_prop_defaults(self):
        """
        Sets default properties as configured by allowed_properties
        @deprecated: code comment '....due for deprecation'.
        """
        ap = self.allowed_properties()
        for key in ap.keys():
            if 'default' in ap[key]:
                self.properties[key] = ap[key]['default']
            else:
                if 'optional' in ap[key].keys():
                    if ap[key]['optional'] is False:
                        self.properties[key] = None

    def local_import(self, classname):
        """
        Loads module and obtains class type reference given dotted class name

        @param classname:    Python class name

        @todo: Ray's plugin manager has "resource-type" mapping to "classname"
               We probably need to support same here.
        """
        strList = classname.split('.')
        classname1 = strList[-1]
        moduleList = strList[:-1]
        modules = ".".join(moduleList)
        if modules:
            module = __import__(modules)
            components = modules.split('.')
            for comp in components[1:]:
                module = getattr(module, comp)
            classitem = getattr(module, classname1)
            return classitem
        return None

    def load_class_from_pluginmgr(self, item_id):
        pluginmgr = self.item_by_path('/pluginmgr')
        if pluginmgr:
            item_class = pluginmgr.get_class_from_mappings(item_id)
        if not pluginmgr or not item_class:
            item_class = self.local_import(item_id)
        return item_class

    def _can_add_child(self, child_class):
        classname = "%s.%s" % (child_class.__module__, child_class.__name__)
        ac_re = self.allowed_children()
        return issubclass(child_class, LitpItem) and \
            self._check_inheritance(classname, ac_re)

    def create_child(self, child_id, child_type, properties):
        try:
            err_msg = "Cannot create child of type: %s" % child_type
            classitem = self.load_class_from_pluginmgr(child_type)
            if not classitem:
                logger.exception(err_msg)
                return {'error': err_msg}
        except:
            logger.exception(err_msg)
            return {'error': err_msg}

        try:
            self._id_is_allowed(child_id)
        except Exception as e:
            logger.exception("%s", str(e))
            return {'error': '%s' % (str(e))}

        vpath = self.get_vpath()
        if not vpath:
            vpath = "/"

        if self.has_child(child_id):
            return {'error': 'Child %s already exists in %s' %
                    (child_id, vpath)}

        if not self._can_add_child(classitem):
            return {'error': '%s not an allowed child of %s' %
                    (child_type, vpath)}

        child = classitem()
        try:
            self.add_child(child_id, child)
        except Exception as e:
            return {'error': 'Exception caught',
                    'exception': str(e)}
        result = self._create_child_properties(child, properties)
        if 'error' in result:
            self.remove_child(child_id)
        return result

    def _create_child_properties(self, child, properties):
        # Hack around macro property feature
        try:
            for key, value in properties.items():
                if not child._validate_property(key, value):
                    return {'error': 'Invalid property %s for %s/%s' %
                                     (key, self.get_vpath(), child.id)}

            if properties:
                result = child.update_properties(properties)
                if 'error' in result:
                    return result
                else:
                    result = child.apply_properties()
                    if 'error' in result:
                        return result
            return {'success': 'Created child %s' % (child.id,)}
        except:
            logger.exception("Error creating child item")
            return {'error': "Error creating child item"}

    def rest_create(self, itemname, classname="litp_item.LitpItem",
                    phase="default", definition="", check_props=True):
        """
        Instantiate/create a new LITP object.

        @attention:  WE NEED TO SUPPORT a DEFINITION PARAMETER HERE
            - WHEN GIVEN definition WE SHOULD locate relevant definition
                AND USE Definition->Init() call to create class

        @type  itemname: String
        @param itemname: LITP Object Identifier

        @type  classname: LITP Resource Type string
        @param classname: LITP Class of the object

        @type  phase: String
        @param phase:

        @type  definition: String
        @param definition:

        @rtype: A mapping structure.
        @return: Newly created instance of a class from the imported module
        @todo: Probably not here but in LitpRestResource we need a method for
               access control and tainted data filtering.
        @todo: Need to support instantiation by the class name.
        """
        try:
            # Get classinfo using the type name
            classitem = self.load_class_from_pluginmgr(classname)
            classname = "%s.%s" % (classitem.__module__, classitem.__name__)
            # is a subclass of LitpItem?
            if issubclass(classitem, LitpItem) is False:
                logger.error('Failed to create a new ' +
                             'instance of a class %s at %s',
                             classname, itemname)
                return {'error':
                            'Failed to create a new ' +
                            'instance of a class ' +
                            classname + ' at ' + itemname,
                        'exception': 'Class given is not an instance of ' +
                            'allowed member classes'}

            ac_re = self.allowed_children()
            allowed = self._check_inheritance(classname, ac_re)

            # @todo: Need to ensure it inherits to allowed_members
            if allowed:  # For an allowed member class lets instantiate
                newitem = classitem()   # LitpItem constructor
                newitem.id = itemname

                # Parent - kind of duplicates parent "default" handler
                newitem.phase = phase   # Phase taken from create parameter
                # Set the attribute inside "self"
                self.add_child(itemname, newitem)
                logger.info('LitpItem.rest_create: ' +
                            'New item %s created, type %s',
                            str(newitem), str(classname))
                return {'success':
                        'New item ' + itemname + ' created successfully',
                        'item': newitem}
            else:
                logger.error('LitpItem.rest_create: Failed to create a new ' +
                        'instance of a class %s at %s, object class is not ' +
                        'among allowed children', classname, itemname)
                return {
                    'error': 'Failed to create a new ' +
                            'instance of a class ' + classname + ' at ' +
                            itemname + ': Class given is not an instance of ' +
                            'allowed member classes for this parent item'}
        except Exception as e:
            logger.exception('Failed to create an item "%s"', itemname)
            return {'error': 'Item ' + itemname +
                    ' not created, please ensure specified class is ' +
                    'supported by this landscape service. Exception: ' +
                    str(e)}

    def _id_is_allowed(self, child_id):
        ''' checks that the id for a new child
            contains only allowed characters

            @type child_id:    Object ID String.
            @param child_id:   The ID of the child LITP item.
        '''
        allowed_char = '^[0-9a-zA-Z_]+$'
        regex = re.compile(allowed_char)
        if not regex.match(child_id):
            msg = ("Invalid id for child [%s]. " % (child_id) +
                "Only alphanumeric characters and underscores are accepted")
            raise Exception(msg)

    def add_child(self, child_id, child_object):
        """ Adds a child object to the current LITP item object.

            @type child_id:    Object ID String.
            @param child_id:   The ID of the child LITP item.

            @type child_object:     LITP resource item object.
            @param child_object:    The new child LITP resource object.
        """
        self._id_is_allowed(child_id)
        child_object.id = child_id
        child_object.parent = self
        self.children[child_id] = child_object

    def remove_child(self, child_id):
        if child_id in self.children:
            self.children.pop(child_id)
        elif self._has_child_field(child_id):
            delattr(self, child_id)
        else:
            raise AttributeError("No such item %s" % (child_id,))

    def _has_child_field(self, child_id):
        return (hasattr(self, child_id) and
                issubclass(type(getattr(self, child_id)), LitpItem))

    def has_child(self, child_id):
        return child_id in self.children or self._has_child_field(child_id)

    def get_child(self, child_id):
        if child_id in self.children:
            return self.children[child_id]
        else:
            return getattr(self, child_id, None)

    def __getattr__(self, key):
        if key.startswith("__"):
            raise AttributeError("No such field %s" % (key,))
        if key == "children":
            raise AttributeError("No such field %s" % (key,))
        if key in self.children:
            return self.children[key]
        else:
            raise AttributeError("No such field %s" % (key,))

    def get_children(self):
        """
        Returns a list (?) of children Resource objects of current resource
        object.
        @rtype: List
        @return: Immediate children of current object.
        """
        children = [c for id, c in self.__dict__.items() if
                    issubclass(type(c), LitpItem) and id != "parent"]
        children.extend(self.children.values())
        children.sort(key=lambda x: x.id)
        return children

    def get_children_paths(self):
        paths = [c.get_vpath() for c in self.get_children()]
        paths.sort()
        return paths

    def get_children_ids(self):
        children = [c.id for c in self.get_children()]
        children.sort()
        return children

    def get_rdni(self):
        """
        Gets rdni name from vpath relative to LitpCluster

        @rtype:  String
        @return: Value of rdni name for self
        """
        vpath = self.get_vpath()
        parent_cluster = self._lookup_parents("",
                                    "core.litp_cluster.LitpCluster")
        if parent_cluster is not None:
            # We're in a cluster - remove the cluster prefix from the path
            parent_path = parent_cluster.get_vpath()
            vpath = vpath[len(parent_path):]
        rdni = vpath.lstrip('/').replace('/', '_')
        logger.debug('get_rdni(): returning "%s" for vpath "%s"' %
                     (rdni, self.get_vpath()))
        return rdni

    def item_by_path(self, vpath):
        """
        DEPRECATED: Provides a runtime object reference from path string
        from a persistent REST URL representation
        """
        return self.get_item_by_path(vpath)

    def get_item_by_path(self, vpath):
        """
        Provides a runtime object reference from Landscape path string
        representation.
        Examples:
            - self.get_item_by_path("")
                returns tree root object
            - self.get_item_by_path("/")
                returns tree root object
            - self.get_item_by_path("/////////////")
                returns tree root object
            - self.get_item_by_path("/definition")
                returns "definition" attribute of root object
            - self.get_item_by_path("/////////definition")
                returns "definition" attribute of root object
            - self.get_item_by_path("definition")
                returns "definition" attribute of root object
            - self.get_item_by_path("/definition/item")
                returns "item" attribute
                which is an attribute of "definition",
                which is attribute of the root object
            - self.get_item_by_path("/////////definition///item")
                returns "item" attribute
                which is an attribute of "definition",
                which is an attribute of the root object.

        @type vpath: LITP resource class Path string.
        @param vpath: URI of the item to be returned.

        @rtype: LITP Resource object.
        @return: The Litp Item item identified by vpath.

        """
        this = self.get_root()
        items = vpath.split('/')
        if vpath[:1] == '/':
            items.pop(0)
        for item in items:
            if item:
                this = this.get_child(item)
                if this is None or not isinstance(this, LitpItem):
                    return None

#            if not this or not this.has_child(item):
#                return None
#            this = this.get_child(item)
        return this

    def _selfinfo(self, parameters={}):
        """
        Return a basic self description item - to be used from find,
        tree, etc.

        @type  parameters:
        @param parameters:

        @rtype:  A mapping of basic object properties.
        @return: Class, Module, Status data.
        """
        return {'class': self.__class__.__name__,
                'module': self.__class__.__module__,
                'deletable': self.deletable,
                'status': self.get_status()}

    def _selfref(self, parameters={}):
        """
        Return a basic self reference - to be used from internal code find
        methods, etc.

        @type  parameters:
        @param parameters:

        @rtype:  A mapping of basic object properties.
        @return: Class, Module, Item data.

        """
        ret_dict = {'class': self.__class__.__name__,
                    'module': self.__class__.__module__, 'item': self}
        return ret_dict

    def is_configurable(self):
        """
        @summary: Checks if the current Item should
                  be Configured
        @rtype: Boolean.
        @return:  True or False
        """
        return self.is_enforcable()

    def is_applyable(self):
        """
        @summary: Checks if the current Item should
                  be Applied
        @rtype: Boolean.
        @return:  True or False
        """
        return self.is_enforcable()

    def is_enforcable(self):
        """
        @summary: Checks if the current object is in a Pool or not
        @return: True or False
        @rtype: Boolean.
        """

        the_types = "^(core.litp_pool.LitpPool|" +\
                    "core.litp_service_group.LitpServiceGroup)$"

        return not bool(self._lookup_parents(types=the_types))

    def _lookup_parents(self, phase="", types="", names="", status="",
                        properties={}, rangepath="/"):
        """
        @summary: Find a nearest parent object
        given its name or type or status or other parameters

        @type phase:  String
        @param phase: required phase label

        @type types:  String
        @param types: required object type name

        @type names:  String
        @param names: required object name (id)

        @type status:  String
        @param status: required object status

        @type properties:  Dict
        @param properties: required properties with required values

        @type rangepath:  string
        @param rangepath: path to the object where to stop searching
                    ("/" by default)

        @rtype: LITP Resource object.
        @return:  a reference to the parent object with the desired
            properties
        """
        try:
            item = self.parent
            while item and item.get_vpath() != rangepath:
                if item._check_condition(phase, types, names, status,
                                         properties):
                    return item
                item = item.parent
            return None
        except Exception:
            logger.exception('Failed lookup parent')
            return None

    def _lookup(self, phase="", types="", names="", status="",
                properties={}, rangepath="/"):
        """
        @summary: Look Up,Left,Right,Down the tree looking for an object
            given its name or type or status or other parameters
            Basic User is Allocate method of a Resource.
            Question: are we looking for a single or multiple objects ?

        @type phase:  String
        @param phase: required phase label

        @type types:  String
        @param types: required object type name

        @type names:  String
        @param names: required object name (id)

        @type status:  String
        @param status: required object status

        @type properties:  Dictionary
        @param properties: required properties with required values

        @type rangepath:  string
        @param rangepath: path to the object where to stop searching
                    ("/" by default)

        @rtype: Dictionary
        @return: dictionary where keys are paths to found objects and
        values are references to the objects

        @todo: Incorrect behavior !!! Shall lookup from item,
               go up to parent, find there, go up the parent and so on
        """
        result = {}
        range_top = self.get_item_by_path(rangepath)
        if range_top:
            result = range_top._find(phase, types, names, status,
                                     properties)
        return result

    def _lookup_children(self, phase="", types="", names="", status="",
                         properties={}):
        """
        @summary: Look Up children objects in the tree looking for an
            object given its name or type or status or other parameters.

        @type  phase: String
        @param phase: required phase label

        @type  types: String
        @param types: required object type name

        @type  names: String
        @param names: regexp for matching required object name (id)

        @type  status: String
        @param status: required object status

        @type  properties: Dictionary
        @param properties: required properties with required values

        @rtype:  List
        @return: List of children vpaths.
        """
        res = self._find(phase, types, names, status, properties)
        #remove self
        res = [value for value in res if value != self.get_vpath()]

        return res

    def get_prop(self, prop_path):
        """
        Gets a property by path relative to this object

        @type prop_path: Litp relative URI resource path.
        @param prop_path: Property path relative to 'self'.
        Examples:looking for MACADDRESS in Node:
            - mac = self.get_prop('profile')
            - mac = self.get_prop('/p0/macaddress')

        @rtype:  String ?
        @return: Property value of object referenced in prop_path.

        """
        if '/' in prop_path:
            pathitems = prop_path.split('/')
            path = self.get_vpath()
            property_name = pathitems.pop()
            for item in pathitems:
                path = path + '/' + item
            obj = self.item_by_path(path)
        else:
            obj = self
            property_name = prop_path
        if obj and obj.properties:
            if property_name in obj.properties:
                property_value = obj.properties[property_name]
                if "macro" in self.allowed_properties().get(property_name, {}):
                    if self.allowed_properties()[property_name]['macro']:
                        if "{rdni}" in str(property_value):
                            v = str(property_value.replace("{rdni}",
                                                           self.get_rdni()))
                            logger.debug('get_prop(): name: "%s" '
                                         'expanded "%s" to "%s"' %
                                         (property_name, property_value, v))
                            return v

                        if (str(property_value).startswith('{') and
                                str(property_value).endswith('}')):
                            evaluated_value = self.get_prop(
                                property_value[1:-1].replace('.', '/'))

                            if evaluated_value is not None:
                                logger.debug('get_prop(): name: "%s" '
                                             'expanded "%s" to "%s"' %
                                             (property_name, property_value,
                                              evaluated_value))
                                return evaluated_value

                return property_value

            elif "default" in self.allowed_properties().get(property_name, {}):
                return self.allowed_properties()[property_name]['default']
        return None

    def set_prop(self, prop_name, prop_value):
        """
        Sets this objects property to a value.

        @type  prop_name: String
        @param prop_name: Object property to which value is to be assigned.

        @type  prop_value: String
        @param prop_value: Value to be assigned to the property.

        """
        ap = self.allowed_properties()
        logger.debug('mmhh13-- set property: ' + prop_name + '; value: ' + str(prop_value))
        if prop_name in ap.keys():
            self.properties[prop_name] = prop_value

    def _check_inheritance(self, classname, regexp):
        """
        ???

        @type  classname: String
        @param classname: ?

        @type  regexp: String
        @param regexp: ?

        @rtype:  Boolean
        @return: ?
        """

        try:
            if isinstance(regexp, list):
                for regexpStr in regexp:
                    cls = self.local_import(classname)
                    thismro = cls.mro()
                    regmatcher = re.compile(regexpStr)
                    for t in thismro:
                        mroitem = t.__module__ + "." + t.__name__
                        if regmatcher.match(mroitem):
                            return True
                return False
            else:
                cls = self.local_import(classname)
                thismro = cls.mro()
                regmatcher = re.compile(regexp)
                for t in thismro:
                    mroitem = t.__module__ + "." + t.__name__
                    if regmatcher.match(mroitem):
                        return True
                return False
        except Exception:
            logger.exception('Failed inheritance check')
            return False

    def _check_properties(self, properties):
        """
        Check if given LitpItem has a property with specific value

        @type  properties: List
        @param properties:

        @rtype:  Boolean
        @return: ?

        """
        for key, value in properties.items():
            if self.get_prop(key) != value:
                return False
        return True

    def _check_condition(self, phase, types, names, status, properties={}):
        """
        Check item for a match against specified conditions

        @type  phase: ?
        @param phase:  Regexp match against phase attribute

        @type  types: ?
        @param types:  Regexp match against classes parent list from MRO //
                        Take module into consideration

        @type  names: ?
        @param names:  Regexp match against id attribute.

        @type  status: ?
        @param status:  Regexp match against status attribute

        @type  properties: Dictionary
        @param properties: Key values for checking properties

        @rtype:  Boolean
        @return: ?
        """
        try:
            re_phase = re.compile(phase)
            if not re_phase.match(self.phase):
                return False
            re_names = re.compile(names)
            if not re_names.match(self.id):
                return False
            re_status = re.compile(status)
            if not re_status.match(self.get_status()):
                return False
            if not self._check_properties(properties):
                return False

            typecheck = self._check_inheritance(self.__module__ + "." +
                                                self.__class__.__name__,
                                                types)
            return typecheck
        except Exception:
            logger.exception('Failed condition check')
            return False

    def get_item_ids(self):
        """
        Landscape API: Get a list of our children items ids

        @rtype:  List of Strings
        @return: A list of strings representing our children LitpItem objects
        """
        children = [c.id for c in self.get_children()]
        children.sort()
        return children

    def get_dependencies(self):
        """

        @rtype:  Set
        @return: Set of "required" properties for an object.

        """
        require = self.properties.get('require')
        if require:
            return set(require.split(','))
        else:
            return set()

    def get_item_ids_ordered(self):
        """
        Landscape API: Get a list of our children items ids ordered by their
        dependencies as specified in "require" property of each item

        Only items at the same level of hierarchy (sharing same parent)
        are getting ordered. All items specified in "require" must exist
        No Cyclic dependencies allowed.

        Example:  Below would result in sorted order of D C B A
        /A   require=B
        /B   require=C D
        /C   require=D
        /D   require=

        Example:  Below would result in a cyclic error
        /A   require=B
        /B   require=A

        Example:  Below would result in an error on missing dependency C.
        /A   require=B
        /B   require=C

        @require: Exploits "require" property as a string of space
                            separated ids. Assuming ids are among
                            children objects of this item. So, our
                            children can refer to their siblings as
                            dependencies.
        @rtype: List of Strings
        @return: A list of strings representing our children
        LitpItem objects where List is ordered by topology sort
        algorithm based on "require" property of each item. "Require"
        property is a string
        """

        children = self.get_item_ids()
        candidates = {}
        for item in children:
            child = self.get_child(item)
            deps = child.get_dependencies()
            if not deps.issubset(children):
                raise Exception("Missing dependency in %s for %s" %
                                (item, deps.difference(children)))
            candidates[item] = deps
        # Now that we have collated all the candidates execute topology
        # sort on them
        sorted_candidates = list(topsort2(candidates))
        # concatenate list-of-lists into one list
        sorted_candidates = [item.split(' ') for item in sorted_candidates]
        sorted_candidates = list(itertools.chain(*sorted_candidates))
        return sorted_candidates

    def _perform_method_call(self, attr, method, *params, **kwargs):
        """
        Executes a named method with parameters on specified item.
        @attention: Method for internal use, does not check for instance type

        @type  attr: A LITP Resource.
        @param attr: Instance of LitpItem

        @type  method: Method name.
        @param method: The method to be executed against the specified
        resource.

        @type  params: Dictionary
        @param params: The parameters to be provided in the method call.
        """
        vpath = self.get_vpath()
        m = getattr(attr, method)
        if m and callable(m):
            logger.debug('LitpItem._perform_method_call: ' +
                         'Invoking %s on "%s"',
                         m, vpath)
            return m(*params, **kwargs)
        else:
            logger.error('LitpItem._perform_method_call: Failed due to ' +
                         'non-callable method %s on %s item', str(method),
                         vpath)
            return {'error': 'Failed due to ' +
                    'non-callable method ' + str(method) +
                    ' on "' + vpath + '" tree item'}

    def _find(self, phase="", types="", names="", status="", properties={}):
        """
        Helper method finding items with criteria under current tree

        @param phase: regexp for matching self.phase
        @type  phase: String

        @type  types:    Regexp String for LITP Class.
        @param types: regexp for matching that self is an instance of a class
                      with given name before executing anything

        @type  names:    Regexp String for attribute.
        @param names: regexp for matching own attribute name before executing
                      anything

        @type  status:    String
        @param status:    regexp for matching status of objects

        @type  properties: Dictionary of parameters.
        @param properties: Properties for exec'ed method

        @rtype:  list of strings containing URI
        @return: list of URIs of object that satisfy conditions passed
            as parameters

        """
        return self.get_all_child_item_ids(phase, types, names, status,
                                           properties)

    def _allocate(self, parameters={}):
        """
        Override-able method to allocate correct properties from either pool
        or service in the tree.

        @type  parameters: Dictionary of ??
        @param parameters: ??

        @rtype:  Dictionary
        @return: Result strings.

        """
        logger.info('LitpItem._allocate: OK on "%s"', self.get_vpath())
        self.set_status('Allocated', 'Abstract allocation OK')
        return {'success': 'LitpItem._dynamic_allocate: ' +
                'Abstract allocation OK.'}

    def _pre_configure(self, parameters={}):
        """
        Override-able method to execute pre configuration steps
        on allocated item.
        Tear down and pre-flight safety checks before running
        configuration on this item.

        @type  parameters: Dictionary of ??
        @param parameters: ??

        @rtype:  Dictionary
        @return: Result strings.

        """
        self.configuration = []
        logger.info('LitpItem._pre_configure: OK on "%s"',
                    self.get_vpath())
        return {'success': 'LitpItem._pre_configure: OK'}

    def _configure(self, parameters={}):
        """
        Override-able method to produce configuration data on allocated item.
        This function is purely abstract and subject to be overwritten.
        This method is designed to APPEND self.configuration ONLY!!!

        @type  parameters: Dictionary of ??
        @param parameters: ??

        @rtype:  Dictionary
        @return: Result strings.

        """
        try:
            #     This is an example of what could have happened
            #     location = self.get_vpath()
            #     self.configuration.append({
            #      'type': '#',
            #      'id': '# Dummy configuration ' + location,
            #      'values': [{'# Dummy configuration ': location}]
            #      })
            logger.info('LitpItem._configure: OK on "%s"', self.get_vpath())
            return {'success': 'LitpItem._configure: Default configuration OK'}
        except Exception as e:
            logger.exception("Failed configuring")
            return {'error':
                    'Configure failed on abstract configuration',
                    'exception': str(e)}

    def get_ms(self):
        ms = self._lookup("", "core.litp_node.LitpNode", "",
                          "", {'nodetype': 'management'}, "/inventory")
        if ms:
            return self.get_item_by_path(ms[0])
        return ms

    def generate_feedback(self):
        try:
            ms = self.get_ms()
            if not ms:
                return self.error('no management node in deployment')
            server = ms.get_hostname()
            if not server:
                return {'error': 'management server doesn\'t have a hostname'}
            location = self.upgrade_to_inventory_path()
            feedback_cmd = ('/usr/bin/curl -X PUT -H ' +
                            '\\"Content-Length:1024\\" -0 ' +
                            'http://' + server + ':9999' + location +
                            '/feedback')
            feedback = {'type': 'exec',
                        'id': feedback_cmd,
                        'values': {'# Feedback for location ': location}}

            onlyif_cmd = ('/usr/bin/curl -i -H \\"Content-Length:26\\" ' +
                          '-H \\"Content-Type: application/json\\" -X GET' +
                          ''' -d \\'{\\"attributes\\": [\\"status\\"]}\\' ''' +
                          'http://' + server + ':9999' + location +
                          '/show | egrep ' +
                          '\\"Applying|Removing|Unsuccessful|Failed\\"')
            feedback['values']['onlyif'] = onlyif_cmd  # Adding onlyif
            return feedback

        except Exception as e:
            logger.exception("Failed to generate the feedback")
            return {'error':
                    'LitpItem.generate_feedback: Failed on abstract'
                    ' configuration', 'exception': str(e)}

    def _post_configure(self, parameters={}):
        """
        Override-able method to execute post configuration steps on
        configured item. Amends contents under "configuration" on this
        item AFTER the configuration.
        Initially we just provide feedback, but we also need to collect
        all Requires, hence the loop
        @todo: Hardcoded "puppet" assuming the hostname is always available -
        not strictly true if we move off Puppet
        SHOULD NOT REALLY BE OVERWRITTEN UNLESS ABSOLUTELY REQUIRED

        @type  parameters: Dictionary of ??
        @param parameters: ??

        @rtype:  Dictionary
        @return: Result strings.

        """
        try:
            logger.debug('LitpItem._post_configure: Started for "%s"',
                         self.get_vpath())

            #FIXME: workaround to have same configuration on upgrade
            #branch/snapshots!
            location = self.upgrade_to_inventory_path()
            logger.debug('LitpItem._post_configure: Started for "%s"',
                         self.get_vpath())
            feedback = self.generate_feedback()
            require = []
            for c in self.configuration:
                # Well, need to work out what you want here,
                # i guess its adding a "Service" with lots of requires.
                # So we already have "vpath/feedback" resource,
                # and below just a few properties to add
                # require +> Class["id"]
                t = c['type'].title()
                require.append({'type': t, 'value': c['id']})
                logger.debug('Post-Configure found %s[%s]', t, c['id'])
            if len(require) > 0:
                feedback['values']['require'] = require  # Adding requires
            # Now we append feedback to configuration
            if feedback:
                self.configuration.append(feedback)
            logger.info('LitpItem._post_configure: Finished for "%s"',
                        self.get_vpath())
            return {'success': 'LitpItem._post_configure: Feedback ' +
                    'configuration added at ' + str(location) + '/feedback'}
        except Exception as e:
            logger.exception("LitpItem._post_configure: " +
                             "Failed to add default feedback configuration")
            return {'error': 'Failed to add default feedback configuration',
                    'exception': str(e)}

    def _is_property_optional(self, property_name):
        property_value = self.allowed_properties()[property_name]
        return property_value.get('optional') and \
            'validation' not in property_value

    def _validate(self, parameters={}):
        """
        Override-able method to validate that item has all properties
        and dependencies it needs for configure method.

        @type  parameters: Dictionary of ??
        @param parameters: ??

        @rtype:  Dictionary
        @return: Result strings.

        """
        try:
            result = {}
            if not self.id and self.parent:
                logger.error('LitpItem._validate: id has no value ')
                return {'error': 'validate: id has no value'}
            logger.debug('LitpItem._validate: Started for "%s"',
                         self.get_vpath())
            self.validated = datetime.datetime.now().isoformat(' ')
            properties = self.allowed_properties()

            if self.id in self.get_dependencies():
                logger.error("Item %s has dependency on itself",
                             self.get_vpath())
                result['require'] = {'error': 'Item cannot require itself'}

            if self.parent:
                siblings = [child.id for child in self.parent.get_children()]
            else:
                siblings = []

            missing_deps = [id for id in self.get_dependencies() if
                            id not in siblings]
            if missing_deps:
                logger.error("Item %s contains missing dependencies: %s",
                             self.get_vpath(), missing_deps,)
                result['require'] = {'error': 'Missing dependencies found:'
                                              '%s' % (missing_deps,)}

            # Check circular
            self.get_item_ids_ordered()

            # checking that all properties are evaluated
            for property_name in properties.keys():
                value = None
                optional = self._is_property_optional(property_name)
                if optional:
                    # if property is optional it might not be there
                    if property_name in self.properties.keys():
                        value = self.properties[property_name]
                else:
                    value = self.properties.get(property_name, None)
                #now validate the value
                if (value is None) and (not optional):
                    logger.debug('Failed validation - empty mandatory "%s" '
                                 'for "%s"', property_name, self.get_vpath())
                    result[property_name] = {'error':
                                             'property ' + property_name
                                             + ' has no value for ' +
                                             'a mandatory field'}
                if (value is not None):
                    logger.debug('mmhh18-- litp_item check: ' + str(properties[property_name]) + '; value: ' + str(value))
                    if properties[property_name]["type"] == "secure":
                        pass
                    if properties[property_name]["type"] == "primary":
                        logger.debug('mmhh18-- ignore primary validation')
                        pass

                    elif not self._validate_property(property_name, value):
                        logger.debug('Failed validation - on "%s" for "%s"',
                                     property_name, self.get_vpath())
                        err_msg = ('validate: property %s' +
                                   ' has a value not compliant to ' +
                                   'specification: %s')
                        result[property_name] = {'error': err_msg %
                                                 (property_name, value)}

            # checking that there are no unsupported properties
            logger.debug('mmhh19-- properties: ' + str(self.properties))
            for property_name in self.properties.keys():
                if property_name not in properties.keys():
                    logger.error('validate: property %s' +
                                 ' is not supported for %s', property_name,
                                 self.get_vpath())
                    result[property_name] = {'error':
                                             'validate: ' +
                                             'property ' + property_name +
                                             ' is not supported ' +
                                             'for this class'}
            if result == {}:
                logger.info('LitpItem._validate: Success for "%s"',
                            self.get_vpath())
                return {'success': 'LitpItem._validate: Success'}
            else:
                logger.error('Validate failed for "%s"' % self.get_vpath())
                result['error'] = 'Validate failed for %s' % self.get_vpath()
                return result

        except Exception as e:
            logger.exception('Validate failed for %s',
                             self.get_vpath())
            return {'error': 'Validate failed for %s with exception: %s ' %
                             (self.get_vpath(), str(e))}

    def is_valid(self):
        return "success" in self._validate()

    def _verify(self, parameters={}):
        """
        Override-able method to remotely verify status for applying and/or
        applied item configuration.

        @type  parameters: Dictionary of ??
        @param parameters: ??

        @rtype:  Dictionary
        @return: Result strings.

        """
        logger.info('LitpItem._verify: Verify not implemented "%s"',
                    self.get_vpath())
        return {'skipped': 'LitpItem._verify: Verify not implemented'}

    # =========================================================================
    def _dynamic_configure(self, parameters={}):
        """
        NON-OVERRIDEABLE Core method that produces contents under
        "configuration" on this item.
        This method is to be called from subtree exec to configure items.
        Checks whether item is configurable and in the right status etc.

        @type  parameters: Dictionary of ??
        @param parameters: ??

        @rtype:  Dictionary
        @return: Result strings.

        """
        vpath = self.get_vpath()
        # =====================================================================
        # First we only do anything if we are set to be configurable
        if not self.is_configurable():
            # Well, we are told we are not configurable,
            # so we succeed without much fuss
            self.configuration = []
            logger.info('LitpItem._dynamic_configure: Non Configurable "%s"',
                        vpath)
            self.configresult = {'success': 'LitpItem._dynamic_configure: ' +
                            'non configurable',
                            'classname': self.__class__.__module__ + "." +
                            self.__class__.__name__,
                            'config_result': {'skipped':
                            'LitpItem._dynamic_configure: non configurable'},
                            'post_config_result': {'skipped':
                            'LitpItem._dynamic_configure: non configurable'}}
            logger.debug('LitpItem._dynamic_configure: ' +
                         'Non configurable item on "%s"', vpath)
            return self.configresult

        # =====================================================================
        # Before we get to configure ourselves, all of our children
        # should be configured
        children = self._lookup_children()
        allchildrenok = True
        failedchild = ""
        for child in children:
            child_item = self.get_item_by_path(child)
            status = child_item.status
            if not status or not (status == "Configured"
                                  or status == "Deconfigured"
                                  or status == "Applying"
                                  or status == "Applied"
                                  or status == "Verified"):

                if (child_item.is_configurable() and not
                        self.has_more_config_priority(child_item)):
                    logger.debug('LitpItem._dynamic_configure: ' +
                                 'Found failed child "%s" on "%s"',
                                 child, vpath)
                    allchildrenok = False
                    failedchild = child
                    break

        if not allchildrenok:
            self.configresult = {'skipped': 'LitpItem._dynamic_configure: ' +
                    'one of the children not configured',
                    'classname': self.__class__.__module__ + "." +
                    self.__class__.__name__,
                    'config_result': {'skipped': 'LitpItem._dynamic_configure'
                    + ': one of the children not configured ' + failedchild},
                    'post_config_result': {'skipped':
                    'LitpItem._dynamic_configure: one of the children not'
                    + ' configured' + failedchild}}
            return self.configresult

        try:
            # ====================================================
            # Invoking validate - all required properties should
            # be valid before attempting to configure

            logger.debug('LitpItem._dynamic_configure: ' +
                         '_validate() started on "%s"', vpath)
            validate_result = self._validate()
            logger.debug('LitpItem._dynamic_configure: ' +
                         '_validate() finished on "%s"', vpath)

            self.configresult['validate'] = validate_result

            if not 'success' in validate_result:

                appendage = '<unknown>'
                key = 'error'

                if 'error' in validate_result.keys():
                    appendage = validate_result['error']
                elif 'skipped' in validate_result.keys():
                    key = 'skipped'
                    appendage = validate_result[key]

                logger.error('LitpItem._dynamic_configure: ' +
                             '%s in _validate() on "%s" (%s)',
                             key, vpath, appendage)

                self.configresult[key] = {key:
                                          'LitpItem._dynamic_configure: ' +
                                          key + ' in _validate'}

                if 'error' in validate_result.keys():
                    return validate_result  # Break out early
        except Exception as e:
            logger.exception('LitpItem._dynamic_configure: ' +
                             ' _validate() caught exception on "%s"(%s)',
                             vpath, str(e))
            self.configresult['error'] = ('LitpItem._dynamic_configure: ' +
                                          'exception caught')
            self.configresult['exception'] = str(e)
            self.configresult['validate'] = {
                  'error': 'LitpItem._dynamic_configure: Exception in '
                  '_validate method ',
                  'exception': str(e)}
            return {'error': 'Exception'
                    'in _validate method ',
                    'exception': str(e)}

        try:
            # ===================================================
            # Invoking pre_configure - hopefully populating own
            # configuration records
            logger.debug('LitpItem._dynamic_configure: ' +
                         ' _pre_configure() started on "%s"', vpath)
            self.configresult = {}  # Fresh start on the results now
            self.configresult['classname'] = self.__class__.__module__ + "." +\
                                             self.__class__.__name__
            self.configresult['pre_config_result'] = \
                                            self._pre_configure(parameters)
            logger.debug('LitpItem._dynamic_configure: ' +
                         ' _pre_configure() finished on "%s"', vpath)
        except Exception as e:
            logger.exception('LitpItem._dynamic_configure: ' +
                             ' _pre_configure() caught exception on "%s"',
                             vpath)
            self.configresult['pre_config_result'] = {
                  'error': 'LitpItem._dynamic_configure: ' + \
                           'Exception in _pre_configure method',
                  'exception': str(e)}
        if not 'success' in self.configresult['pre_config_result']:
            logger.error('LitpItem._dynamic_configure: ' +
                         'Error in _pre_configure() on "%s"', vpath)
            self.configresult['error'] = ('LitpItem._dynamic_configure: ' +
                                    'Unsuccessful _pre_configure execution')
            return self.configresult  # Break out early - no reason to continue

        # =====================================================================
        # Invoking _configure - hopefully populating own configuration records
        try:
            logger.debug('LitpItem._dynamic_configure: ' +
                         '_configure() started on "%s"', vpath)
            self.configresult['config_result'] = self._configure(parameters)
            logger.debug('LitpItem._dynamic_configure: ' +
                         '_configure() finished on "%s"', vpath)
            logger.debug('mmhh5-- vpath: ' + vpath)
        except Exception as e:
            logger.debug('mmhh5-- vpath exception: ')
            logger.exception('LitpItem._dynamic_configure: ' +
                             '_configure() caught exception on "%s"', vpath)
            self.configresult['config_result'] = {
                  'error': 'LitpItem._dynamic_configure: Exception in ' +
                  '_configure method ', 'exception': str(e)}
        if not 'success' in self.configresult['config_result']:
            logger.error('LitpItem._dynamic_configure: ' +
                         'Error in _configure() on "%s"', vpath)
            self.configresult['error'] = ('LitpItem._dynamic_configure: ' +
                                          'Unsuccessful _configure execution')
            # Break out early - no reason to continue
            return self.configresult

        # =====================================================================
        # Invoking post configuration -
        # hopefully populating own feedback configuration records
        try:
            logger.debug('LitpItem._dynamic_configure: ' +
                         '_post_configure() started on "%s"', vpath)
            self.configresult['post_config_result'] = \
                                            self._post_configure(parameters)
            logger.debug('LitpItem._dynamic_configure: ' +
                         '_post_configure() finished on "%s"', vpath)
        except Exception as e:
            logger.exception('LitpItem._dynamic_configure: ' +
                             '_post_configure() caught exception on "%s"',
                             vpath)
            self.configresult['post_config_result'] = {
                    'error': 'LitpItem._dynamic_configure: \
                    Exception in _post_configure method',
                    'exception': str(e)}
        if 'success' in self.configresult['post_config_result']:
            if "deconfigure" in parameters:
                self.set_status('Deconfigured',
                                'LitpItem._dynamic_configure: Deconfigured')
                logger.info('LitpItem._dynamic_configure: ' +
                            '"%s" Deconfigured', vpath)
            else:
                self.set_status('Configured',
                                'LitpItem._dynamic_configure: Configured')
                logger.info('LitpItem._dynamic_configure: ' +
                            '"%s" Configured', vpath)
            self.configresult['success'] = ('LitpItem._dynamic_configure: '
                                        + 'Success in both _configure and '
                                        + '_post_configure')
        else:
            logger.error('LitpItem._dynamic_configure: ' +
                         'Error in _post_configure() on "%s"', vpath)
            self.configresult['error'] = ('LitpItem._dynamic_configure: ' +
                                    'Unsuccessful _post_configure execution')

        return self.configresult

    def _dynamic_allocate(self, parameters={}):
        """
        This method is designed to be overridden ONLY by LitpResource

        @type  parameters: Dictionary of ??
        @param parameters: ??

        @rtype:  Dictionary
        @return: Result strings.

        """
        logger.debug("LitpItem._dynamic_allocate Allocating %s",
                     self.get_vpath())
        return self._allocate(parameters)

    def _dynamic_release(self, parameters={}):
        """
        Core method to release an allocated entry -
        only override if really needs be

        @type  parameters: Dictionary of ??
        @param parameters: ??

        @rtype:  Dictionary
        @return: Result strings.

        """
        vpath = self.get_vpath()
        if self.origin:
            original = self.item_by_path(self.origin)
            if original:
                self.set_status('Initial', 'LitpItem._dynamic_release')
                original.set_status('Available', 'LitpItem._dynamic_release')
                original.consumer = None
                self.configuration = []     # Controversial !!!
                logger.info('LitpItem._dynamic_release: ' +
                            'Released on "%s", origin "%s" made available',
                            vpath, self.origin)
                result = {'success':
                          'LitpItem._dynamic_release: Released, ' +
                          'origin made available',
                          'origin': self.origin}
            else:
                logger.error('LitpItem._dynamic_release: ' +
                             'Failed to release on "%s", ' +
                             'origin "%s" not found',
                             vpath, self.origin)
                result = {'error': 'LitpItem._dynamic_release: ' +
                          'Failed to release - ' +
                          'cannot find the origin item',
                          'origin': self.origin}
        else:
            self.set_status('Available', 'LitpItem._dynamic_release')
            logger.info('LitpItem._dynamic_release: Released on "%s"', vpath)
            result = {'success': 'LitpItem._dynamic_release: Released'}
        self.origin = None
        return result

    def _dynamic_validate(self, parameters={}):
        """
        @summary: Core method to validate integrity of content for
        allocated properties. Currently just calls override-able _validate()

        @type  parameters: Dictionary of ??
        @param parameters: ??

        @rtype:
        @return:

        """
        return self._validate(parameters)

    def _dynamic_verify(self, parameters={}):
        """
        @summary: Core method to remotely verify status for applying and/or
        applied items
        @type  parameters: Dictionary of ??
        @param parameters: ??
        @rtype:  Dictionary
        @return: Result strings.

        """
        preamble = self.__class__.__name__ + '._dynamic_verify: '

        # Before we get to verify ourselves,
        # all of our children should be verified
        status = self.get_status()
        vpath = self.get_vpath()
        logger.debug((preamble + 'Started on %s') % vpath)

        # Filter only those that are not "Verified"
        badchildren = self._lookup_children(status='Failed')

        if badchildren:      # If some still there its a problem
            result = {'skipped': preamble + 'one of the children not verified',
                      'classname': self.__class__.__module__ + "." +
                                   self.__class__.__name__}
            logger.error((preamble + 'One of the children failed on %s') % \
                         vpath)
            return result
        else:
            logger.debug((preamble + 'Starting _verify() on %s') % vpath)
            result = self._verify(parameters)

        # Now update status if required.
        if 'error' in result:
            if status in ('Applied', 'Verified',
                          'Applying', 'Removing', 'Removed'):
                msg = preamble + result['error']
                if 'exception' in result:
                    msg += '\n (Exception :' + result['exception'] + ')'

                if status in ('Removing', 'Removed'):
                    self.set_status('Unsuccessful', msg)
                else:
                    self.set_status('Failed', msg)

        elif 'success' in result:
            newstatus = 'Verified'
            if status in ('Removing', 'Removed', 'Unsuccessful'):
                newstatus = 'Removed'

            self.set_status(newstatus,
                            preamble + 'verified successfully')

        return result

    def allowed_methods(self):
        """
        List of allowed methods.
        @rtype:  List
        @return: Allowed methods on current objects, excluding CRUD methods.
        """

        am = {}

        am['save'] = {'help': 'Save the entire Landscape tree image to a ' +
                      'back-end storage'}
        am['restore'] = {'help': 'Load the entire Landscape tree from a ' +
                                 'last saved image in back-end storage'}
        am['exportxml'] = {'help': 'Export subtree to a xml encoded string'}
        am['exportjson'] = {'help': 'Export subtree to a json encoded string'}
        am['load'] = {'help': 'Import definition from xml file'}
        am['materialise'] = {'help':
                             'Materialise the definition into inventory)'}
        am['materialise']['parameters'] = {
                    'destination': {'help': 'Optional destination, ' +
                                     'if target inventory name should be ' +
                                     'different from the original definition'}}
        am['allocate'] = {'help': 'Iterates over a subtree and executes ' +
                                  'allocate methods on each supporting item'}
        am['allocate']['parameters'] = default_parameters
        am['configure'] = {'help': 'Iterates over a subtree and executes ' +
                                   'configure methods on each supporting item'}
        am['configure']['parameters'] = default_parameters
        am['verify'] = {'help': 'Iterates over a subtree and executes ' +
                                'verify methods on each supporting item'}
        am['verify']['parameters'] = default_parameters
        am['validate'] = {'help': 'Iterates over a subtree and executes ' +
                                  'validate methods on each supporting item'}
        am['validate']['parameters'] = default_parameters
        am['feedback'] = {'help': 'Populates applied date stamp ' +
                                  '(to be used by feedback hooks)'}
        am['fail'] = {'help': 'Populates failed date stamp ' +
                              '(to be used by feedback hooks)'}
        return am

    def allowed_properties(self):
        """
        Defines the object's allowed properties adding the following to the
        litp_properties default dictionary:
            - name, initialised to 'name'
            - require, initialised to 'require'

        @rtype:  dict
        @return: Object's allowed properties.
        """
        ap = {}
        ap['name'] = create_str_property('name')
        ap['require'] = create_str_property('require')
        ap['primary'] = create_str_property('primary')
        return ap

    def allowed_children(self):
        """
           Return the object's list of allowed LITP resource object
           types.

        @rtype:  List
        @return: LITP object's resource object types.

        """
        return ['core.litp_item.LitpItem']

    @serialized
    def supported_methods(self):
        """
        Return a Serialized list of supported methods.

        @rtype:  Serialised List.
        @return: The LITP object's supported methods.

        """
        return self.allowed_methods()
    supported_methods.exposed = True

    @serialized
    def supported_properties(self):
        """
        Return a Serialized list of supported properties.

        @rtype:  Serialised List.
        @return: The LITP object's supported properties.

        """
        return self.allowed_properties()
    supported_properties.exposed = True

    def apply_properties(self):
        """
        Overridable method to support custom populate of internal values
        from properties
        """
        return {'success': 'Nothing to do'}

    def litp_add(self, itemname, classname, definition=""):
        """
        REST POST handler method
        Method deserializes values provided in the CherryPy request body.
        Invoked by PUT method.

        @type  itemname: LITP object name ?
        @param itemname: The LITP object to be added to the resource
        tree ?

        @type  classname: LITP object/resource type.
        @param classname: The type of object/resource  to be added to the
        resource tree.

        @type  definition: ?
        @param definition: ?

        @rtype:  A serialised result string.
        @return: Success string or error string with exception details.

        @note: that instantiation already happened in rest_create so all
                we need is to call update()
        """
        try:
            result = self._update(itemname, manual_allocation=False)
            # remove any success message
            if 'error' in self.litp_serialize(result):
                if "success" in result:
                    del result["success"]

                chars = ["{", "}", "[", "]", '"']
                errorstr = 'Item was not created. ' \
                    + str(result.values()).translate(None, ''.join(chars))

                logger.error('LitpItem.litp_add: Errors '
                    + 'encountered updating property. ' + errorstr)
                msg = {'error': errorstr}
                if 'exception' in result:
                    msg.update({'exception': eval(str(result))['exception']})
                result = msg
                if self.parent:
                    # we don't want the attribute to be hanging from the
                    #parent anymore since its creation failed,
                    #so just delete it
                    delattr(self.parent, self.id)
            else:
                logger.info("LitpItem.litp_add: Success %s" % itemname)
                result = {'success': 'LitpItem.litp_add: Success'}
            return self.litp_serialize(result)
        except Exception as e:
            logger.error('LitpItem.litp_add: Exception caught ' + str(e))
            result = self.litp_serialize({'error': 'LitpItem.litp_add: ' +
                                                   'Exception caught',
                                                   'exception': str(e)})
            return result
    litp_add.allowed_options = {'classname':
                                {'name': 'classname',
                                 'help': 'Class name, e.g. "module.MyClass"'}}

    def _update(self, itemname, manual_allocation=True):
        try:
            req = self.request_body()
            if len(req) > 0:
                old_properties = copy.deepcopy(self.properties)
                new_properties = self.litp_deserialize(req)
                result = self.update_properties(new_properties)
                if result and 'success' in result:
                    logger.info("Updating properties on %s to %s",
                                self.get_vpath(), new_properties)
                    rc_app = self.apply_properties()

                    if rc_app and 'error' in rc_app:
                        if 'exception' in rc_app:
                            errormsg = 'exception: ' + rc_app.get('exception')
                        else:
                            errormsg = rc_app.get('error')

                        logger.error(errormsg)
                        return {"error": errormsg}
                else:
                    logger.error(str(result))

                if (manual_allocation and self.is_configurable() and
                    (old_properties != self.properties)):
                    msg = ('LitpItem.litp_update: Update successful, ' +
                           'Item Validated and status changed to Allocated ' +
                           'after manual allocation')
                    _statusmap = {
                        'Initial': 'Initial',
                        'Available': 'Available'}
                    self.set_status(_statusmap.get(self.status, 'Allocated'),
                        msg)
                    result['success'] = msg
                    return result
                else:
                    return result
            else:
                return {'warning': 'LitpItem.litp_update: Nothing to update'}

        except Exception as e:
            logger.exception("Error updating properties on %s",
                self.get_vpath())
            result = {'error': 'Failed to update',
                               'exception': str(e)}
            return result

    @serialized
    def litp_update(self, itemname, manual_allocation=True):
        """
        REST PUT handler method
        Method de-serialises values provided in the CherryPy request body.
        Invoked by REST POST method.

        @type  itemname: LITP object name ?
        @param itemname: The LITP object to be updated on the resource tree

        @rtype:  A serialised result string.
        @return: Success string or string with error/warning details.
        """

        return self._update(itemname, manual_allocation)
    litp_update.exposed = True

    def _validate_property(self, name, value):
        ap = self.allowed_properties()
        if name not in ap:
            return False
        if "macro" in ap[name] and ap[name]['macro']:
            if '{rdni}' in str(value):
                logger.debug('_validate_property: property "%s" '
                             'value "%s" includes "{rdni}"' % (name, value))
                # special case - allow strings like "/home/{rdni}"
                # We replace "{rdni}" with the actual value, then fall
                # through to normal regex checking
                value = value.replace("{rdni}", self.get_rdni())
                logger.debug('_validate_property: expanded to "%s"' % value)
            elif str(value).startswith('{') and value.endswith('}'):
                logger.debug('_validate_property: property "%s" '
                             'value "%s" looks like a macro reference"' %
                             (name, value))
                # This property contains a macro reference, of the form
                # "{childid.propertyname}".  We can turn that into a
                # relative path ("childid/propertyname") and use
                # get_prop() to retrieve the value of that property. If
                # the property does not exist (yet), get_prop() will
                # return None.
                ref_path = value[1:-1].replace('.', '/')

                if ref_path == name:
                    # Caught a self-reference: foo = {foo}
                    logger.debug('_validate_property: self-referencing '
                                 'property "%s" has value "%s"' %
                                 (name, value))
                    return False

                new_value = self.get_prop(ref_path)
                if new_value is not None:
                    # We expanded the reference successfully - use
                    # the new value for validation.
                    value = new_value
                    logger.debug('_validate_property: expanded to "%s"' %
                                 value)
                else:
                    # If property is an unresolved macro; return False
                    if self.is_in_inventory():
                        logger.debug('_validate_property: '
                                     'failed to expand inventory macro')
                        return False
                    # This is an unresolved  macro reference, so just
                    # check the contents so that it is just dot-separated
                    # identifiers.
                    logger.debug('_validate_property: '
                                 'validating definition macro')
                    re_macro = re.compile('^[a-zA-Z0-9_]+(\.[a-zA-Z0-9_]+)*$')
                    return bool(re_macro.match(unicode(value[1:-1])))

        # Either this property doesn't support macro references, or
        # this value isn't one, or we resolved the reference to an actual
        # value. Apply the property's regex as normal.
        property_regexp = ap[name].get('regexp', '')
        re_phase = re.compile(property_regexp)
        return not property_regexp or bool(re_phase.match(unicode(value)))

    def _can_delete_property(self, property_name):
        property_value = self.allowed_properties()[property_name]
        return property_value.get("optional") is True or \
            property_value.get("validation") == "validate"

    def update_properties(self, new_properties):
        """
        @summary:
        Method validates properties and then updates them.
        If the user tries to update properties that are not supported
        an error is reported for each unsupported property.

        @type  new_properties: Dictionary of properties.
        @param new_properties: Properties to validate & update.

        @rtype:  A serialised result string.
        @return: Result string with success/error/warning details.

        """
        result = {}
        try:
            logger.debug('starting LitpItem.update_properties')
            applying_props = {}
            removed_props = list()

            for name, property_value in self.allowed_properties().items():
                if property_value.get("validation") == "create":
                    if name not in new_properties:
                        return {'error': 'Missing required ' +
                                         'property: %s' % (name,)}

            # remove properties not allowed before adding them
            allowed_prop = self.allowed_properties()
            for property_name, value in new_properties.items():

                # ^ character says he want to remove the property
                remove = property_name.startswith('^')
                if remove:
                    property_name = property_name[1:]

                    if property_name not in allowed_prop:
                        result[property_name] = {'error':
                                                 "property does not exist"}
                        continue

                    # Prevent update command to delete NOT optional
                    # properties
                    if not self._can_delete_property(property_name):
                        result[property_name] = {'error':
                            "%s property is not optional " % property_name + \
                            "and can not be removed"}
                        continue

                    removed_props.append(property_name)
                    continue

                if property_name not in allowed_prop:
                    result[property_name] = {'error':
                        'Property not supported: %s' % (property_name,)}
                elif self._validate_property(property_name, value):
                    if allowed_prop[property_name]["type"] == "secure":
                        enc_result = EncryptionAES.readkey("/root/litp_key")
                        if "key" in enc_result:
                            new_properties[property_name] = \
                                EncryptionAES.encrypt(enc_result["key"], value)
                        else:
                            result["error"] = enc_result["error"]
                    elif allowed_prop[property_name]["type"] == "hash":
                        new_properties[property_name] = crypt.crypt(
value, crypt.METHOD_SHA512).replace('$', "\\$")

                    applying_props[property_name] = \
                        new_properties[property_name]
                else:
                    result[property_name] = {'error':
                        'Could not set property with name %s. '
                        'Invalid value: \"%s\" (%s)' % (property_name, value,
                        allowed_prop[property_name]["regexp"])}

            # Until here result is only appending errors
            # so if there's any error we shouldn't apply
            # the changes
            if len(result):
                return result

            if removed_props:
                for prop in removed_props:
                    del self.properties[prop]

            if applying_props or removed_props:
                self.properties.update(applying_props)
                result['success'] = ('Successfully updated the properties')
            else:
                result['error'] = ('No valid properties to update')
            return result
        except Exception as e:
            result = {'error': 'Failed to update ' + str(e)}
            return result

    def litp_read(self, params=None):
        """
        REST GET handler method
        Method provides access to serialised content of requested instance.
        Invoked by REST GET method.

        @type  params: ?
        @param params: Not currently used.

        @rtype:  A serialised result string.
        @return: Object content (or error) details.

        """
        try:
            response = self
            result = (response)
            return self.litp_serialize(result)
        except Exception as e:
            logger.exception("litp_index: Exception on read")
            result = self.litp_serialize({'error': 'litp_index: Failed to ' +
                              'serialize the response',
                              'exception': str(e)})
            return result

    @serialized
    def find(self, names=None, resource=None):
        response = []  # Default response for no item found

        preamble = self.__class__.__name__ + '.find: '

        vpath = self.get_vpath()
        logger.info("Item VPath: %s\n" % vpath)

        lkup_classname = ''
        lkup_names = ''

        if names:
            lkup_names = '^(%s)$' % '|'.join(names.split(','))
            # Validate regular expression
            try:
                re.compile(lkup_names)
            except sre_constants.error as e:
                return {"error": "Invalid regular expression, %s: %s" %
                                 (lkup_names, e)}
            logger.info((preamble + "%s processed into %s") %
                        (names, lkup_names))

        if resource:
            logger.info(preamble + "Resource type: " + resource)

            try:
                classitem = self.load_class_from_pluginmgr(resource)
                if not classitem:
                    return[]
            except Exception as e:
                msg = "Failed to determine class for resource " + resource
                logger.exception(preamble + msg)
                return self.litp_serialize({'error': 'find: ' + msg})

            lkup_classname = "%s.%s" % \
                             (classitem.__module__, classitem.__name__)
            logger.info(preamble + "Classname: " + lkup_classname)

            if issubclass(classitem, LitpItem) is False:
                msg = "Invalid Resource type '%s'" % resource
                logger.exception(preamble + msg)
                return self.litp_serialize({'error': 'find: ' + msg,
                                            'exception': msg})

        if lkup_classname or lkup_names:
            logger.info("Lookup keys: class %s names %s" %
                        (lkup_classname, lkup_names))
            children = self._lookup_children(types=lkup_classname,
                                             names=lkup_names)
            if children:
                return children

        return self.litp_serialize(response)
    find.exposed = True

    @serialized
    def show(self, *args, **kwargs):
        """
        REST GET handler method
        Method provides access to serialised content of requested instance.
        Invoked by REST GET method.

        @rtype: A serialised result String.
        @return: Object Content (or error) details.

         """
        try:
            #info = self._request_dict()

            mode = ''
            attributes = []
            if 'verbose' in kwargs:
                mode = kwargs['verbose']

            if 'attributes' in kwargs:
                attributes = ast.literal_eval(kwargs['attributes'])

            if 'software_version' in attributes:
                recursive = 'recursive' in kwargs
                return self._show_packages(recursive)

            if 'version' in attributes:
                return {'error': {"version": "requested attribute is not " \
                        "supported by this class"}}
            if 'recursive' in kwargs:
                response = []
                all_ids = self.get_all_child_item_ids()
                for path in all_ids:
                    obj = self.get_item_by_path(path)
                    if mode == 'l':
                        response.append(path)
                    else:
                        if self.__class__.__name__ == "LitpRoot" \
                            and path == '':
                            path = '/'
                        response.append((path, obj._show(mode, attributes)))
            # should be only -l
            elif 'recursive' not in kwargs and mode == 'l':
                response = self.get_item_ids()
                response.sort()

            else:
                response = self._show(mode, attributes)
            return response
        except Exception as e:
            logger.exception("Exception in show")
            result = ({'error': 'litp_show: Failed to ' +
                              'serialize the response',
                              'exception': str(e)})
            return result
    show.exposed = True

    @serialized
    def litp_delete(self, *args, **kwargs):
        """
        REST DELETE handler method
        Method removes itself from the parent, therefore removing itself
        from LITP Tree.

        @rtype:  Serialised string.
        @return: Success or error details.

        """
        try:
            force = None
            if 'force' in kwargs:
                force = kwargs['force']
            if force:
                self.parent.remove_child(self.id)
                return ({
                'success': 'LitpItem.litp_delete: Item deleted ' + self.id})

            # make sure the object is not in /depmgr
            if '/depmgr' not in self.get_vpath():
                if not self.deletable:
                    logger.info("Preventing delete on %s. " +
                            "Object need to be " +
                            "deconfigured first", self.get_vpath())
                    return self.litp_serialize({'error':
                        'LitpItem.litp_delete: Please deconfigure ' +
                        'the item before you delete. Status must be set ' +
                        'to "Removed" first, this may take 3 minutes'})

            children = self._lookup_children()
            for child in children:
                obj = self.get_item_by_path(child)
                deletable = obj.deletable
                if not deletable:
                    logger.info("Preventing delete on %s. " +
                                "Children can't be " +
                                "deleted %s", self.get_vpath(), child)
                    return self.litp_serialize({'error':
                                        'LitpItem.litp_delete: Children ' +
                                        'can\'t be deleted %s' % child})

            logger.info("Deleting %s", self.get_vpath())
            self.parent.remove_child(self.id)
            return ({'success': 'LitpItem.litp_delete: Item deleted ' +
                                self.id})
        except Exception as e:
            return ({'error': 'LitpItem.litp_delete: Failed to delete item',
                     'exception': str(e)})
    litp_delete.exposed = True

    @serialized
    def exportjson(self):
        """
        Serialize self using object serializer helper into a JSON string

        @todo: Thread Safety is a major problem for the LITP Item, and
        critically for DUMP/LOAD.

        @rtype:  Serialised String.
        @return: Serialised Object or error string details.

        """
        savedparent = self.parent

        try:
            jsonpickle.set_encoder_options('simplejson', sort_keys=True,
                                           indent=4)
            # @attention: This is the most critical place here
            # for the duration of pickle we are running without parent
            # I REALLY REALLY WANT TO LOCK THIS INSTANCE OF AN OBJECT!!!
            self.parent = None
            result = jsonpickle.encode(self)
            self.parent = savedparent
            return result
        except Exception as e:
            self.parent = savedparent       # we need to restore our parent
            logger.exception("LitpItem.exportjson: could not serialize")
            return {'error': 'LitpItem.exportjson: ' +
                    'Failed to serialize object data',
                    'exception': str(e)}
    exportjson.exposed = True

    def _show_packages(self, recursive):
        if recursive:
            data = []
            nodes = self._find(types='core.litp_node.LitpNode')
            for path in nodes:
                obj = self.get_item_by_path(path)
                res = obj.query_packages()
                if isinstance(res, list):
                    res.sort()
                data.append((path, res))

            all_packages = data
        else:
            all_packages = self.query_packages()
        return all_packages

    def eric_versions(self):
        return self.parent.eric_versions()

    def query_packages(self):
        """
        Returns list of installed packages on node - on LitpNode
        On LitpItem does nothing
        """
        logger.info("Skipped - no packages to list")
        return []

    def _can_serialize(self, item):
        """
        Returns serialised LITP object or "False" if it can't be
        serialised.

        @type  item: LITP object/resource instance.
        @param item: the object to serialise.

        @rtype: Boolean
        @return:
            - False if an object cannot be serialised.
            - Otherwise, the serialised object.

        """
        try:
            json = item.exportjson()
            if ('error' in json and 'exception' in json and
            (('litp_serialize: Failed to serialize data' in json) or
            ('LitpItem.exportjson: Failed to serialize object data' in json))):
                return False
            else:
                loaded = self._loadjson(json)
                return json == jsonpickle.encode(loaded)
        except:
            return False

    def _check_json_export(self):
        """
        Checks if object can be serialised for json export.
        Raises invalid state exception for object if it can't be serialised.

        """
        if not self._can_serialize(self):
            invalid_item = self._find_invalid_item(self)
            raise Exception("Item %s is in an invalid state and cannot "
                            "be serialized" % (invalid_item.get_vpath(),))

    def _find_invalid_item(self, item):
        """
        Checks if all the child objects of a LITP item can be
        serialised.

        @type  item: LITP object/resource item.
        @param item: the object whose children are to be validated.

        @rtype: LITP object/resource item.
        @return:
            - the current LITP item if it all children can be serialised.
            - Otherwise, details of the children that cannot be serialised.

        """
        for child in item.get_children():
            if not self._can_serialize(child):
                return self._find_invalid_item(child)
        return item

    def exportxml(self):
        """
        Export landscape object to xml

        @rtype:  String
        @return: Either:
            - an XML representation of the current LITP object/resource item;
            - or, a serialised LITP error string.
        """
        try:
            pluginmgr = self.item_by_path('/pluginmgr')
            object_xml = pluginmgr.save_object(self)
            return object_xml
        except Exception, e:
            logger.exception("Failed to serialize object data")
            return self.litp_serialize({'error': 'LitpItem.exportxml: ' +
                                        'Failed to serialize object data',
                                        'exception': str(e)})
    exportxml.exposed = True

    @staticmethod
    def _loadjson(data):
        """
        Deserialise a LITP object.

        @type  data: A serialised LITP object string.
        @param data: The LITP object to deserialise.

        @rtype:  A json object represention.
        @return: The LITP object in unserialised json format.
        """
        #  Deserialize self using object serializer helper into a JSON
        #                string
        unpickled = jsonpickle.decode(data)
        return unpickled

    def _file_exists(self, filepath):
        return os.path.exists(filepath)

    def _load_file(self, filepath):
        f = open(filepath, 'r')
        data = f.read()
        f.close()
        return data

    def _loadjson_fromfile(self, filepath):
        data = self._load_file(filepath)
        return self._loadjson(data)

    def _read_file_stream(self, file_stream):
        """
        Reads data from a given file stream until end of stream.

        @type  file_stream: file stream.
        @param file_stream: the data source.

        @rtype:  String
        @return: The data read form the stream.
        """
        return file_stream.read()

    @serialized
    def load(self, loadFile):
        """
        Load xml file into Landscape management system ??

        @type  loadFile: File name.
        @param loadFile: The name of the xml file to be loaded.

        @rtype:  Serialised result string.
        @return: Success or failure details.
        """

        try:
            data = loadFile.file.read()
            return self._load_child_from_xml(data)
        except Exception as e:
            logger.exception("Failed to deserialize xml data")
            return {'error': str(e)}

    load.exposed = True

    def _load_child_from_xml(self, xml_data):
        pluginmgr = self.item_by_path('/pluginmgr')
        errors = pluginmgr.validate_xml(xml_data)
        if errors:
            return (errors)

        newobject = pluginmgr.load_object(xml_data)

        if self.has_child(newobject.id):
            logger.error('Child %s already exists in %s',
                         newobject.id, self.get_vpath())
            return {'error': 'Child %s already exists in %s' %
                             (newobject.id, self.get_vpath())}

        ac_re = self.allowed_children()
        if not self._check_inheritance("%s.%s" %
            (newobject.__module__, newobject.__class__.__name__), ac_re):
            logger.error('%s not allowed child of %s', newobject.id,
                         self.get_vpath())
            return {'error': '%s not allowed child of %s' %
                    (newobject.id, self.get_vpath())}
        self.add_child(newobject.id, newobject)
        logger.info("Successfully loaded xml")
        return {'success': 'LitpItem.loadXml: ' +
                'Loaded from serialized representation'}

    @serialized
    def loadjson(self, loadFile):
        """
        Load a json serialised file into the Landscape management system ??

        @type  loadFile:    File name.
        @param loadFile:    The name of the json file to be loaded.

        @rtype:  Serialised result string.
        @return: Success or failure details.

        """
        #   Re-Instantiate this object from pickled representation
        #   @param loadFile: File upload containing json data
        #   @todo: VERY INSECURE -- data needs to be sanitized before loading
        #   as we accept it from BODY
        try:
            data = self._read_file_stream(loadFile)
            newobject = self._loadjson(data)

            # return newobject.dump()
            # @todo: We need to sanitize newobject to ensure all
            # attributes/classes are ok
            if self.parent:
                # Renaming id and replacing parent to reflect new location of
                # this imported object
                newobject.id = self.id
                self.parent.add_child(self.id, newobject)
                return ({'success':
                    'LitpItem.load: Loaded from serialized representation'})

            elif self.__class__.__name__ == "LitpRoot":
                self.inventory = newobject.inventory
                self.inventory.parent = self
                self.definition = newobject.definition
                self.definition.parent = self
                self.bootmgr = newobject.bootmgr
                self.bootmgr.parent = self
                self.cfgmgr = newobject.cfgmgr
                self.cfgmgr.parent = self
                return ({'success':
                    'LitpItem.load: Loaded from serialized representation'})
            else:
                return (
                    {'error': 'LitpItem.load: Can not deserialize object ' +
                              'which has no parent'})
        except Exception as e:
            return ({
                'error': 'LitpItem.load: Failed to deserialize object data',
                'exception': str(e)})
    loadjson.exposed = True

    @serialized
    def activate(self):
        '''
        @summary: This exposed method Activates the Item
                  Base implementation - no-op
        @return: Dictionary with result.
        @rtype: Dictionary
        '''
        preamble = self.__class__.__name__ + '.activate: '
        return {'skipped': preamble + 'Nothing to activate'}
    activate.exposed = True

    @serialized
    def deactivate(self):
        '''
        @summary: This exposed method Deactivates the Item
                  Base implementation - no-op
        @return: Dictionary with result.
        @rtype: Dictionary
        '''
        preamble = self.__class__.__name__ + '.deactivate: '
        return {'skipped': preamble + 'Nothing to deactivate'}
    deactivate.exposed = True

    @background
    def allocate(self, job, origin=None, range="/inventory"):
        """
        Recursively allocates resources under current LITP object/resource
        item.

        @type  range: String
        @param range: Path representing top object delimiting
                      search for available resources.

        @rtype:  Serialised hierarchy string.
        @return: Either:
                - Landscape subtree with allocated resources ?
                - Error information.
        """

        try:
            results = []
            sorted_ids = self.all_children_by_dependency()

            for obj_path in sorted_ids:
                obj = self.get_item_by_path(obj_path)
                results.append((obj_path,
                                obj._dynamic_allocate({'range': range,
                                                       'origin': origin})))

            return results
        except Exception as e:
            logger.exception("LitpItem.allocate: Exception caught")
            return {'error': 'LitpItem.allocate: Exception caught',
                    'exception': str(e)}

    @background
    def release(self, job=None, phase="default",
                types="core.litp_item.LitpItem",
                names="", params="", status=""):
        """
        Recursively releases resources under current LITP object/resource
        item.

        @rtype:  Serialised hierarchy string.
        @return: Either:
            - Landscape subtree after release of resources ?
            - Error information.

        """
        try:
            results = []
            all_ids = self._find(phase, types, names, status)

            for obj_path in all_ids:
                obj = self.get_item_by_path(obj_path)
                results.append((obj_path,
                                obj._dynamic_release()))

            return (results)
        except Exception as e:
            return ({'error': 'LitpItem.release: Exception caught'},
                    {'exception': str(e)})
    release.exposed = True

    def int_configure(self):
        """
        Internal method that recursively configures this item and its children.

        @rtype:  Serialised hierarchy string.
        @return: Either:
            - Landscape subtree after release of resources ?
            - Error information.

        """
        try:
            results = []
            all_configured = []

            while True:
                latest_paths = self._find()
                latest_paths.sort(key=lambda kid: self.get_item_by_path(kid).\
                                                    get_config_priority())

                if all_configured == []:
                    new_paths = latest_paths
                else:
                    new_paths = [x for x in latest_paths
                                 if x not in all_configured]

                if new_paths == []:
                    break

                for obj_path in new_paths:
                    obj = self.get_item_by_path(obj_path)
                    results.append((obj_path, obj._dynamic_configure()))

                    all_configured.append(obj_path)

            return results
        except Exception as e:
            return {'error': 'LitpItem.configure: Exception caught',
                    'exception': str(e)}

    def get_config_priority(self):
        ''' only used by LitpClusterConfig. USE WITH CAUTION '''
        return 0

    def has_more_config_priority(self, item):
        return self.get_config_priority() < item.get_config_priority()

    @background
    def configure(self, job):
        """
        Exposed background method that Recursively configures this item
        and its children.

        @rtype:  Serialised hierarchy string.
        @return: Either:
            - Landscape subtree after release of resources ?
            - Error information.

        """
        return self.int_configure()

    # FIXME: This function shouldn't exist, all feedbacks should be sent
    # to the feedback() method. Testing/Prototype propouse only
    @serialized
    def feedback_failure(self, message=None):
        """
        Prototype
        """
        try:
            #only exception to not having params in body
            if not message:
                body = eval(self.request_body())
                message = body["message"]
                message = urllib2.unquote(message)
            # TODO: The puppet report is not to sending
            # a proper json file yet, it should!!!!!!!!.
            logger.error("{0} returned a puppet feedback failure: {1}".\
                                        format(self.get_vpath(), message))

            status = self.get_status()
            if (status == 'Removing'):
                self.set_status('Unsuccessful', message)
                self.deletable = False
            elif status == 'Applying':
                self.set_status('Failed', message)
                self.deletable = False
            return {'success': 'LitpItem.feedback_failure: Feedback Recorded'}
        except Exception as e:
            return {'error':
                'LitpItem.feedback_failure: Failed to serialize object data',
                'exception': str(e)}
    feedback_failure.exposed = True

    @serialized
    def feedback(self):
        '''
        Record feedback from enforcement management software
        using external REST call

        @rtype: Serialised result string.
        @return: Details of get_stauts operation.
        '''
        try:
            status = self.get_status()
            # list of statuses where item ignores feedback
            ignoring_status_list = ['Applied', 'Verified',
                                    'Removed', 'Deconfigured']
            if status in ignoring_status_list:
                msg = 'LitpItem.feedback: ignoring feedback'
                logger.debug(msg)
                return {'skipped': msg}
            else:
                if status in ('Removing', 'Unsuccessful'):
                    self.set_status('Removed', "")
                    self.deletable = True
                else:
                    self.set_status('Applied',
                                    'Feedback received from Puppet')

                return {'success': 'LitpItem.feedback: Feedback Recorded'}
        except Exception as e:
            return {'error': 'LitpItem.dump: Failed to serialize object data',
                    'exception': str(e)}
    feedback.exposed = True

    # FIXME: Duplicated method ? feedback_failure() != fail() ?!?
    @serialized
    def fail(self):
        '''
        Record failure from enforcement management software
        using external REST call

        @rtype: Serialised result string.
        @return: Details of get_stauts operation.

        '''
        try:
            self.set_status('Failed', 'Feedback received from Puppet')
            return {'success': 'LitpItem.fail: Fail Recorded'}
        except Exception as e:
            return {'error': 'LitpItem.dump: Failed to serialize object data',
                    'exception': str(e)}
    fail.exposed = True

    def int_verify(self, phase="default", types="",
                   names="", params="", status="", flat=False):
        try:
            if flat == "True":
                results = self._verify()
            else:
                results = []
                all_ids = self._find()

                for obj_path in all_ids:
                    obj = self.get_item_by_path(obj_path)
                    results.append((obj_path,
                                    obj._dynamic_verify()))

            return results
        except Exception as e:
            return {'error': 'LitpItem.verify: Exception caught',
                    'exception': str(e)}

    @serialized
    @background
    def verify(self, job=None, phase="default", types="",
               names="", params="", status="", flat=False):
        """
        Exposed method recursively verifying this item and its children.
        @type  types: LITP Class.
        @param types: Note that by default we verify only
                      Roles and Resources.
        @rtype:  Serialised string.
        @return: Either:
                 - Landscape subtree after release of resources ?
                 - Error information.
        """
        return self.int_verify(phase, types, names, params, status, flat)
    verify.exposed = True

    @serialized
    @background
    def validate(self, job=None, phase="default",
                 types="core.litp_item.LitpItem",
                 names="", params="", status=""):
        """
        Exposed method recursively validating this item and its children.
        @type  types: LITP Class.
        @param types: Note that by default we validate only
                      Roles and Resources.
        @rtype:  Serialised string.
        @return: Either:
                - Landscape subtree after release of resources ?
                - Error information.
        """

        try:
            self._check_json_export()
            return self._perform_validation(phase, types, names, params,
                                            status)
        except Exception as e:
            logger.exception("LitpItem.validate: Exception caught")
            return {'error': 'LitpItem.validate: Exception caught',
                    'exception': str(e)}
    validate.exposed = True

    def _perform_validation(self, phase="default",
                            types="core.litp_item.LitpItem",
                            names="", params="", status=""):
        try:
            results = []
            all_ids = self._find(phase, types, names, status)

            for obj_path in all_ids:
                obj = self.get_item_by_path(obj_path)
                results.append((obj_path, obj._dynamic_validate()))

            return results
        except Exception as e:
            logger.exception("LitpItem._perform_validation: Exception caught")
            return {'error': 'LitpItem.validate: Exception caught',
                    'exception': str(e)}

    @serialized
    def deconfigure(self, phase="default", types="",
                    names="", params="", status="", undo="False"):
        """
        Set the item to be deconfigured.
        """

        try:
            if self.siblings_require_me():
                return {'error': 'Cannot deconfigure - this item is required'
                                 ' by %s' % (self.siblings_require_me_ids(),)}
            if undo and undo == "True":
                if self.get_status() != "Deconfigured":
                    return {'error': 'LitpItem.deconfigure: Object is ' +
                                     'not in the \'Deconfigured\' state'}
                results = []
                all_ids = self._find(phase, types, names, status)

                for obj_path in all_ids:
                    obj = self.get_item_by_path(obj_path)
                    results.append((obj_path,
                                    obj._dynamic_configure()))
                path = self.get_vpath()
                res = [item for item in results if item[0] == path]

                if 'success' in res[0][1].keys():
                    msg = ('LitpItem.deconfigure: Successfully Undo.'
                           ' Item moved to the previous status')
                    pstatus = self.get_last_status_change(
                                                    'Deconfigured')
                    self.set_status(pstatus['old'], msg)
            else:
                logger.info("LitpItem.deconfigure: Deconfiguring "
                            "object %s" % self.get_vpath())
                results = []
                all_ids = self._find(phase, types, names, status)

                for obj_path in all_ids:
                    obj = self.get_item_by_path(obj_path)
                    results.append((obj_path,
                                    obj._dynamic_configure("deconfigure")))

            return results
        except Exception as e:
            logger.error('LitpItem.deconfigure: Exception caught:\n' + str(e))
            return {'error': 'LitpItem.deconfigure: Exception caught',
                    'exception': str(e)}
    deconfigure.exposed = True

    def to_be_removed(self):
        return self.status in ['Deconfigured', 'Deconfiguring']

    @serialized
    def compare(self, *args, **kwargs):
        """
        Comparing contents of the two objects reporting any discrepancies on
        either side.
        @todo: Read only compare contents of the object.
        Report any LitpItems:
            - "missing" items, i.e. in Definition, but not in Object
            - "extra" items, i.e. not in Definition, but found in Object
            - "different" items, i.e. properties in Definition / RoleReferences
             != respective Object.properties
            - Note: it is to be expected that there will be extra properties,
            but those that were defined should match

        @rtype:  Serialised string
        @return: List of object that were added, deleted and updated
        """
        try:
            comparedObject = kwargs['obj']
            comparedObject = comparedObject.strip('"')
            result = self.dynamic_compare(comparedObject)
            if 'success' in result:
                added, deleted, updated, errors = result['success']
                result = {'success': 'LitpItem.compare: comparison completed'}
                result['added'] = added
                result['deleted'] = deleted
                result['updated'] = updated
            return result
        except Exception as e:
            logger.exception('LitpItem.compare: Exception caught')
            return {'error': 'LitpItem.compare: Exception caught',
                    'exception': str(e)}
    compare.exposed = True

    def _compare_properties(self, comparedObject):
        """
        Compare the properties between two objects.

        @type  comparedObject: object
        @param comparedObject: object whose properties are compared with

        @rtype:  Boolean.
        @return: Either True (no differences) or False (differences):
        """
        errs = []
        try:
            no_diff = True
            diff_props = set(self.properties.keys()).symmetric_difference(
                                            comparedObject.properties.keys())
            if diff_props:
                if self.props_are_ok(diff_props):
                    no_diff = False
            common_props = set(self.properties.keys()).intersection(
                                        comparedObject.properties.keys())
            for prop in common_props:
                if self.properties[prop] != comparedObject.properties[prop]:
                    try:
                        if self.prop_is_ok(prop):
                            no_diff = False
                    except NotUpgradablePropertyException as e:
                        errs.append(e.code)
            if errs:
                raise NotUpgradablePropertyException(errs)
            return no_diff
        except Exception as e:
            logger.exception('LitpItem._compare_properties: Exception caught '
                             + str(e))
            raise

    def props_are_ok(self, diff_props):
        '''
        returns True if all the diff_props are allowed in the upgrade. If not,
        gathers all the errors and raises and exception with them
        '''
        errs = []
        for prop in diff_props:
            try:
                self.prop_is_ok(prop)
            except NotUpgradablePropertyException:
                msg = 'Cannot update property {0} for item {1} as it is not ' \
                      'supported for upgrade'.format(prop, self.get_vpath())
                errs.append(msg)
        if errs:
            raise NotUpgradablePropertyException(errs)
        return True

    def prop_is_ok(self, prop):
        '''
        Campaign generation/execution related. To be overridden by
        LitpItems that support only some properties to be upgraded.
        '''
        # in the general case, upgrades are not supported if we're inside a sg
        if self.is_in_sg() or self.__class__.__name__ == 'LitpServiceGroup':
            # property updated and we're inside a SG. NOT SUPPORTED!
            msg = 'Cannot update property {0} for item {1} as it is not ' \
                  'supported for upgrade'.format(prop, self.get_vpath())
            logger.error(msg)
            raise NotUpgradablePropertyException(msg)
        return True

    def prop_is_ok_specific(self, prop, supported):
        '''
        LitpItems that need to override prop_is_ok will call this function
        with their specific list of supported properties
        '''
        if not self.is_in_sg():
            #if we are out of a SG then everything's ok
            return True
        if not prop in supported:
            msg = 'Cannot update property {0} for item {1} as it is not ' \
                  'supported for upgrade'.format(prop, self.get_vpath())
            logger.error(msg)
            raise NotUpgradablePropertyException(msg)
        return True

    def obj_is_ok(self):
        # in the general case, upgrades are not supported if we're inside a sg
        if self.is_in_sg() or self.__class__.__name__ == 'LitpServiceGroup':
            # property updated and we're inside a SG. NOT SUPPORTED!
            msg = 'Cannot update item {0} as it is not ' \
                  'supported for upgrade'.format(self.get_vpath())
            logger.error(msg)
            raise NotUpgradableObjectException(msg)
        return True

    def _compare_configurations(self, comparedObj):
        """
        Compare the configurations between two objects.

        @type  comparedObj: object
        @param comparedObj: object whose configuration are compared with

        @rtype:  Boolean.
        @return: Either True (no differences) or False (differences):
        """
        try:
            if not (self.is_configurable() or comparedObj.is_configurable()):
                # aside of puppet, we don't care about its configuration
                logger.info("Not configurable item, skipping compare_"
                            "configurations: {0}".format(self.get_vpath()))
                return True
            if len(self.configuration) != len(comparedObj.configuration):
                return False

            comp = comparedObj.configuration
            for index, item in enumerate(self.configuration):
                cmp_item = comp[index]
                if isinstance(item, list):

                    for sub_index, sub_item in enumerate(item):
                        cmp_sub_item = cmp_item[sub_index]
                        for key in sub_item.keys():
                            if key not in cmp_sub_item.keys():
                                return False
                            elif sub_item[key] != cmp_sub_item[key]:
                                return False
                        for key in cmp_sub_item.keys():
                            if key not in sub_item.keys():
                                return False

                elif isinstance(item, dict):

                    for key in cmp_item.keys():
                        if key not in cmp_item.keys():
                            return False
                        elif item[key] != cmp_item[key]:
                            return False
                    for key in cmp_item.keys():
                        if key not in cmp_item.keys():
                            return False
            return True
        except Exception as e:
            logger.exception('LitpItem._compare_configs: Exception ' + str(e))
            raise

    def dynamic_compare(self, comparedObj):
        """
        Compare the properties and configurations between two objects.

        @type  comparedObj: str
        @param comparedObj: path to the object whose properties are compared

        @rtype:  3 lists.
        @return: 3 lists containing paths to
                1. added    objects
                2. deleted  objects
                3. modified objects
        """
        added_objs = []
        deleted_objs = []
        updated_objs = []
        # error regarding properties (i.e: properties allowed in campaigns)
        error_props = []

        try:
            comp_obj = self.get_item_by_path(comparedObj)

            if comp_obj is None:
                raise Exception('error: LitpItem.compare: '
                                'comparedObject is None!')
            else:

                children_id = self.get_item_ids()

                comp_children_id = comp_obj.get_item_ids()

                path = self.get_vpath()
                cmp_path = comp_obj.get_vpath()

                diff_children = set(children_id).symmetric_difference(
                                                            comp_children_id)

                for diff_child in diff_children:
                    if diff_child in children_id:
                        child_path = path + '/' + diff_child
                        child_obj = self.get_item_by_path(child_path)
                        added_children = child_obj.get_all_child_item_ids()
                        added_children.sort()
                        for ch_path in added_children:
                            try:
                                ch_obj = self.get_item_by_path(ch_path)
                                if ch_obj.obj_is_ok():
                                    added_objs.append(ch_path)
                            except NotUpgradableObjectException as e:
                                # the added object was in a service group
                                error_props.append(e.code)
                    else:
                        child_path = cmp_path + '/' + diff_child
                        child_obj = self.get_item_by_path(child_path)
                        del_children = child_obj.get_all_child_item_ids()
                        del_children.sort()
                        for ch_path in del_children:
                            try:
                                ch_obj = self.get_item_by_path(ch_path)
                                if ch_obj.obj_is_ok():
                                    deleted_objs.append(ch_path)
                            except NotUpgradableObjectException as e:
                                # the added object was in a service group
                                error_props.append(e.code)

                common_ids = set(children_id).intersection(comp_children_id)

                for child_id in common_ids:
                    child_path = path + '/' + child_id
                    child_obj = self.item_by_path(child_path)

                    cmp_child_path = cmp_path + '/' + child_id
                    result = child_obj.dynamic_compare(cmp_child_path)
                    if 'success' in result:
                        added, deleted, updated, errors = result['success']
                    else:
                        return result

                    added_objs.extend(added)
                    deleted_objs.extend(deleted)
                    updated_objs.extend(updated)
                    error_props.extend(errors)

                if ((self._compare_properties(comp_obj) is False)
                or (self._compare_configurations(comp_obj) is False)):
                    updated_objs.append(path)

            return {'success': [added_objs, deleted_objs,
                                updated_objs, error_props]}
        except (NotUpgradablePropertyException,
                ConditionalUpgradablePropertyException) as e:
            if type(e.code) == str:
                error_props.append(e.code)
            else:
                error_props.extend(e.code)
            # return success because the error will be handled in the method
            # that calls this other method.
            return {'success': [[], [], [], error_props]}
        except Exception as e:
            logger.exception('LitpItem.dynamic_compare: Exception caught '
                             + str(e))
            raise

    def _last_history_is(self, newstatus, message):
        """
        Returns history['new'] and message == history['message'] ??

        @type  newstatus: LITP object status string.
        @param newstatus: New Status, allowed values:
                          "Initial", "Available", "Allocated", "Configured",
                          "Applying", "Verified", "Failed"

        @type  message: String
        @param message: Information message to explain reason for status change

        @rtype:  Boolean
        @return: history['new'] and message == history['message']

        """
        if not self.status_history:
            return False
        history = self.status_history[-1]
        return newstatus == history['new'] and message == history['message']

    def set_status(self, newstatus, message):
        """
        Set Status of this item
        @type  newstatus: LITP object status string.
        @param newstatus: New Status, allowed values:
                          "Initial", "Available", "Allocated", "Configured",
                          "Applying", "Verified", "Failed"
        @type  message: String
        @param message: Information message to explain reason for status change
        @return: True when Status transition is allowed, False otherwise
        @rtype:  Boolean
        """
        regex = re.compile('(Initial)|(Available)|(Allocated)|(Configured)|'
                    '(Applying)|(Applied)|(Verified)|(Failed)|'
                    '(Deconfigured)|(Removing)|(Removed)|(Unsuccessful)')
        if not regex.match(newstatus):
            logger.error("LitpItem.set_status(%s) on %s failed "
                         "as new status is not supported",
                         newstatus, self.get_vpath())
            return False
        else:
            last_status = self.get_last_status_change()
            if last_status and \
               self.status == newstatus and \
               last_status['message'] == message:
                # TODO: Maybe we should update the date
                # of the last status
                return True

            history = dict(date=datetime.datetime.now().isoformat(' '),
                           new=newstatus, old=self.status, message=message)

            if self.is_in_inventory():
                if newstatus in ("Applying", "Applied", "Verified",
                                 "Deconfigured", "Removing", "Failed"):
                    self.deletable = False
                elif newstatus == "Allocated":
                    # Tricky
                    # Allocated can't set the deletable flag because
                    # the first time an item is allocated it can be deleted,
                    # but after an apply() it can't be deleted anymore, even
                    # if the status is set back to Allocated.(You can do that
                    # changing the value of a property for example)
                    pass
                else:
                    self.deletable = True

            self.status = newstatus
            self._add_to_status_history(history)
            logger.info("LitpItem.set_status(%s) on %s changed items status",
                        newstatus, self.get_vpath())
            return True

    def _add_to_status_history(self, element):
        self.status_history.append(element)
        self.status_history = self.status_history[-10:]

    def get_status(self):
        """
        Get current LITP object status value.

        @rtype:  LITP object status string.
        @return: The current status.
        """
        return self.status

    def get_last_status_change(self, status=""):
        """
        Get last status change info for the LITP object.

        @type status: LITP object status string.
        @param status: status, allowed values:
                          "Initial", "Available", "Allocated", "Configured",
                          "Applying", "Verified", "Failed"

        @rtype: ?
        @return: Status change info for last status change to status passed as
        status ?
        # Status change element same as in get_status_history()
        Example:
          - self.get_last_status_change('Verified') returns last Verify change
          - self.get_last_status_change() returns last status change info
        """
        last_status = None
        if self.status_history:
            if status:
                for h in reversed(self.status_history):
                    if h['new'] == status:
                        last_status = copy.deepcopy(h)
                        break
            else:
                last_status = copy.deepcopy(self.status_history[-1])
        return last_status

    def get_status_history(self):
        """
        Get an array containing history of status changes

        @rtype:  Array of Dict
        @return: Each array element contains a dictionary the with following
        fields:
                - 'date': string_containint_status_change_date_stamp,
                - 'new': string_with_new_status_value,
                - 'old': string_with_old_status_value,
                - 'message': string_with_status_message
        """
        return self.status_history

    def _is_litp_item(self, obj):
        """
        Determines whether the object passed as "obj" is a LITP
        Item object/resource.

        @type  obj: a Python object.
        @param obj: the object to test whether it's a LITP object.

        @rtype:    Boolean
        @return:   True if "obj" is a LITP Item object, False otherwise.

        """
        return issubclass(type(obj), LitpItem)

    def _show(self, mode='', attr_list=[]):
        """
        Show a list of attributes of the current LITP object.

        @type  mode:  String literal. .
        @param mode: 'd', 'l', 'v', 'vv', or 'vvv', 'help'

        @type  attr_list: List of String.
        @param attr_list: the set,if any, of specific attributes to show.

        @rtype:  Dictionary
        @return: Details of the requried object attributes.

        """

        response = {}
        read_attrs = ['id', 'status', 'properties', 'checked_status']

        if mode == 'd':
            response = dict([(key, value) for (key, value) in
                self.__dict__.items() if not self._is_litp_item(value)])
            response['class'] = self.__class__.__name__
        else:
            if attr_list:
                if mode in ('v', 'vv', 'vvv'):
                    error_dict = {'error': 'Positional argument incompatible' \
                                               ' with {0} option'.format(mode)}
                    return dict(zip(attr_list, [error_dict] * len(attr_list)))
                read_attrs = attr_list

            if mode == 'v':
                read_attrs = ['id', 'status', 'properties', 'configuration',
                              'checked_status']
            elif (mode == 'vv'):
                read_attrs = ['id', 'status', 'properties', 'configuration',
                              'status_history', 'checked_status']
            elif (mode == 'vvv'):
                read_attrs = self._get_show_vvv_attr()
            elif mode == 'l':
                read_attrs = []

            checked_status = 'Warning'
            if self.get_status() == self._get_last_state():
                checked_status = 'Ok'
            elif self.get_status() == 'Failed':
                checked_status = 'Failed'
            elif self.get_status() == 'Applied':
                checked_status = 'Ok'
            elif self.get_status() == 'Verified':
                checked_status = 'Ok'
            elif self.get_prop('external') == 'True':
                checked_status = 'Ok'
                self.set_status('Applied', 'External service')
            elif self.__class__.__name__ == "LitpRoot":
                checked_status = 'Ok'
            else:
                checked_status = 'Warning'

            for attrname in read_attrs:
                attr = getattr(self, attrname, None)
                if attr is not None:
                    response[attrname] = attr
                elif attrname == "class":
                    response[attrname] = self.__class__.__name__
                elif attrname == "checked_status":
                    response[attrname] = checked_status
                else:
                    if attrname in self.__dict__.keys():
                        response[attrname] = 'None'
                    else:
                        response[attrname] = {'error': 'requested attribute '
                                              'not supported by this class'}

            if mode == 'help':
                response['all_properties'] = self.properties
                response['allowed_methods'] = self.allowed_methods()
                response['allowed_properties'] = self.allowed_properties()

        return response

    def is_in_inventory(self):
        """
        Determines if current object is under /inventory subtree or not.
        @rtype:    Boolean
        @return:   True if it has an ancestor of type LitpInventory and
            id Inventory.
        """
        parent = self._lookup_parents("", "core.litp_inventory.LitpInventory",
                                      "", "", {})
        if parent:
            return True
        else:
            return False

    def has_been_applying(self):
        """
        Determines if status of current object is 'Applying', 'Applied or
        'Verified'.

        @rtype:    Boolean
        @return:   True if object status is 'Applying', 'Applied' or
        'Verified'.

        """
        return self.get_status() in ['Removing', 'Removed',
                                     'Applying', 'Applied', 'Verified']

    def from_inventory_to_definition_path(self):
        """
        @summary: find the path for the item that needs to be materialised
                  from this definition

        @rtype: A Landscape URI path strinig.
        @return: The definition path
        """
        pathArray = self.get_vpath_array()
        pathArray.pop(0)  # pop of inventory from the array

        pathArray.insert(0, "definition")

        path = ''

        for subpath in pathArray:
            path = path + '/' + subpath

        return path

    def plan_check_children(self):
        """
        Update own status depending on children status
        """
        children = self.get_children()

        for child in children:
            if child.status == 'Failed':
                return {'error': 'LitpItem.plan_check_children child task ' +
                                 child.id + " failed"}

        return {'success': 'LitpItem.plan_check_children successful'}

    def shallow_copy(self, dest):
        """
        @summary: copy an object to another, but not its children
        (nor its parent attribute, obviously)

        @type  dest:  Sting containing uri.
        @param dest: path where to create copy of self.

        @rtype: Dict
        @return: Dictionary describing a shallow_copy step
        """
        try:
            if not dest:
                msg = ('LitpItem.shallow_copy: destination path '
                       'not specified')
                logger.error(msg)
                return {'error': msg}
            else:
                dest_obj = self.item_by_path(dest)
                if not dest_obj:
                    msg = ('LitpItem.shallow_copy: destination object '
                           'doesn\'t exist')
                    logger.error(msg)
                    return {'error': msg}

                #get all attributes from dest
                dest_children = dir(dest_obj)
                dest_children = filter(lambda c: c[0] != "_" and \
                    c != "parent" and c != "children", dest_children)
                dest_children = filter(lambda c: not isinstance(getattr(self,
                                                    c, None),
                                                    LitpItem), dest_children)
                dest_children = filter(lambda c: not callable(getattr(self,
                                                    c, None)), dest_children)
                #get all atributes to be copied
                self_children = dir(self)
                self_children = filter(lambda c: c[0] != "_" and \
                    c != "parent" and c != "children", self_children)
                self_children = filter(lambda c: not isinstance(getattr(self,
                                                    c, None),
                                                    LitpItem), self_children)

                self_children = filter(lambda c: not callable(getattr(self,
                                                    c, None)), self_children)
                #remove attributes not in self
                for child in dest_children:
                    if child not in self_children:
                        delattr(dest_obj, child)
                #copy all attributes from self
                for child in self_children:
                    setattr(dest_obj, child, getattr(self, child))
                #copy properties
                dest_obj.properties = {}
                for prop, value in self.properties.items():
                    dest_obj.properties[prop] = value

            return {'success': 'LitpItem.shallow_copy: copy completed'}
        except Exception as e:
            msg = 'LitpItem.shallow_copy: exception caught'
            logger.exception(msg)
            return {'error': msg, 'exception': str(e)}

    def create_shallow_copy(self, dest_path):
        """
        @summary: copy an object to another, but not its children
        (nor its parent attribute, obviously)

        @type  dest_path:  Sting containing uri.
        @param dest_path: path where to create copy of self.

        @rtype: Dict
        @return: Dictionary describing a shallow_copy step

        """
        try:
            parent_inv_path_list = dest_path.rsplit('/', 1)
            parent_inv_path = parent_inv_path_list.pop(0)
            copy_id = parent_inv_path_list.pop(0)

            orig_parent = self.parent
            self.parent = None
            copy_obj = copy.deepcopy(self)
            self.parent = orig_parent
            parent_inv_obj = self.get_item_by_path(parent_inv_path)

            parent_inv_obj.add_child(copy_id, copy_obj)
            copy_obj.parent = parent_inv_obj
            #for prop, value in self.properties.items():
            #    dest.properties[prop] = value
            copy_children = copy_obj.get_children()
            for child in copy_children:
                copy_obj.remove_child(child.id)
            return {'success': 'LitpItem.create_shallow_copy: copy completed'}
        except Exception as e:
            msg = 'LitpItem.create_shallow_copy: exception caught'
            logger.exception(msg)
            return {'error': msg, 'exception': str(e)}

    def upgrade_to_inventory_path(self):
        """
        @summary: If self is under an upgrade branch, this method returns
        the "equivalent" path under inventory or its vpath if it's in the
        inventory already

        @rtype: String containing URL
        @return: Path to the equivalent object under inventory, or Empty string
            if the object is not in an upgrade branch
        """
        path = ""
        upgrade_obj = self._lookup_parents("",
                                       "core.litp_upgrade.LitpUpgrade")
        if upgrade_obj:
            new_obj = self._lookup_parents("",
                                           "core.litp_inventory.LitpInventory")
            if new_obj is None and self.id == 'new':
                new_obj = self
            new_path_array = new_obj.get_vpath_array()
            item_path_array = self.get_vpath_array()

            while new_path_array:
                new_path_array.pop(0)
                item_path_array.pop(0)

            item_path_array.insert(0, "inventory")
            path = path + "/" + "/".join(item_path_array)
        if not path:
            path = self.get_vpath()
        return path

    def upgrade_to_inventory_obj(self):
        if self.get_item_by_path(self.upgrade_to_inventory_path()):
            return self.get_item_by_path(self.upgrade_to_inventory_path())
        return self

    def _version(self, style=None, attr=None):
        """
        Show a list of attributes of the current LITP object.

        @type  style:  String literal.
        @param style: Output mode, eg screen (default) xml, txt, html

        @type  attr: List
        @param attr: 'iso', 'package', 'etc'.

        @rtype:  Dictionary
        @return: Details of the requried object attributes.

        """
        if attr is None:
            return []

        response = []
        exec_on_nodes = ['all', 'litp', 'package',
                         'campaign', 'solution', 'iso']

        nodecmds = [cmd for cmd in attr if cmd in exec_on_nodes]
        nodecmds.insert(0, style)

        if nodecmds:
            all_ids = self.get_all_child_item_ids()

            for obj_path in all_ids:
                obj = self.get_item_by_path(obj_path)
                if obj.get_prop("nodetype") == "sfs":
                    # Ignore sfs node
                    continue
                elif obj._check_condition("", "core.litp_node.LitpNode",
                                          "", ""):
                    response.append((obj_path, obj.query_version(nodecmds)))

        # landscape tree not set up, but one of all/iso/litp selected
        if bool(set(("all", "iso")) & set(attr)):
            iso = PkgInfo().global_versions()
            if iso == '':
                iso = 'Cannot find litp .version file'
            response.append(["Local machine", {"iso": iso}])
        if not response and "iso" not in attr:
            response.append({"error": "Cannot find nodes in landscape tree"})

        return response

    @serialized
    def version(self, *args, **kwargs):
        """
        REST GET handler method
        Method provides access to serialised content of requested instance.
        Invoked by REST PUT method.

        @rtype: A serialised result String.
        @return: Object Content (or error) details.

        """
        try:
            #info = self._request_dict()
            allowed_attr = ['all', 'litp', 'package', 'iso', 'campaign',
                            'solution']
            #later jboss, java,

            #Default output style defined here
            style = kwargs.get('style', 'j')
            if 'attributes' in kwargs.keys():
                for attr in ast.literal_eval(kwargs['attributes']):
                    if attr not in allowed_attr:
                        err = "Attribute %s not recognised try --help" % attr
                        return {'error': err}

                response = self._version(style,
                            ast.literal_eval(kwargs['attributes']))
            else:
                #Default command defined here
                response = self._version(style, ['iso'])
            return response
        except Exception as e:
            logger.exception("Exception in version")
            result = {'error': 'litp_version: Failed to ' +
                               'serialize the response',
                               'exception': str(e)}
            return result
    version.exposed = True

    def get_all_child_item_ids(self, phase="default",
                               types="core.litp_item.LitpItem", names="",
                               status="", properties={}):
        child_ids = []
        children = self.get_children()

        for child in children:
            child_ids.extend(child.get_all_child_item_ids(phase, types,
                                                          names, status,
                                                          properties))
        if self._check_condition(phase, types, names, status, properties):
            child_ids.append(self.get_vpath())

        return child_ids

    def _list_dependencies(self):
        """
        overridable method that checks whether the requires properties are
        satisfied in the list passed as argument

        @rtype:  list of URIs
        @return: list of objects on which self depends
        """
        return []

    def all_children_by_dependency(self):
        """
        overridable method that checks ordered list of all children
        according to some dependency rule

        @rtype:  list of URIs
        @return: list of objects ordered by dependency
        """
        item_ids = self.get_all_child_item_ids()

        candidates = dict([(vpath,
            set(self.item_by_path(vpath)._list_dependencies()))
            for vpath in item_ids])

        sorted_candidates = topsort2(candidates)
        sorted_candidates = [item.split(' ') for item in sorted_candidates]
        sorted_candidates = list(itertools.chain(*sorted_candidates))

        return sorted_candidates

    def immediate_children_by_dependency(self):
        """
        overridable method that checks ordered list of all children
        according to some dependency rule

        @rtype:  list of URIs
        @return: list of objects ordered by dependency
        """
        item_ids = self.get_children_paths()

        candidates = dict([(vpath,
            set(self.item_by_path(vpath)._list_dependencies()))
            for vpath in item_ids])

        sorted_candidates = topsort2(candidates)
        sorted_candidates = [item.split(' ') for item in sorted_candidates]
        sorted_candidates = list(itertools.chain(*sorted_candidates))

        return sorted_candidates

    def _get_last_state(self):
        """
        overridable method that returns the ultimate state for objects
        of this class

        @rtype:  string
        @return: status where objects from this class will be at ehe end
        of their lifecycle
        """
        return "Verified"

    def _get_show_vvv_attr(self):
        return ['id', 'status', 'properties', 'configuration',
                'status_history', 'deletable', 'checked_status']

    def get_closest_ancestor(self):
        '''
        returns the first element of type node, cluster, site or inventory,
        in that order. If any of them exists returns none
        '''
        priority_list = ['core.litp_node.LitpNode',
                         'core.litp_cluster.LitpCluster',
                         'core.litp_site.LitpSite',
                         'core.litp_inventory.LitpInventory']
        for item in priority_list:
            found_obj = self._lookup_parents('', item)
            if found_obj:
                return found_obj
        return None

    def _siblings(self):
        if self.parent:
            return [item for item in self.parent.get_children() if
                    item != self]
        else:
            return []

    def siblings_require_me(self):
        siblings = self._siblings()
        siblings = [item for item in siblings if self.id in
                    item.get_dependencies()]
        return siblings

    def siblings_require_me_ids(self):
        return [item.id for item in self.siblings_require_me()]

    def get_module_class_name(self):
        return '.'.join([self.__class__.__module__, self.__class__.__name__])

    def is_in_sg(self):
        # returns the sg path if item is a child of a service group
        if self._check_condition("",
                        "core.litp_service_group.LitpServiceGroup", "", ""):
            return self.get_vpath()
        kwargs = {'types': 'core.litp_service_group.LitpServiceGroup'}
        sg = self._lookup_parents(**kwargs)
        if sg:
            return sg.get_vpath()
        return ''

    def _find_all_errors(self, response):
        if type(response) is dict:
            if set(response.keys()).intersection(set(('error', 'exception'))):
                return response
            errors = [self._find_all_errors(i) for i in response.values()]
            errors = [err for err in errors if err]
            if errors:
                return errors
        elif type(response) in (list, tuple):
            errors = [self._find_all_errors(item) for item in response]
            errors = [err for err in errors if err]
            if errors:
                return errors
        return []

    def success(self, response, log=True):
        if response and type(response) == str and log:
            logger.debug(response)
        return {'success': response}

    def is_success(self, response):
        return 'success' in response

    def error(self, response, log=True):
        if response and type(response) == str and log:
            logger.error(response)
        return {'error': response}

    def exception(self, response):
        logger.exception(response)
        return {'exception': response}

    def update_pkgs_in_tree(self, pkg_list, force=False):
        lookup_types = ["litputil.package.Package",
                        "litputil.package_def.LitpPackageDef",
                        "litputil.package_def.LitpPackageDef",
                        "litputil.package.Package"]
        lookup_roots = ["/inventory", "/definition", "/depmgr", "/depmgr"]
        for lookup_type, lookup_root in zip(lookup_types, lookup_roots):
            self._update_pkgs(lookup_type, lookup_root, pkg_list, force)

    def _update_pkgs(self, lookup_type, lookup_root, pkgs, force):
        pkg_paths = self._lookup("", lookup_type, "", "", {}, lookup_root)
        tree_pkgs = [self.get_item_by_path(pkg_obj) for pkg_obj in pkg_paths]
        for pkg_obj, pkg_match in self._get_matching_packages(pkgs, tree_pkgs):
            pkg_obj.update_pkg_props(pkg_match, force)
            logger.info('updated pkg {0}'.format(pkg_match))

    def _get_matching_packages(self, pkg_list, tree_pkgs):
        ''' returns a generator with the Package objs that match the elements
            in the package list and the dictionary it should be updated to
            @param pkg_list package list. Each element will be a dictionary
            containing up to 4 properties (name, arch, version, release)
        '''
        for pkg_obj in tree_pkgs:
            match = pkg_obj.matches('name', pkg_list)
            if match:
                logger.info("found match: {0}".format(pkg_obj.get_vpath()))
                yield pkg_obj, match

    def get_node_from_hostname(self, hostname):
        ''' returns the node obj that matches the hostname,
            None if there is no match '''
        for node in self._nodes():
            if node.get_hostname() == hostname:
                return node
        return None

    def get_node_from_id(self, id):
        for node in self._nodes():
            if node.id == id:
                return node
        return None

    def _nodes(self):
        """ @summary: Return a list of node objs """
        args = ("", "core.litp_node.LitpNode", "", "", {}, "/inventory")
        nodes = self._lookup(*args)
        return [self.get_item_by_path(node) for node in nodes]

    @serialized
    def cli_get_prop(self, name):
        return {name: self.get_prop(name)}
    cli_get_prop.exposed = True
