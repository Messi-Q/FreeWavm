"""Defines a simple, generic data (de)serialization mechanism."""
from __future__ import print_function, absolute_import, division, unicode_literals

from .compat import add_metaclass, byte2int, indent, deprecated_func
import collections
import logging
import struct as pystruct
import copy
import traceback

logger = logging.getLogger()

#'name':cur_field_name,'type':field_type,'data':field_val,'parent':pnode
class Node(object):
    def __init__(self,_name,_type,_data,_parent):
        self.name = _name
        self.type = _type
        self.data = _data
        self.parent = _parent
        
    def fix_node_data_length(self,fix_length):
        node = self
        while True:
            cur_field_name = node.name
            parent_node = node.parent
            if parent_node == None:     # no need fix,fix all fields
                break
            if type(parent_node.data) == list: #not data object pass
                pass
            else:
                parent_node.data._decoder_meta['lengths'][cur_field_name] += fix_length
            node = node.parent

    def fix(self):
        node = self
        while True:
            if node == None:
                break
            if isinstance(node.data, StructureData):
                node.data._meta.structure().fix(node.data)
            node = node.parent
        
class WasmField(object):
    """
    Abstract base class for all fields.

    Fields are purely a (de)serialization mechanism. They don't hold the value
    of decoded information, but take Python data-types and convert them
    to a raw byte format or vice versa. Thus, a field instance can be reused
    to de/encode multiple values.

    Besides the abstract interface, implements type counting and IDing to allow
    field order detection in Python 2, where `__prepare__` doesn't exist yet.
    In order to work correctly, field instances MUST NOT be shared between
    multiple structures using it but have to be instantiated per structure.
    """
    _type_ctr = 0

    def __init__(self):
        self._type_id = WasmField._type_ctr
        WasmField._type_ctr += 1
   
    def from_raw(self, struct, raw):
        raise NotImplementedError()

    def to_string(self, value):
        return repr(value)
    
    def rebuild(self,value):
        raise NotImplementedError()
    
    def fix(self,data):
        pass

class UIntNField(WasmField):
    """Field handling an unsigned LE int of fixed size."""
    CONVERTER_MAP = {
        8: pystruct.Struct('<B'),
        16: pystruct.Struct('<H'),
        32: pystruct.Struct('<I'),
        64: pystruct.Struct('<Q'),
    }

    def __init__(self, n, **kwargs):
        super(UIntNField, self).__init__(**kwargs)
        self.n = n
        self.byte_size = n // 8
        self.converter = self.CONVERTER_MAP[n]

    def from_raw(self, ctx, raw):
        return self.byte_size, self.converter.unpack(raw[:self.byte_size])[0], self

    def to_string(self, value):
        return hex(byte2int(value) if self.n == 8 else value)
    
    def rebuild(self,value):
        return self.converter.pack(value)


class UnsignedLeb128Field(WasmField):
    """
    Field handling unsigned LEB128 values.
    https://en.wikipedia.org/wiki/LEB128
    """
    def from_raw(self, ctx, raw):
        offs = 0
        val = 0

        while True:
            segment = byte2int(raw[offs])
            val |= (segment & 0x7F) << (offs * 7)
            offs += 1
            if not (segment & 0x80):
                break

        return offs, val, self

    def to_string(self, value):
        return hex(value) if value > 1000 else str(value)
    
    def rebuild(self,value):
        #print(value)   
        bytes = b""
        while True:
            if value < 0:      
                value = -value
            byte = value &0x7f
            value >>= 7
            if value !=0:
                byte |=0x80
            bytes+= pystruct.Struct('<B').pack(byte)
            if value ==0:
                break
        return bytes

class SignedLeb128Field(WasmField):
    """
    Field handling signed LEB128 values.
    https://en.wikipedia.org/wiki/LEB128
    """
    def from_raw(self, ctx, raw):
        offs = 0
        val = 0
        bits = 0

        while True:
            segment = byte2int(raw[offs])
            val |= (segment & 0x7F) << bits
            offs += 1
            bits += 7
            if not (segment & 0x80):
                break

        if val & (1 << (bits - 1)):
            val -= 1 << bits

        return offs, val, self
    
    def rebuild(self,value):
        bytes = b''
        more = True
        while more:
            byte = value & 0x7f
            value >>= 7
            if (value == 0 and (byte & 0x40) == 0) or (value == -1 and (byte & 0x40) != 0):
                more = False
            else:
                byte |= 0x80
            bytes+= pystruct.Struct('<B').pack(byte)
        return bytes
    
  

class CondField(WasmField):
    """Optionalizes a field, depending on the context."""
    def __init__(self, field, condition, **kwargs):
        super(CondField, self).__init__(**kwargs)
        self.field = field
        self.condition = condition

    def from_raw(self, ctx, raw):
        #print(ctx._meta.fields)
        if self.condition(ctx):
            return self.field.from_raw(ctx, raw)
        return 0, None, self

    def to_string(self, value):
        #print("[+]",value)
        return 'None' if value is None else self.field.to_string(value)
    
    def rebuild(self,value):
        if value == None:
            return b''
        else:
            raise NotImplementedError("todo")
        

class RepeatField(WasmField):
    """Repeats a field, having the repeat count depend on the context."""
    def __init__(self, field, repeat_count_getter, **kwargs):#this is new only once
        super(RepeatField, self).__init__(**kwargs)
        self.field = field
        self.repeat_count_getter = repeat_count_getter

    def from_raw(self, ctx, raw):
        repeat_count = self.repeat_count_getter(ctx)

        # Avoiding complex processing for byte arrays.
        if type(self.field) == UIntNField and self.field.n == 8:
            return repeat_count, raw[:repeat_count], self

        # For more complex types, invoke the field for parsing the
        # individual fields.
        offs = 0
        items = []
        for i in range(repeat_count):
            length, item, element_type = self.field.from_raw(ctx, raw[offs:])
            offs += length
            items.append(item)
        return offs, items, self

    def to_string(self, value):
        if value is None:
            return 'None'
        if len(value) > 100:
            return '<too long>'
        if len(value) == 0:
            return '[]'
        if isinstance(value[0], StructureData):
            return '\n' + indent(
                '\n'.join(self.field.to_string(x) for x in value),
                '  '
            )
        else:
            return '[' + ', '.join(self.field.to_string(x) for x in value) + ']'
        
    def rebuild(self,value):
        buf = b''
        if type(self.field) == UIntNField and self.field.n == 8:
            return value#.tobytes()
        if value is None:
            return b''
        if len(value) == 0:
            return b''
        for x in value:
            buf += self.field.rebuild(x)
        return buf
    
    def get_all_nodes(self,value,parent=None):
        nodes = []
        if value is None:
            return None
        if len(value) == 0:
            return None
        for x in value:
            if isinstance(x, StructureData) or isinstance(x, RepeatField):
                nodes += x.get_all_nodes(parent)
            else:
                return None
        return nodes
    
    
class ConstField(WasmField):
    """Pseudo-Field, always returning a constant, consuming/generating no data."""
    def __init__(self, const, **kwargs):
        super(ConstField, self).__init__(**kwargs)
        self.const = const

    def from_raw(self, ctx, raw):
        return 0, self.const, self


class ChoiceField(WasmField):
    """Depending on context, either represent this or that field type."""
    _shared_none_field = ConstField(None)

    def __init__(self, choice_field_map, choice_getter, **kwargs):
        super(ChoiceField, self).__init__(**kwargs)
        self.choice_field_map = choice_field_map
        self.choice_getter = choice_getter
        self.choice_data = None

    def from_raw(self, ctx, raw):
        choice = self.choice_getter(ctx)
        if choice is None:
            return 0, None, self._shared_none_field
        length, obj_data, obj_type  = self.choice_field_map[choice].from_raw(ctx, raw)
        self.choice_data = obj_data
        return length, obj_data, obj_type 


class BytesField(RepeatField):
    """Shorthand for U8 `RepeatField`, adding string support."""
    def __init__(self, length_getter, is_str=False):
        super(BytesField, self).__init__(UIntNField(8), length_getter)
        self.is_str = is_str

    def to_string(self, value):
        if not self.is_str:
            return super(BytesField, self).to_string(value)
        try:
            return '"' + bytearray(value).decode('utf8') + '"'
        except UnicodeDecodeError:
            return '<bad utf8>'

FieldMeta = collections.namedtuple('FieldMeta', 'name field')


class MetaInfo(object):
    """Meta information for a `Structure`."""
    def __init__(self):
        self.fields = []
        self.data_class = None
        self.structure = None
        self.name = ''
     

class StructureData(object):
    """Base class for generated structure data classes."""
    __slots__ = ('_meta', '_decoder_meta','_data_id')
    #_data_instance = 0
    def __init__(self, for_decoding=False):
        #self._data_id = StructureData._data_instance
        #StructureData._data_instance += 1


        self._decoder_meta = {'lengths': {}, 'types': {}} if for_decoding else None
        for cur_field_name, cur_field in self._meta.fields:
            setattr(self, cur_field_name, None)

    def get_meta(self):
        """
        Obtains meta info for this object. The object returned is shared
        between all objects of the same structure type.

        A getter is utilized here instead of a property to allow strict
        distinction of meta info from regular fields.
        """
        return self._meta

    def get_decoder_meta(self):
        """
        Obtains meta info from the decoder, like byte length in raw format.
        For objects not created through decoding, `None` is returned.
        """
        return self._decoder_meta
    def get_all_nodes(self,parent=None):
        
        nodes = []
        node_name = self._meta.name#self._meta.structure.__name__#+str(self._data_id) diff cond and class name
        node_type = self._meta.structure
        #pnode = {'name':node_name,'type':node_type,'data':self,'parent':parent}
        pnode = Node(node_name,node_type,self,parent)
        nodes.append(pnode)
        #print({'name':node_name,'data':self,'parent':parent})
        for cur_field_name, cur_field in self._meta.fields:
            field_val = getattr(self, cur_field_name)
            field_type = self.get_decoder_meta()['types'][cur_field_name]
            #print('[!]',cur_field_name,field_type)
            if isinstance(field_val, StructureData):
                nodes += field_val.get_all_nodes(pnode)
            elif isinstance(field_type, RepeatField):
                cnode = Node(cur_field_name,field_type,field_val,pnode)
                nodes.append(cnode)
                _node = field_type.get_all_nodes(field_val,cnode)
                if _node != None:
                    nodes += _node
            else:
                #print({'name':cur_field_name,'data':field_val,'parent':self._meta.structure.__name__+str(self._data_id)})
                #cnode = {'name':cur_field_name,'type':field_type,'data':field_val,'parent':pnode}
                cnode = Node(cur_field_name,field_type,field_val,pnode)
                nodes.append(cnode)
        return nodes
    def rebuild(self):
    #    print(self)
        return self._meta.structure().rebuild(self)

    @property
    @deprecated_func
    def _data_meta(self):
        """Property emulating old name of `_decoder_meta`. Deprecated, do not use."""
        return self._decoder_meta


class StructureMeta(type):
    """
    Metaclass used to create `Structure` classes,
    populating their `_meta` field and performing sanity checks.
    """
    def __new__(mcs, name, bases, cls_dict):
        # Inject _meta.
        #print("[+]",mcs, name, bases)
        meta = cls_dict['_meta'] = MetaInfo()
        # Iterate over fields, move relevant data to meta.
        for cur_field_name, cur_field in list(cls_dict.items()):
            # Is callable, property, private or magic? We don't touch those.
            if (
                isinstance(cur_field, collections.Callable) or
                isinstance(cur_field, property) or
                cur_field_name.startswith('_')
            ):
                pass

            # Is one of our types? Metafy.
            elif isinstance(cur_field, WasmField):
                #print(cur_field_name, cur_field)
                meta.fields.append(FieldMeta(cur_field_name, cur_field))

            # Unknown type, print warning.
            else:
                logger.warning(
                    'Non-WasmField typed field "{}" found on type "{}". '
                    'Ignoring.'.format(cur_field_name, name)
                )

        # Order fields by type ID (see `WasmField` for the "why").
        meta.fields = sorted(meta.fields, key=lambda x: x.field._type_id)

        # Create data class type for "instances".
        class GeneratedStructureData(StructureData):
            __slots__ = [x for x, _ in meta.fields]
            _meta = meta
        meta.data_class = GeneratedStructureData

        # Create class, saving type ref in meta.
        meta.structure = type.__new__(mcs, name, bases, cls_dict)
        return meta.structure


@add_metaclass(StructureMeta)
class Structure(WasmField):
    """Represents a collection of named fields."""
    def from_raw(self, ctx, raw):
        offs = 0
        data = self._meta.data_class(for_decoding=True)
        #print(data._meta.structure.__name__+str(data._data_id), data) #data msg
        #print("**************************")
        for cur_field_name, cur_field in self._meta.fields:
            data_len, val, data_type = cur_field.from_raw(data, raw[offs:])#all node info
            if isinstance(val, StructureData):
                val._meta.name = cur_field_name
            setattr(data, cur_field_name, val)
            #print(data, cur_field_name, val)
            decoder_meta = data.get_decoder_meta()
            decoder_meta['lengths'][cur_field_name] = data_len
            decoder_meta['types'][cur_field_name] = data_type
            #print(self.__class__.__name__,cur_field.__class__.__name__+str(cur_field._type_id),cur_field_name,data_len)
            offs += data_len
        return offs, data, self
 
    def to_string(self, value):
        lines = ['- [ {}'.format(self.__class__.__name__)]
        for cur_field_name, cur_field in self._meta.fields:
            field_val = getattr(value, cur_field_name)
            field_type = value.get_decoder_meta()['types'][cur_field_name]
            if isinstance(field_val, StructureData):
                lines.append('  | {} =\n{}'.format(
                    cur_field_name,
                    indent(field_type.to_string(field_val), '  ')
                ))
            else:
                lines.append('  | {} = {}'.format(
                    cur_field_name,
                    field_type.to_string(field_val)
                ))

        return '\n'.join(lines)

    def rebuild(self,value):
        #data = self._meta.data_class(for_decoding=True)._decoder_meta
        #print(data)
        buf = b''
        for cur_field_name, cur_field in self._meta.fields:
            #print(cur_field_name, cur_field)
            field_val = getattr(value, cur_field_name)
            field_type = value.get_decoder_meta()['types'][cur_field_name]
            #print(field_type,field_val)
            buf += field_type.rebuild(field_val)
        return buf
    def fix(self,value):
        pass
