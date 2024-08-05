# import byteconv as bc
import random
import os

INTERSTRING_8 = [-128 & 0xff,-1 & 0xff,0 & 0xff,1 & 0xff,16 & 0xff,32 & 0xff,64 & 0xff,100 & 0xff,127 & 0xff]
INTERSTRING_16 = [-32768 & 0xffff,-129 & 0xffff,128 & 0xffff,255 & 0xffff,256 & 0xffff,512 & 0xffff,1000 & 0xffff,1024 & 0xffff,4096 & 0xffff,32767 & 0xffff]
INTERSTRING_32 = [-2147483648 & 0xffffffff,-100663046 & 0xffffffff,-32769 & 0xffffffff,32768 & 0xffffffff,65535 & 0xffffffff,65536 & 0xffffffff,100663045 & 0xffffffff,2147483647 & 0xffffffff] 

intersing_8 = INTERSTRING_8
intersing_16 = INTERSTRING_8 + INTERSTRING_16
intersing_32 = INTERSTRING_8 + INTERSTRING_16 + INTERSTRING_32

def UR(limit):
	r = random.randint(0, limit - 1)
	return r
	
def URBYTE():
	r = UR(0x100)
	return r

def URWORD():
	r = UR(0x10000)
	return r

def URDWORD():
	r = UR(0x100000000)
	return r		

# Bytes Mutation Operation
def mutate_case_0(buf):	 # FLIP_BIT
	buf_len = len(buf)
	_bf = UR(buf_len<<3)
	buf[_bf>>3] = int(buf[_bf>>3]) ^ (128 >> (_bf & 7))
	fix_len = len(buf) - buf_len
	return buf, fix_len
	
def mutate_case_1(buf):	 # SET_BYTE_INTER_VALUE
	buf_len = len(buf)
	buf[UR(buf_len)] = random.choice(intersing_8) & 0xff
	fix_len = len(buf) - buf_len
	return buf, fix_len
	
def mutate_case_2(buf):	 # SET_WORD_INTER_VALUE
	buf_len = len(buf)
	if(buf_len < 2):
		return buf, 0
	int16 = random.choice(intersing_16)
	int16_0 = int16 & 0xff
	int16_1 = (int16 >> 8) & 0xff
	# print "%x,%x,%x" % (int16,int16_0,int16_1)
	index = UR(buf_len-1)
	if(UR(2)):
		buf[index] = int16_0
		buf[index+1] = int16_1
	else:
		buf[index] = int16_1
		buf[index+1] = int16_0
	fix_len = len(buf) - buf_len
	return buf, fix_len
	
def mutate_case_3(buf):	 # SET_DWORD_INTER_VALUE
	buf_len = len(buf)
	if(buf_len < 4):
		return buf, 0
	int32 = random.choice(intersing_32)
	int32_0 = int32 & 0xff
	int32_1 = (int32 >> 8) & 0xff
	int32_2 = (int32 >> 16) & 0xff
	int32_3 = (int32 >> 24) & 0xff
	# print "%d,%x,%x,%x,%x" % (int32,int32_0,int32_1,int32_2,int32_3)
	index = UR(buf_len - 3)
	if(UR(2)):
		buf[index] = int32_0
		buf[index+1] = int32_1
		buf[index+2] = int32_2
		buf[index+3] = int32_3
	else:
		buf[index] = int32_3
		buf[index+1] = int32_2
		buf[index+2] = int32_1
		buf[index+3] = int32_0
	fix_len = len(buf) - buf_len
	return buf, fix_len
	
def mutate_case_4(buf):  # SUB_BYTE_VALUE
	buf_len = len(buf)
	buf[UR(buf_len)] = (buf[UR(buf_len)] - (1 + UR(35))) & 0xff
	fix_len = len(buf) - buf_len
	return buf, fix_len
	
def mutate_case_5(buf):  # ADD_BYTE_VALUE
	buf_len = len(buf)
	buf[UR(buf_len)] = (buf[UR(buf_len)] + 1 + UR(35)) & 0xff
	fix_len = len(buf) - buf_len
	return buf, fix_len
	
def mutate_case_6(buf):  # SUB_WORD_VALUE	
	buf_len = len(buf)
	if(buf_len < 2):
		return buf, 0
	index = UR(buf_len - 1)  # index
	int16_0 = buf[index]
	int16_1 = buf[index+1]
	num = 1 + UR(35)
	
	if(UR(2)):
		int16 = int16_1<<8 + int16_0
		int16 = (int16 - num) & 0xffff
		
		int16_0 = int16 & 0xff
		int16_1 = (int16 >> 8) & 0xff
	else:
		int16 = int16_0<<8 + int16_1
		int16 = (int16 - num) & 0xffff
		
		int16_1 = int16 & 0xff
		int16_0 = (int16 >> 8) & 0xff
		
	buf[index] = int16_0
	buf[index+1] = int16_1
	fix_len = len(buf) - buf_len
	return buf, fix_len
	
def mutate_case_7(buf):  # ADD_WORD_VALUE	
	buf_len = len(buf)
	if(buf_len < 2):
		return buf, 0
	index = UR(buf_len - 1)  # index
	int16_0 = buf[index]
	int16_1 = buf[index+1]
	num = 1 + UR(35)
	
	if(UR(2)):
		int16 = int16_1<<8 + int16_0
		int16 = (int16 + num) & 0xffff
		
		int16_0 = int16 & 0xff
		int16_1 = (int16 >> 8) & 0xff
	else:
		int16 = int16_0<<8 + int16_1
		int16 = (int16 + num) & 0xffff
		
		int16_1 = int16 & 0xff
		int16_0 = (int16 >> 8) & 0xff
		
	buf[index] = int16_0
	buf[index+1] = int16_1
	fix_len = len(buf) - buf_len
	return buf, fix_len
	
def mutate_case_8(buf):  # SUB_WORD_VALUE	
	buf_len = len(buf)
	if(buf_len < 4):
		return buf, 0
	index = UR(buf_len - 3)  # index
	int32_0 = buf[index]
	int32_1 = buf[index+1]
	int32_2 = buf[index+2]
	int32_3 = buf[index+3]
	num = 1 + UR(35)
	
	if(UR(2)):
		int32 = int32_0 + int32_1 << 8 + int32_2 << 16 + int32_3 << 24
		int32 = (int32 - num) & 0xffffffff
		
		int32_0 = int32 & 0xff
		int32_1 = (int32 >> 8) & 0xff
		int32_2 = (int32 >> 16) & 0xff
		int32_3 = (int32 >> 24) & 0xff
	else:
		int32 = int32_3 + int32_2 << 8 + int32_1 << 16 + int32_0 << 24
		int32 = (int32 - num) & 0xffffffff
		
		int32_3 = int32 & 0xff
		int32_2 = (int32 >> 8) & 0xff
		int32_1 = (int32 >> 16) & 0xff
		int32_0 = (int32 >> 24) & 0xff
		
	buf[index] = int32_0
	buf[index+1] = int32_1
	buf[index+2] = int32_2
	buf[index+3] = int32_3
	fix_len = len(buf) - buf_len
	return buf, fix_len
	
def mutate_case_9(buf):  # SUB_WORD_VALUE	
	buf_len = len(buf)
	if(buf_len < 4):
		return buf, 0
	index = UR(buf_len - 3)  # index
	int32_0 = buf[index]
	int32_1 = buf[index+1]
	int32_2 = buf[index+2]
	int32_3 = buf[index+3]
	num = 1 + UR(35)
	
	if(UR(2)):
		int32 = int32_0 + int32_1 << 8 + int32_2 << 16 + int32_3 << 24
		int32 = (int32 + num) & 0xffffffff
		
		int32_0 = int32 & 0xff
		int32_1 = (int32 >> 8) & 0xff
		int32_2 = (int32 >> 16) & 0xff
		int32_3 = (int32 >> 24) & 0xff
	else:
		int32 = int32_3 + int32_2 << 8 + int32_1 << 16 + int32_0 << 24
		int32 = (int32 + num) & 0xffffffff
		
		int32_3 = int32 & 0xff
		int32_2 = (int32 >> 8) & 0xff
		int32_1 = (int32 >> 16) & 0xff
		int32_0 = (int32 >> 24) & 0xff
		
	buf[index] = int32_0
	buf[index+1] = int32_1
	buf[index+2] = int32_2
	buf[index+3] = int32_3
	fix_len = len(buf) - buf_len
	return buf, fix_len
	
def mutate_case_10(buf):
	buf_len = len(buf)
	buf[UR(buf_len)] ^= 1 + UR(255)
	fix_len = len(buf) - buf_len
	return buf, fix_len

def mutate_case_11(buf):   # Insert bytes at random position (40%) 
	buf_len = len(buf)
	if(buf_len < 4):
		return buf, 0
	index = UR(buf_len - 1)
	insert_byte_len = int(0.4 * buf_len)
	inserted_byte = bytearray(os.urandom(insert_byte_len))
	buf[index:index] = inserted_byte
	fix_len = len(buf) - buf_len
	return buf, fix_len

def mutate_case_12(buf):   # Remove bytes at random position (25%) 
	buf_len = len(buf)
	if(buf_len < 10):
		return buf, 0
	index = UR(buf_len - 1)
	delete_bytes_len = int(0.25 * buf_len)
	buf[index:index + random.randint(0, delete_bytes_len)] = b''
	fix_len = len(buf) - buf_len
	return buf, fix_len

def mutate_case_13(buf):   # Clone bytes at random position (75%) 
	buf_len = len(buf)
	if(buf_len < 4):
		return buf, 0
	index = UR(buf_len - 1)
	clone_bytes_len = int(0.75 * buf_len)
	if buf_len - index < 1:
		clone_bytes_len = buf_len
	buf[index:index] = buf[index:clone_bytes_len]
	fix_len = len(buf) - buf_len
	return buf, fix_len

def mutate_case_14(buf):   # Overwrite bytes with 50% randomly generated extra bytes
	buf_len = len(buf)
	if(buf_len < 10):
		return buf, 0
	overwrite_byte_len = int(0.5 * buf_len)
	overwrite_byte = bytearray(os.urandom(overwrite_byte_len))
	start_index = random.randint(0, buf_len - overwrite_byte_len)
	buf[start_index:start_index + overwrite_byte_len] = overwrite_byte
	fix_len = len(buf) - buf_len
	return buf, fix_len

def mutate_case_15(buf):   # Overwrite bytes with a randomly selected part (40%)
	buf_len = len(buf)
	if(buf_len < 10):
		return buf, 0
	overwrite_bytes_len = int(0.4 * buf_len)
	index = random.randint(0, buf_len - overwrite_bytes_len)
	start_index = random.randint(0, buf_len - overwrite_bytes_len)
	overwrite_bytes = buf[index:index + overwrite_bytes_len]
	buf[start_index:start_index + overwrite_bytes_len] = overwrite_bytes
	fix_len = len(buf) - buf_len
	return buf, fix_len



# Structure Mutation Operation
# RepeatField Node Mutate
def mutate_case_structure_clone(node):     # Clone and Insert a structure data (RepeatField) 
	nodeData = random.choice(node.data)
	lens, data, _ = node.type.field.from_raw(None, nodeData.rebuild())
	node.data.append(data)
	return lens

def mutate_case_structure_sub(node):       # Remove a structure data randomly (RepeatField) 
	if (len(node.data) < 4):
		return 0
	nodeData = random.choice(node.data)
	lens, _, _ = node.type.field.from_raw(None, nodeData.rebuild())
	node.data.remove(nodeData)
	return -lens

#TODO: need to fix
def mutate_case_structure_add(node, add_node):       # Add a structure data (RepeatField) 
	if (len(add_node.data) < 1):
		return 0
	addNodeData = random.choice(add_node.data)
	if type(addNodeData) == int:
		return 0
	lens, data, _ = add_node.type.field.from_raw(None, addNodeData.rebuild())
	node.data.append(data)
	return lens


# RepeatField subfield Int Mutate
def muate_case_int_add(node):              # Add a random int value (0 ~ 10)
	node_len = len(node.data)
	num = random.randint(1, 10)
	for _ in range(num):
		random_value = random.randint(0, 10)
		random_index = random.randint(0, node_len)
		node.data.insert(random_index, random_value)
	fix_len = len(node.data) - node_len
	return fix_len

def mutate_case_int_clone(node):          # Clone and Insert a random int value 
	node_len= len(node.data)
	nodeData = random.choice(node.data)
	index = random.randint(0, node_len)
	node.data.insert(index, nodeData)
	fix_len = len(node.data) - node_len
	return fix_len

def mutate_case_int_sub(node):            # Remove a random int value
	node_len = len(node.data)
	if (len(node.data) < 4):
		return 0
	node.data.remove(random.choice(node.data))
	fix_len = len(node.data) - node_len
	return fix_len



# RepeatField subfield (UnsignedLeb128Field, SignedLeb128Field, UIntNField) Mutate
def mutate_case_unsignedint_replace(node):      # Replace with a random unsignedint value (0 ~ 2 ^ 7)
	node_len = len(node.data)
	value = random.randint(0, 2 ^ 7)
	index = random.randint(0, node_len - 1)
	node.data[index] = value
	return 0
	
def mutate_case_signedint_replace(node):        # Replace with a random signedint value (-1 ~ 2 ^ 7)
	node_len = len(node.data)
	value = random.randint(-1, 2 ^ 7)
	index = random.randint(0, node_len - 1)
	node.data[index] = value
	return 0

def mutate_case_uintn_replace(node):        # Replace with a random uintn value (0 ~ 2 ^ 8)
	node_len= len(node.data)
	value = random.randint(0, 2 ^ 8)
	index = random.randint(0, node_len - 1)
	node.data[index] = value
	return 0



# UnsignedLeb128Field Mutate
def mutate_case_unsignedlebint_replace(node):   # Replace with a random uintn value (0 ~ 2 ^ 7)
	value = random.randint(0, 2 ^ 7)
	node.data = value
	return 0

# SignedLeb128Field Mutate
def mutate_case_signedlebint_replace(node):     # Replace with a random uintn value (0 ~ 2 ^ 7)
	value = random.randint(-1, 2 ^ 7)
	node.data = value
	return 0

# UIntNField Mutate
def mutate_case_uintnfield_replace(node):      # Replace with a random uintn value (0 ~ 2 ^ 8)
	value = random.randint(0, 2 ^ 8)
	node.data = value
	return 0



# Instruction Mutation Operation
# You may use the LLM to do the instruction mutation
# Instruction mutation operation can be found at wasm_insn_op.py



# Mutator Operation
if __name__ == "__main__":
	r = UR(100)
	
