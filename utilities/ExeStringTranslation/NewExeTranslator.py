#!/usr/bin/env python3.4

'''
File: ExeTranslator.py
Date: 8/8/2015
Author: Elyk
Purpose: Rip out the JPN text into a csv, then reinsert along with ENG
Modified: 7/5/2016 by Dabomstew for YnK
'''

import csv
import sys
import io
import time

def readWord(bin, addr):
	return bin[addr] | (bin[addr+1]<<8)
	
def readLong(bin, addr):
	return readWord(bin, addr) | (readWord(bin, addr+2)<<16)
	
def writeWord(bin, addr, value):
	bin[addr] = value & 0xFF
	bin[addr+1] = (value >> 8) & 0xFF
	
def writeLong(bin, addr, value):
	writeWord(bin, addr, value&0xFFFF)
	writeWord(bin, addr+2, (value>>16)&0xFFFF)

# read exe for constants
exeFile = open("tpdp.exe",'rb')
exeBin = bytearray(exeFile.read())
exeFile.close()

RDATA_START = readLong(exeBin, 0x234) # 1.103: 0x3C0A00
DATA_START = readLong(exeBin, 0x25C) # 1.103: 0x44A000
JP_OFFSET = readLong(exeBin, 0x22C) - RDATA_START + 0x400000 # 1.103: 0x401600
CODE_START = readLong(exeBin, 0x20C) # 1.103: 0x400 (never changes)
CODE_END = CODE_START + readLong(exeBin, 0x200) # 1.103: 0x3C09AB


#lists
tableAddr = []
tableJpn = []
tableEng = []
illegalFirstChars = [i for i in range(0xF0, 0xFF)]
illegalFirstChars.append(0x80)
illegalFirstChars.append(0xA0)

validOpcodes = [ 0x68, 0xBE, 0xBF ] # 0x68 = push, 0xBE = mov esi, 0xBF = mov edi,

###############################################
# Name: extractMachine()
# Description: Runs through the bin buffer and pulls
#   out all the non 0 bytes as strings with locations
###############################################
def extractMachine(bin,offset):
	index = 0
	startIndex = 0
	length = len(bin)
	while index < length:
		if bin[index] == 0:
			#print("checking "+hex(index))
			startIndex = max(startIndex, index-0x80)
			# handle previous string
			while startIndex < index-1:
				searchResults = []
				if startIndex % 4 == 0 and isValidString(bin[startIndex:index]):
					# done
					try:
						tablestr = bin[startIndex:index].decode("shift-jis")
						tableJpn.append(tablestr.replace("\r\n", "[WNEWLINE]").replace("\n", "[NEWLINE]").replace("\r", "[MNEWLINE]"))
						tableEng.append("")
						tableAddr.append(startIndex+offset)
						break
					except:
						pass
				startIndex += 1
					
			startIndex = index + 1
			valid = True
		index += 1
	#Do the output
	with open('tpdp_in.csv', 'w', encoding='utf-8', newline='') as csvfile:
		spamwriter = csv.writer(csvfile, dialect='excel')
		for i in range(0, len(tableAddr)):
			spamwriter.writerow([tableAddr[i], tableJpn[i], tableEng[i]])

def isValidString(strBytes):
	# 1st check: no invalid characters
	for index in range(0, len(strBytes)):
		if (strBytes[index] < 0x20 and strBytes[index] != 0x0D and strBytes[index] != 0x0A and strBytes[index] != 0x09):
			return False
	# 2nd check: needs at least one SJIS japanese symbol (why TL otherwise?)
	for index in range(0, len(strBytes)):
		if strBytes[index] >= 0x81 and strBytes[index] <= 0xEF and strBytes[index] != 0xA0:
			return True
	# no SJIS symbol found
	return False
	
###############################################
# Name: insertMachine()
# Description: Push the translated elements into
#   the exe and adjust the correct pointers
###############################################
def insertMachine(exeBin):

	# get stuff from the exe
	numSections = readWord(exeBin, 0x106)
	overallRamBase = readLong(exeBin, 0x134)
	vAlign = readLong(exeBin, 0x138)
	fAlign = readLong(exeBin, 0x13C)
	
	# read the location of the last section as it stands
	lastSectionOffset = 0x1F8 + (numSections-1)*0x28
	lastVOffset = readLong(exeBin, lastSectionOffset + 0xC)
	lastFOffset = readLong(exeBin, lastSectionOffset + 0x14)
	lastPSize = readLong(exeBin, lastSectionOffset + 0x10)
	
	# work out where to place the new section for translated strings
	newVOffset = padToAlign(lastVOffset + lastPSize, vAlign)
	newFOffset = padToAlign(lastFOffset + lastPSize, fAlign)
	
	EN_OFFSET = newVOffset + overallRamBase
	
	log = open("tpdp_log.txt", 'w', encoding='utf-8')
	#number of successful writes
	writeCount = 0
	writeOffset = 0
	# empty buffer to store translated strings for now
	buf = [0] * 1000000
	#loop through the table of addresses
	for index in range(0, len(tableAddr)):
			
			#clear search results
			searchResults = []
			#if there is something in the translation table
			if (len(tableEng[index]) > 0):
				# direct mode?
				if tableEng[index].startswith("[DIRECT]"):
					tableEng[index] = tableEng[index][8:]
					# write the new string directly over the old one
					outStr = tableEng[index].encode('shift-jis')
					exeBin[tableAddr[index]:tableAddr[index]+len(outStr)] = outStr
					exeBin[tableAddr[index]+len(outStr)] = 0
					# done
					log.write(str(tableAddr[index]) + " : direct replacement done.\n")
					continue
				log.write(str(tableAddr[index]) + " ")
				searchResults = pointerSearch(tableAddr[index], exeBin)
				#Error -2, not found
				if len(searchResults) == 0:
					log.write("Address not found, skipping.\n")
				#Success
				else:
					if len(searchResults) > 1:
						log.write("WARN: Multiple pointers found; ")
					#do a write
					outStr = tableEng[index].encode('shift-jis')
					newAddr = writeOffset
					buf[writeOffset:writeOffset+len(outStr)] = outStr
					buf[writeOffset+len(outStr)] = 0
					writeOffset += len(outStr) + 1
					# each string offset must be padded to 4bytes
					writeOffset = (writeOffset + 3) & ~3
					
					#edit the old pointer(s)
					for seekAddr in searchResults:
						if seekAddr == 0:
							continue # lol
						opcode = exeBin[seekAddr-1]
						if opcode not in validOpcodes:
							log.write("ERR: unknown opcode before pointer %02X (offset = %X / %X)" % (opcode, seekAddr-1, seekAddr-1-0x400+0x401000))
						else:
							exeBin[seekAddr:seekAddr+4] = makePointer(newAddr + EN_OFFSET)
					log.write("Performed the write successfully\n")
					#update the write count
					writeCount += 1
				#missing translation
			else:
				#log.write("No translation\n")
				pass
	log.close()
	
	# OK, make a new EXE file. The size of the new section = current value of writeOffset. Calculate padded size.
	fSizeToInsert = padToAlign(writeOffset, fAlign)
	vSizeToInsert = padToAlign(writeOffset, vAlign)
	
	# Make the new exe file and copy in the old data + the new strings
	newExe = bytearray([0] * (newFOffset + fSizeToInsert))
	newExe[0:len(exeBin)] = exeBin
	newExe[newFOffset:newFOffset+fSizeToInsert] = buf[0:fSizeToInsert]
	
	# Update exe header stuff
	writeWord(newExe, 0x106, numSections + 1)
	writeLong(newExe, 0x150, newVOffset + vSizeToInsert)
	
	# Write new section header
	sectionName = ".tldata".encode("shift-jis")
	newSecHAddress = 0x1F8 + numSections * 0x28
	newExe[newSecHAddress:newSecHAddress+len(sectionName)] = sectionName
	writeLong(newExe, newSecHAddress + 0x8, fSizeToInsert)
	writeLong(newExe, newSecHAddress + 0xC, newVOffset)
	writeLong(newExe, newSecHAddress + 0x10, fSizeToInsert)
	writeLong(newExe, newSecHAddress + 0x14, newFOffset)
	writeLong(newExe, newSecHAddress + 0x24, 0x40000040)
	
	return newExe
	
def padToAlign(value, align):
	if value == 0:
		return 0
		
	return ((value - 1) & (~(align - 1))) + align
				

###############################################
# Name: listPopulator()
# Description: Reads in from the input CSV and
#   populates the three lists
###############################################
def listPopulator():
	#open the input csv
	inputCSV = open("tpdp_in.csv", 'r', encoding='utf-8')
	#handle the basic csv parsing into a list
	outCSV=(line for line in csv.reader(inputCSV, dialect='excel'))
	#break into the actual lists
	for line in outCSV:
		try:
			tableAddr.append(int(line[0]))
			tableJpn.append(line[1])
			tableEng.append(line[2])
		except:
			print("Error Reading")
	
def pointerSearch(addr, bin):
	#adjust the address to the proper offset
	addr += JP_OFFSET
	
	# calculate the bits to search for
	addrBits = makePointer(addr)
	
	searchResults = []
	
	# new search method adapted from http://stackoverflow.com/questions/2250633/python-find-a-list-within-members-of-another-listin-order
	first = addrBits[0]
	rest = bytearray(addrBits[1:])
	pos = CODE_START
	endpos = CODE_END - 3
	
	while pos < endpos:
		pos = bin.index(first, pos) + 1
		if pos <= endpos and bin[pos:pos+3] == rest:
			searchResults.append(pos-1)		
	
	return searchResults

def makePointer(addr):
	# turn an address into a little-endian 4-byte pointer
	return [((addr >> (i*8)) & 0xFF) for i in range(0, 4)]
		
	
###############################################
# Name: performExtract()
# Description: Launch the extraction operation
###############################################
def performExtract():
	#start the extract machine
	extractMachine(exeBin[RDATA_START:DATA_START],RDATA_START)

###############################################
# Name: performInsert()
# Description: Launch the insertion operation
###############################################
def performInsert():
	#open the input csv and populate the lists
	listPopulator()
	#start the insert machine
	newExe = insertMachine(exeBin)
	exeFile = open("tpdp_out.exe", "wb")
	exeFile.write(newExe)
	exeFile.close()
	
###############################################
# Name: main()
# Description: 
###############################################
def main():
	#performExtract()
	performInsert()
	print("Complete")		

if __name__ == "__main__":
    main()