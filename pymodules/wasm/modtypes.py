"""Defines data structures used in WASM (binary) modules."""
from __future__ import print_function, absolute_import, division, unicode_literals

from .wasmtypes import *
from .opcodes import OP_END
from .types import (
    Structure, CondField, RepeatField,
    ChoiceField, WasmField, ConstField, BytesField,
)


class ModuleHeader(Structure):
    magic = UInt32Field()
    version = UInt32Field()


class FunctionImportEntryData(Structure):
    type = VarUInt32Field()


class ResizableLimits(Structure):
    flags = VarUInt32Field()
    initial = VarUInt32Field()
    maximum = CondField(VarUInt32Field(), lambda x: x.flags & 1)


class TableType(Structure):
    element_type = ElementTypeField()
    limits = ResizableLimits()


class MemoryType(Structure):
    limits = ResizableLimits()


class GlobalType(Structure):
    content_type = ValueTypeField()
    mutability = VarUInt1Field()


class ImportEntry(Structure):
    module_len = VarUInt32Field()
    module_str = BytesField(lambda x: x.module_len, is_str=True)
    field_len = VarUInt32Field()
    field_str = BytesField(lambda x: x.field_len, is_str=True)
    kind = ExternalKindField()
    type = ChoiceField({
        0: FunctionImportEntryData(),
        1: TableType(),
        2: MemoryType(),
        3: GlobalType(),
    }, lambda x: x.kind)


    def fix(self,value):
        setattr(value,'module_len',len(getattr(value,'module_str')))
        setattr(value,'field_len',len(getattr(value,'field_str')))

class ImportSection(Structure):
    count = VarUInt32Field()
    entries = RepeatField(ImportEntry(), lambda x: x.count)

    def fix(self,value):
        setattr(value,'count',len(getattr(value,'entries')))



class FuncType(Structure):
    form = VarInt7Field()
    param_count = VarUInt32Field()
    param_types = RepeatField(ValueTypeField(), lambda x: x.param_count)
    return_count = VarUInt1Field()
    return_type = CondField(ValueTypeField(), lambda x: bool(x.return_count))

    def fix(self,value):
        setattr(value,'param_count',len(getattr(value,'param_types')))


class TypeSection(Structure):
    count = VarUInt32Field()
    entries = RepeatField(FuncType(), lambda x: x.count)

    def fix(self,value):
        setattr(value,'count',len(getattr(value,'entries')))

class FunctionSection(Structure):
    count = VarUInt32Field()
    types = RepeatField(VarUInt32Field(), lambda x: x.count)

    def fix(self,value):
        setattr(value,'count',len(getattr(value,'types')))


class TableSection(Structure):
    count = VarUInt32Field()
    entries = RepeatField(TableType(), lambda x: x.count)

    def fix(self,value):
        setattr(value,'count',len(getattr(value,'entries')))


class MemorySection(Structure):
    count = VarUInt32Field()
    entries = RepeatField(MemoryType(), lambda x: x.count)

    def fix(self,value):
        setattr(value,'count',len(getattr(value,'entries')))

class InitExpr(WasmField):
    def from_raw(self, struct, raw):
        from .decode import decode_bytecode

        offs = 0
        instrs = []
        for cur_insn in decode_bytecode(raw):
            offs += cur_insn.len
            instrs.append(cur_insn)
            if cur_insn.op.id == OP_END:
                break
        return offs, raw[:offs], self
        #return offs, instrs, self
    def rebuild(self,value):
        return value  #.tobytes()

class GlobalEntry(Structure):
    type = GlobalType()
    init = InitExpr()


class GlobalSection(Structure):
    count = VarUInt32Field()
    globals = RepeatField(GlobalEntry(), lambda x: x.count)


    def fix(self,value):
        setattr(value,'count',len(getattr(value,'globals')))

class ExportEntry(Structure):
    field_len = VarUInt32Field()
    field_str = BytesField(lambda x: x.field_len, is_str=True)
    kind = ExternalKindField()
    index = VarUInt32Field()

    def fix(self,value):
        setattr(value,'field_len',len(getattr(value,'field_str')))

class ExportSection(Structure):
    count = VarUInt32Field()
    entries = RepeatField(ExportEntry(), lambda x: x.count)

    def fix(self,value):
        setattr(value,'count',len(getattr(value,'entries')))


class StartSection(Structure):
    index = VarUInt32Field()


class ElementSegment(Structure):
    index = VarUInt32Field()
    offset = InitExpr()
    num_elem = VarUInt32Field()
    elems = RepeatField(VarUInt32Field(), lambda x: x.num_elem)

    def fix(self,value):
        setattr(value,'num_elem',len(getattr(value,'elems')))

class ElementSection(Structure):
    count = VarUInt32Field()
    entries = RepeatField(ElementSegment(), lambda x: x.count)

    def fix(self,value):
        setattr(value,'count',len(getattr(value,'entries')))


class LocalEntry(Structure):
    count = VarUInt32Field()
    type = ValueTypeField()


class FunctionBody(Structure):
    body_size = VarUInt32Field()
    local_count = VarUInt32Field()
    locals = RepeatField(
        LocalEntry(),
        lambda x: x.local_count,
    )
    code = BytesField(
        lambda x: (
            x.body_size -
            x.get_decoder_meta()['lengths']['local_count'] -
            x.get_decoder_meta()['lengths']['locals']
        )
    )
    def fix(self,value):
        setattr(value,'local_count',len(getattr(value,'locals')))
        _body_size = value.get_decoder_meta()['lengths']['local_count'] + value.get_decoder_meta()['lengths']['locals']+ value.get_decoder_meta()['lengths']['code']
        setattr(value,'body_size',_body_size)  
        

class CodeSection(Structure):
    count = VarUInt32Field()
    bodies = RepeatField(FunctionBody(), lambda x: x.count)
    
    def fix(self,value):
        setattr(value,'count',len(getattr(value,'bodies')))


class DataSegment(Structure):
    index = VarUInt32Field()
    offset = InitExpr()
    size = VarUInt32Field()
    data = BytesField(lambda x: x.size)
    
    def fix(self,value):
        setattr(value,'size',len(getattr(value,'data')))


class DataSection(Structure):
    count = VarUInt32Field()
    entries = RepeatField(DataSegment(), lambda x: x.count)

    def fix(self,value):
        setattr(value,'count',len(getattr(value,'entries')))

class DataCountSection(Structure):
    count = VarUInt32Field()


class Naming(Structure):
    index = VarUInt32Field()
    name_len = VarUInt32Field()
    name_str = BytesField(lambda x: x.name_len, is_str=True)
 
    def fix(self,value):
        setattr(value,'name_len',len(getattr(value,'name_str')))


class NameMap(Structure):
    count = VarUInt32Field()
    names = RepeatField(Naming(), lambda x: x.count)

    def fix(self,value):
        setattr(value,'count',len(getattr(value,'names')))


class LocalNames(Structure):
    index = VarUInt32Field()
    local_map = NameMap()


class LocalNameMap(Structure):
    count = VarUInt32Field()
    funcs = RepeatField(LocalNames, lambda x: x.count)

    def fix(self,value):
        setattr(value,'count',len(getattr(value,'funcs')))

class NameSubSection(Structure):
    name_type = VarUInt7Field()
    payload_len = VarUInt32Field()
    payload = ChoiceField({
        NAME_SUBSEC_FUNCTION: NameMap(),
        NAME_SUBSEC_LOCAL: LocalNameMap(),
    }, lambda x: x.name_type)


class Section(Structure):
    id = VarUInt7Field()
    payload_len = VarUInt32Field()
    name_len = CondField(
        VarUInt32Field(),
        lambda x: x.id == 0,
    )
    name = CondField(
        BytesField(lambda x: x.name_len, is_str=True),
        lambda x: x.id == 0,
    )

    payload = ChoiceField({
        SEC_UNK: BytesField(lambda x: (
            x.payload_len -
            x.get_decoder_meta()['lengths']['name'] -
            x.get_decoder_meta()['lengths']['name_len']
        )),
        SEC_TYPE: TypeSection(),
        SEC_IMPORT: ImportSection(),
        SEC_FUNCTION: FunctionSection(),
        SEC_TABLE: TableSection(),
        SEC_MEMORY: MemorySection(),
        SEC_GLOBAL: GlobalSection(),
        SEC_EXPORT: ExportSection(),
        SEC_START: StartSection(),
        SEC_ELEMENT: ElementSection(),
        SEC_CODE: CodeSection(),
        SEC_DATA: DataSection(),
        SEC_DATA_COUNT: DataCountSection(),
    }, lambda x: x.id)

    overhang = BytesField(lambda x: max(0, (
        x.payload_len -
        x.get_decoder_meta()['lengths']['name'] -
        x.get_decoder_meta()['lengths']['name_len'] -
        x.get_decoder_meta()['lengths']['payload']
    )))
  
    def fix(self,value):
        _payload_len = value.get_decoder_meta()['lengths']['name'] + value.get_decoder_meta()['lengths']['name_len'] + value.get_decoder_meta()['lengths']['payload']
        setattr(value,'payload_len',_payload_len)  
        if getattr(value,'id') == 0:
             setattr(value,'name_len',len(getattr(value,'name')))  
