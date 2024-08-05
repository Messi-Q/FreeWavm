#!/usr/bin/env python
# encoding: utf-8
'''
Example Python Module for AFLFuzz

@author:     Christian Holler (:decoder)

@license:

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.

@contact:    choller@mozilla.com
'''

from __future__ import print_function, absolute_import, division, unicode_literals

from collections import namedtuple
from .wasm.modtypes import *
from .wasm.opcodes import OPCODE_MAP
from .wasm.compat import byte2int
from .wasm.types import *
from .mutator import *
from .weighted_choice import *
from .wasm_insn_op import *
import random
import binascii


# Global Definition
NODE_WEIGHT_LIST = [('FirstLevel', 1), ('SecondLevel', 1), ('ThirdLevel', 1), ('FourLevel', 1), ('OtherLevel', 1)] 
NODE_LEVEL_LIST = ['FirstLevel', 'SecondLevel', 'ThirdLevel', 'FourLevel', 'OtherLevel'] 
EPSILON = 0.1

adaptive_epsilon_greedy = AdapativeEpsilonGreedy(len(NODE_LEVEL_LIST), EPSILON)
adaptive_thompson_sampler = AdapativeThompsonSampling(len(NODE_LEVEL_LIST))


# Wasm File Parser => Parse Tree
def parser(buf):
    hdr = ModuleHeader()
    hdr_len, hdr_data, _ = hdr.from_raw(None, buf)
    buf = buf[hdr_len:]
    sec_list = []
    sec_data_list = []

    while buf:
        sec = Section()
        sec_len, sec_data, _ = sec.from_raw(None, buf)
        # print("[+] len ",sec_len)
        sec_list.append(sec)
        sec_data_list.append(sec_data)
        buf = buf[sec_len:]
    
    buf_new = hdr.rebuild(hdr_data)

    return buf_new, sec_list, sec_data_list


# Extract different levels of leaf nodes
def node_path(node):
    path = ''
    while True:
        s = node.name
        parent = node.parent
        path += s
        if parent == None:
            return path
        if type(parent.data) == list:
            index = parent.data.index(node.data)
            path = path+'['+str(index)+']'+'.'
        else:
            path = path + '.'
        node = parent


# Specific mutation operation
def RunMutate(subnode):
    byte_mutators = [mutate_case_0, mutate_case_1, mutate_case_2, mutate_case_3, mutate_case_4, mutate_case_5, mutate_case_6, 
                     mutate_case_7, mutate_case_8, mutate_case_9, mutate_case_10, mutate_case_11, mutate_case_12, mutate_case_13, 
                     mutate_case_14, mutate_case_15]
    structure_mutators = [mutate_case_structure_clone, mutate_case_structure_sub]
    structure_int_mutators = [muate_case_int_add, mutate_case_int_clone, mutate_case_int_sub]
    instruction_mutators = [insertInstruction, eraseInstruction, moveInstruction]
    ByteMutatorList = ["byte_mutators", "instruction_mutators"]

    path = node_path(subnode)
    result = path.split(".")
    
    # TODO: The selection strategy of mutators can be optimized
    fix_len = 0
    if isinstance(subnode.type, SignedLeb128Field):
        fix_len = mutate_case_signedlebint_replace(subnode)
    elif isinstance(subnode.type, UnsignedLeb128Field):
        fix_len = mutate_case_unsignedlebint_replace(subnode)
    elif isinstance(subnode.type, UIntNField):
        fix_len = mutate_case_uintnfield_replace(subnode)
    elif isinstance(subnode.type, BytesField):
        item = random.choice(ByteMutatorList)
        if item == "byte_mutators":
            if 'code' in result or 'data' in result:
                if subnode.name != "overhang" and len(subnode.data) > 0:
                    bytemutate = random.choice(byte_mutators)
                    _, fix_len = bytemutate(subnode.data)
        elif item == "instruction_mutators":
            DataLen = len(subnode.data)
            ByteNodeData = binascii.hexlify(subnode.data).decode('utf-8')
            insnMutate = random.choice(instruction_mutators)
            NewByteData = insnMutate(ByteNodeData)
            NewDataLen = len(NewByteData)
            fix_len = NewDataLen - DataLen
    elif isinstance(subnode.type, RepeatField) and not isinstance(subnode.type, BytesField):
        if len(subnode.data) > 0:
                subnodeData = random.choice(subnode.data)
                if isinstance(subnodeData, StructureData):
                    structuremutate = random.choice(structure_mutators)
                    fix_len = structuremutate(subnode)
                elif type(subnodeData) == int:
                    randomSelect = random.randint(1, 10)
                    if randomSelect >= 5:
                        structureintmutate = random.choice(structure_int_mutators)
                        fix_len = structureintmutate(subnode)
                    else:
                        if isinstance(subnode.type.field, SignedLeb128Field):
                            fix_len = mutate_case_signedint_replace(subnode)
                        elif isinstance(subnode.type.field, UnsignedLeb128Field):
                            fix_len = mutate_case_unsignedint_replace(subnode)
                        elif isinstance(subnode.type.field, UIntNField):
                            fix_len = mutate_case_uintn_replace(subnode)
    
    # fixing
    subnode.fix_node_data_length(fix_len)
    subnode.fix() 



# Parse Tree-based Structure-Aware Mutation 
def parseTreeMutate(allNode):
    # Strategy 1 : Randomly Selection
    filedName = random.choice(NODE_LEVEL_LIST)

    # Strategy 2 : Adaptive Thompson Sampling
    # index = adaptive_thompson_sampler.choose_arm()
    # filedName = NODE_LEVEL_LIST[index]
    # adaptive_thompson_sampler.update_parameters(index, feedback)

    # Strategy 3 : Adaptive Epsilon Greedy
    # index = adaptive_epsilon_greedy.choose_arm()
    # filedName = NODE_LEVEL_LIST[index]
    # adaptive_epsilon_greedy.update_parameters(index, feedback)

    # Strategy 4 : Roulette Wheel Selection
    # result = weighted_random_choice(NODE_WEIGHT_LIST)
    # filedName = result.weighted_choice()

    if filedName == "FirstLevel":
        filed = allNode.get(filedName)
        if len(filed) > 0:
            subnode = random.choice(filed)
            RunMutate(subnode)
    
        # # update tuple list
        # for i in range(len(NODE_WEIGHT_LIST)):
        #     if "FirstLevel" in NODE_WEIGHT_LIST[i]:
        #         value1, value2 = NODE_WEIGHT_LIST[i]
        #         value2 += feedback
        #         NODE_WEIGHT_LIST = (value1, value2)
        #         NODE_WEIGHT_LIST[i] = updated_tuple
    
    if filedName == "SecondLevel":
        filed = allNode.get(filedName)
        if len(filed) > 0:
            subnode = random.choice(filed)
            RunMutate(subnode)
    
    if filedName == "ThirdLevel":
        filed = allNode.get(filedName)
        if len(filed) > 0:
            subnode = random.choice(filed)
            RunMutate(subnode)
    
    if filedName == "FourLevel":
        filed = allNode.get(filedName)
        if len(filed) > 0:
            subnode = random.choice(filed)
            RunMutate(subnode)
    
    if filedName == "OtherLevel":
        filed = allNode.get(filedName)
        if len(filed) > 0:
            subnode = random.choice(filed)
            RunMutate(subnode)


def init(seed):
    '''
    Called once when AFLFuzz starts up.

    @type seed: int
    @param seed: A 32-bit random value
    '''
    # generate a seed randomly
    random.seed(seed)
    return 0


def fuzz(buf, add_buf):
    '''
    Called per fuzzing iteration.
    
    @type buf: bytearray
    @param buf: The buffer that should be mutated.
    
    @type add_buf: bytearray
    @param add_buf: A second buffer that can be used as mutation source.
    
    @rtype: bytearray
    @return: A new bytearray containing the mutated data
    '''
    ret = bytearray(buf)
    
    # catch potential abnormal test cases or potential issues of parser
    try:
        ref_new, sec_list, sec_data_list = parser(ret)
    except Exception as e:
        print("Exception", e)

    
    # classify nodes based on the node types
    allField = []
    nodeUIntNField = []
    nodeUnsignedLeb128Field = []
    nodeSignedLeb128Field = []
    nodeRepeatField = []
    nodeBytesField = []

    # classify nodes based on the leaf levels
    allNode = []
    firstLevelLeafNode = []
    secondLevelLeafNode = []
    thirdLevelLeafNode = []
    fourLevelLeafNode = []
    leafNode = []

    # The buffer that should be mutated
    for i in range(len(sec_list)):
        nodes = sec_data_list[i].get_all_nodes()
        
        for node in nodes:
            path = node_path(node)
            result = path.split(".")
            if 'code' in result or 'data' in result:
                nodeBytesField.append(node)
            # if isinstance(node.type, BytesField):
            #     nodeBytesField.append(node) 
            if isinstance(node.type, RepeatField) and not isinstance(node.type, BytesField):
                nodeRepeatField.append(node)
            if isinstance(node.type, SignedLeb128Field):
                nodeSignedLeb128Field.append(node)
            if isinstance(node.type, UnsignedLeb128Field):
                nodeUnsignedLeb128Field.append(node)
            if isinstance(node.type, UIntNField):
                nodeUIntNField.append(node)

        for node in nodes:
            path = str(node_path(node))
            result = path.split(".")
            if len(result) == 2 and not isinstance(node.type, StructureMeta) and not isinstance(node.type, InitExpr):
                firstLevelLeafNode.append(node)
            if len(result) == 3 and not isinstance(node.type, StructureMeta) and not isinstance(node.type, InitExpr):
                secondLevelLeafNode.append(node)
            if len(result) == 5 and not isinstance(node.type, StructureMeta) and not isinstance(node.type, InitExpr):
                thirdLevelLeafNode.append(node)
            if len(result) == 6 and not isinstance(node.type, StructureMeta) and not isinstance(node.type, InitExpr):
                fourLevelLeafNode.append(node)
            if len(result) > 6 and not isinstance(node.type, StructureMeta) and not isinstance(node.type, InitExpr):
                leafNode.append(node)
    
    # mutation operation (first version)
    # allNodeField = [nodeBytesField, nodeRepeatField, nodeUnsignedLeb128Field, nodeSignedLeb128Field, nodeUIntNField]
    # allFieldName = ['BytesField', 'RepeatField', 'UnsignedLeb128Field', 'SignedLeb128Field', 'UIntNField']
    # allField = dict(zip(allFieldName, allNodeField))
    # mutate(allField)

    # Parse Tree-based Mutation
    allLeafNode = [firstLevelLeafNode, secondLevelLeafNode, thirdLevelLeafNode, fourLevelLeafNode, leafNode]
    allNodeName = ['FirstLevel', 'SecondLevel', 'ThirdLevel', 'FourLevel', 'OtherLevel']
    allNode = dict(zip(allNodeName, allLeafNode))
    parseTreeMutate(allNode)
 
    for i in range(len(sec_list)):
        ref_new += sec_list[i].rebuild(sec_data_list[i])
    
    return bytearray(ref_new)


def init_trim(buf):
    return 0

def trim():
    pass

def post_trim(success):
    return 0


# Mutation Operation
def mutate(allField):
    byte_mutators = [mutate_case_0, mutate_case_1, mutate_case_2, mutate_case_3, mutate_case_4, mutate_case_5, mutate_case_6, 
                     mutate_case_7, mutate_case_8, mutate_case_9, mutate_case_10, mutate_case_11, mutate_case_12, mutate_case_13, 
                     mutate_case_14, mutate_case_15]
    structure_mutators = [mutate_case_structure_clone, mutate_case_structure_sub]
    structure_int_mutators = [muate_case_int_add, mutate_case_int_clone, mutate_case_int_sub]
    
    # Manually set the probability of different node types
    node_weight_list = [('RepeatField', 2), ('BytesField', 6), ('UnsignedLeb128Field', 1), ('SignedLeb128Field', 1), ('UIntNField', 1)]
    
    # Mutation strategy design can be set here 

    # Randomly select the type of node that requires mutation. 
    # The higher the weight of the weight, the greater the probability of being selected (here you can redesign it)
    filedName = weighted_choice(node_weight_list)
    
    # perform mutation
    if filedName == "BytesField":
        filed = allField.get(filedName)
        if len(filed) > 0:
            subnode = random.choice(filed)
            if subnode.name != "overhang" and len(subnode.data) > 0:
                bytemutate = random.choice(byte_mutators)
                _, fix_len = bytemutate(subnode.data)
                subnode.fix_node_data_length(fix_len)
                subnode.fix()

    if filedName == "RepeatField":
        filed = allField.get(filedName)
        if len(filed) > 0:
            subnode = random.choice(filed)
            if len(subnode.data) > 0:
                subnodeData = random.choice(subnode.data)
                if isinstance(subnodeData, StructureData):
                    structuremutate = random.choice(structure_mutators)
                    fix_len = structuremutate(subnode)
                    subnode.fix_node_data_length(fix_len)
                    subnode.fix()
                elif type(subnodeData) == int:
                    fix_len = 0
                    randomSelect = random.randint(1, 10)
                    if randomSelect >= 5:
                        structureintmutate = random.choice(structure_int_mutators)
                        fix_len = structureintmutate(subnode)
                    else:
                        if isinstance(subnode.type.field, SignedLeb128Field):
                            fix_len = mutate_case_signedint_replace(subnode)
                        elif isinstance(subnode.type.field, UnsignedLeb128Field):
                            fix_len = mutate_case_unsignedint_replace(subnode)
                        elif isinstance(subnode.type.field, UIntNField):
                            fix_len = mutate_case_uintn_replace(subnode)
                    subnode.fix_node_data_length(fix_len)
                    subnode.fix()
    
    if filedName == "UnsignedLeb128Field":
        filed = allField.get(filedName)
        if len(filed) > 0:
            subnode = random.choice(filed)
            fix_len = mutate_case_unsignedlebint_replace(subnode)
            subnode.fix_node_data_length(fix_len)
            subnode.fix()

    if filedName == "SignedLeb128Field":
        filed = allField.get(filedName)
        if len(filed) > 0:
            subnode = random.choice(filed)
            fix_len = mutate_case_signedlebint_replace(subnode)
            subnode.fix_node_data_length(fix_len)
            subnode.fix()
    
    if filedName == "UIntNField":
        filed = allField.get(filedName) 
        if len(filed) > 0:
            subnode = random.choice(filed)
            fix_len = mutate_case_uintnfield_replace(subnode)
            subnode.fix_node_data_length(fix_len)
            subnode.fix()


# Uncomment and implement the following methods if you want to use a custom
# trimming algorithm. See also the documentation for a better API description.

# def init_trim(buf):
#     '''
#     Called per trimming iteration.
#     
#     @type buf: bytearray
#     @param buf: The buffer that should be trimmed.
#     
#     @rtype: int
#     @return: The maximum number of trimming steps.
#     '''
#     global ...
#     
#     # Initialize global variables
#     
#     # Figure out how many trimming steps are possible.
#     # If this is not possible for your trimming, you can
#     # return 1 instead and always return 0 in post_trim
#     # until you are done (then you return 1).
#         
#     return steps
# 
# def trim():
#     '''
#     Called per trimming iteration.
# 
#     @rtype: bytearray
#     @return: A new bytearray containing the trimmed data.
#     '''
#     global ...
#     
#     # Implement the actual trimming here
#     
#     return bytearray(...)
# 
# def post_trim(success):
#     '''
#     Called after each trimming operation.
#     
#     @type success: bool
#     @param success: Indicates if the last trim operation was successful.
#     
#     @rtype: int
#     @return: The next trim index (0 to max number of steps) where max
#              number of steps indicates the trimming is done.
#     '''
#     global ...
# 
#     if not success:
#         # Restore last known successful input, determine next index
#     else:
#         # Just determine the next index, based on what was successfully
#         # removed in the last step
#     
#     return next_index
