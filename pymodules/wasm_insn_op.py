import random
from wasm.formatter import *
from wasm.decode import *
from wasm.opcodes import OPCODES
import binascii


# Parameter
variableInstruction = ['20', '21', '22', '23', '24']
memoryInstruction = ['28', '29', '2a', '2b', '2c', '2d', '2e', '2f', '31', '32', '33', '34', '35', '36', '37', '38', '39', '3a', '3b', '3c', '3d', '3e']
constInstruction = ['41', '42', '43', '44']
# No Parameter
numericInstruction = ['45', '46', '47', '48', '49', '4a', '4b', '4c', '4d', '4e', '4f', 
                      '50', '51', '52', '53', '54', '55', '56', '57', '58', '59', '5a', '5b', '5c', '5d', '5e', '5f',
                      '60', '61', '62', '63', '64', '65', '66', '67', '68', '69', '6a', '6b', '6c', '6d', '6e', '6f',
                      '70', '71', '72', '73', '74', '75', '76', '77', '78', '79', '7a', '7b', '7c', '7d', '7e', '7f',
                      '80', '81', '82', '83', '84', '85', '86', '87', '88', '89', '8a', '8b', '8c', '8d', '8e', '8f',
                      '90', '91', '92', '93', '94', '95', '96', '97', '98', '99', '9a', '9b', '9c', '9d', '9e', '9f',
                      'a0', 'a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7', 'a8', 'a9', 'aa', 'ab', 'ac', 'ad', 'ae', 'af',
                      'b0', 'b1', 'b2', 'b3', 'b4', 'b5', 'b6', 'b7', 'b8', 'b9', 'ba', 'bb', 'bc', 'bd', 'be', 'bf']

InstructionList = ["variableInstruction", "memoryInstruction", "constInstruction", "numericInstruction"]


# Insert Instruction
def insertInstruction(wasm_bytes):
    wasm_byte_len = len(wasm_bytes)
    if wasm_byte_len < 4:
        return bytearray(binascii.unhexlify(wasm_bytes))
    
    index = random.randint(1, wasm_byte_len - 2)
    insert_position = index + index % 2
    
    item = random.choice(InstructionList)
    if item == "numericInstruction":
        random_inst = random.choice(numericInstruction)
        new_instruction = random_inst
        wasm_bytes = wasm_bytes[:insert_position] + new_instruction + wasm_bytes[insert_position:]
    elif item == "variableInstruction":
        random_inst = random.choice(variableInstruction)
        random_byte = random.randint(0x00, 0xff)
        hex_random_byte = format(random_byte, '02x')
        new_instruction = random_inst + hex_random_byte
        wasm_bytes = wasm_bytes[:insert_position] + new_instruction + wasm_bytes[insert_position:]
    elif item == "memoryInstruction":
        random_inst = random.choice(memoryInstruction)
        random_byte = random.randint(0x00, 0xff)
        hex_random_byte = format(random_byte, '02x')
        new_instruction = random_inst + hex_random_byte
        wasm_bytes = wasm_bytes[:insert_position] + new_instruction + wasm_bytes[insert_position:]
    elif item == "constInstruction":
        random_inst = random.choice(constInstruction)
        random_byte = random.randint(0x00, 0xff)
        hex_random_byte = format(random_byte, '02x')
        new_instruction = random_inst + hex_random_byte
        wasm_bytes = wasm_bytes[:insert_position] + new_instruction + wasm_bytes[insert_position:]

    wasm_bytearray = bytearray(wasm_bytes.encode('utf-8')).replace(b'\\\\', b'\\')
    
    return bytearray(binascii.unhexlify(bytes(wasm_bytearray)))


# Delete Instruction
def eraseInstruction(wasm_bytes):
    wasm_byte_len = len(wasm_bytes)
    if wasm_byte_len < 4:
        return bytearray(binascii.unhexlify(wasm_bytes))

    formate_wasm_byte = ''.join('\\x' + wasm_bytes[i:i+2] for i in range(0, len(wasm_bytes), 2))

    item = random.choice(InstructionList)
    if item == "numericInstruction":
        random_inst = '\\x' + random.choice(numericInstruction)
        offset = formate_wasm_byte.find(random_inst)
        if offset != -1:
            formate_wasm_byte = formate_wasm_byte[:offset] + formate_wasm_byte[offset + len(random_inst):]
    elif item == "variableInstruction":
        random_inst = '\\x' + random.choice(variableInstruction)
        offset = formate_wasm_byte.find(random_inst)
        if offset != -1:
            formate_wasm_byte = formate_wasm_byte[:offset] + formate_wasm_byte[offset + len(random_inst) + 4:]
    elif item == "memoryInstruction":
        random_inst = '\\x' + random.choice(memoryInstruction)
        offset = formate_wasm_byte.find(random_inst)
        if offset != -1:
            formate_wasm_byte = formate_wasm_byte[:offset] + formate_wasm_byte[offset + len(random_inst) + 4:]
    elif item == "constInstruction":
        random_inst = '\\x' + random.choice(constInstruction)
        offset = formate_wasm_byte.find(random_inst)
        if offset != -1:
            formate_wasm_byte = formate_wasm_byte[:offset] + formate_wasm_byte[offset + len(random_inst) + 4:]

    formate_wasm_byte = formate_wasm_byte.replace("\\x", "")
    wasm_bytearray = bytearray(formate_wasm_byte.encode('utf-8')).replace(b'\\\\', b'\\')

    return bytearray(binascii.unhexlify(bytes(wasm_bytearray)))


# Move Instruction
def moveInstruction(wasm_bytes):
    wasm_byte_len = len(wasm_bytes)
    if wasm_byte_len < 4:
        return bytearray(binascii.unhexlify(wasm_bytes))
    
    formate_wasm_byte = ''.join('\\x' + wasm_bytes[i:i+2] for i in range(0, len(wasm_bytes), 2))

    index = random.randint(1, wasm_byte_len - 2)
    move_position = index + index % 2

    item = random.choice(InstructionList)
    if item == "numericInstruction":
        radom_inst = '\\x' + random.choice(numericInstruction)
        offset = formate_wasm_byte.find(radom_inst)
        if offset != -1:
            instruction = formate_wasm_byte[offset:offset + len(radom_inst)]
            formate_wasm_byte = formate_wasm_byte[:offset] + formate_wasm_byte[offset + len(radom_inst):]
            formate_wasm_byte = formate_wasm_byte[:move_position] + instruction + formate_wasm_byte[move_position:]
    elif item == "variableInstruction":
        radom_inst = '\\x' + random.choice(variableInstruction)
        offset = formate_wasm_byte.find(radom_inst)
        if offset != -1:
            instruction = formate_wasm_byte[offset:offset + len(radom_inst) + 4]
            formate_wasm_byte = formate_wasm_byte[:offset] + formate_wasm_byte[offset + len(radom_inst) + 4:]
            formate_wasm_byte = formate_wasm_byte[:move_position] + instruction + formate_wasm_byte[move_position:]
    elif item == "memoryInstruction":
        radom_inst = '\\x' + random.choice(memoryInstruction)
        offset = formate_wasm_byte.find(radom_inst)
        if offset != -1:
            instruction = formate_wasm_byte[offset:offset + len(radom_inst) + 4]
            formate_wasm_byte = formate_wasm_byte[:offset] + formate_wasm_byte[offset + len(radom_inst) + 4:]
            formate_wasm_byte = formate_wasm_byte[:move_position] + instruction + formate_wasm_byte[move_position:]
    elif item == "constInstruction":
        radom_inst = '\\x' + random.choice(constInstruction)
        offset = formate_wasm_byte.find(radom_inst)
        if offset != -1:
            instruction = formate_wasm_byte[offset:offset + len(radom_inst) + 4]
            formate_wasm_byte = formate_wasm_byte[:offset] + formate_wasm_byte[offset + len(radom_inst) + 4:]
            formate_wasm_byte = formate_wasm_byte[:move_position] + instruction + formate_wasm_byte[move_position:]

    formate_wasm_byte = formate_wasm_byte.replace("\\x", "")
    wasm_bytearray = bytearray(formate_wasm_byte.encode('utf-8')).replace(b'\\\\', b'\\')
    
    return bytearray(binascii.unhexlify(bytes(wasm_bytearray)))


# TODO: Replace Instruction
def replaceInstruction(wasm_bytes):
    wasm_byte_len = len(wasm_bytes)
    if wasm_byte_len < 4:
        return wasm_bytes
    
