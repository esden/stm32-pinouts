#!/usr/bin/env python2
"""Kicad library file generator for the machine readable MCU description files."""

__author__ = 'esdentem'

import csv
import re
import StringIO
import os


def pretty_print_banks(banks):
    bank_names = sorted(banks.keys())
    for bank in bank_names:
        print "Bank: %s" % bank
        print "\tPin\tName\tType\tStruct\tFunc"
        for pin in banks[bank]:
            print "\t%s\t%s\t%s\t%s\t%s" % (pin['Pin'],
                                            pin['Pin_name'],
                                            pin['Pin_type'],
                                            pin['Pin_structure'],
                                            pin['Pin_functions'])


def lib_head(f):
    print >>f, 'EESchema-Library Version 2.3\n'
    print >>f, '#encoding utf-8'


def lib_foot(f):
    print >>f, '#'
    print >>f, '#End Library'


def symbol_head(f, name, footprint):
    print >>f, "#"
    print >>f, "# " + name
    print >>f, "#"
    print >>f, "DEF " + name + " U 0 50 Y Y 1 F N"
    print >>f, "F0 \"U\" 0 100 50 H V C CNN"
    print >>f, "F1 \"" + name + "\" 0 -100 50 H V C CNN"
    print >>f, "F2 \"" + footprint + "\" 0 -200 50 H V C CIN"
    print >>f, "F3 \"\" 0 0 50 H V C CNN"
    print >>f, "DRAW"


def symbol_frame(f, startx, starty, endx, endy):
    print >>f, "S %s %s %s %s 0 1 10 N" % (startx, starty, endx, endy)


def symbol_pin(f, name, num, x, y, direction):
    print >>f, "X %s %s %s %s 300 %s 50 50 1 1 I" % (name, num, x, y, direction)


def symbol_bank(f, pins, x_offset, y_offset, spacing, direction):
    counter = 0
    for pin in sorted(pins, key=lambda p: p['Pin_name']):
        name = pin['Pin_name']
        if pin['Pin_functions']:
            name += "/" + '/'.join(pin['Pin_functions'])
        if direction == 'R' or direction == 'L':
            symbol_pin(f, name, pin['Pin'], x_offset, y_offset - (counter * spacing), direction)
        elif direction == 'U' or direction == 'D':
            symbol_pin(f, name, pin['Pin'], x_offset, y_offset - (counter * spacing), direction)
        else:
            print "Unknown direction!!!"
        counter += 1


def symbol_foot(f):
    print >>f, "ENDDRAW"
    print >>f, "ENDDEF"


def vertical_height(banks):
    left_banks = []
    right_banks = []

    side = 'L'
    for bank in sorted(banks.keys()):
        if not (bank == 'VSS' or bank == 'VDD'):
            if side == 'L':
                left_banks.append(bank)
                side = 'R'
            elif side == 'R':
                right_banks.append(bank)
                side = 'L'

    left_banks.append('VDD')
    right_banks.append('VSS')

    left_height = (100 * 17) * (len(left_banks) - 1)
    left_height += 100 * (len(banks[left_banks[-1]]) - 1)
    right_height = (100 * 17) * (len(right_banks) - 1)
    right_height += 100 * (len(banks[right_banks[-1]]) -1)
    return max(left_height, right_height)


def lib_symbol(f, name, all_data, footprint):
    data = []
    # Filter data for the specific footprint
    for row in all_data:
        if not re.match("(^-$)|(^NC.*$)", row[footprint]):
            pin = row[footprint]
            pin_name = row['Pin_name']
            if row['Alternate_functions']:
                function_str = row['Alternate_functions']
                functions = function_str.split(' ')
            else:
                functions = []
            pin_type = row['Pin_type']
            pin_structure = row['IO_structure']
            data.append({'Pin': pin,
                         'Pin_name': pin_name,
                         'Pin_functions': functions,
                         'Pin_type': pin_type,
                         'Pin_structure': pin_structure})
    # Group pins into banks
    banks = {'OTHER': [], 'VSS': [], 'VDD': []}
    for row in data:
        pin_name = row["Pin_name"]
        if re.match("VSS.?", pin_name):
            banks['VSS'].append(row)
        elif re.match("VDD.?", pin_name):
            banks['VDD'].append(row)
        else:
            m = re.match("P([A-Z])\d+", pin_name)
            if m:
                if m.group(1) in banks:
                    banks[m.group(1)].append(row)
                else:
                    banks[m.group(1)] = [row]
            else:
                banks['OTHER'].append(row)
    # pretty_print_banks(banks)
    symbol_head(f, name, footprint)

    height = vertical_height(banks)
    v_offset = height / 2
    v_offset -= v_offset % 100

    width = 7000
    h_offset = width / 2

    symbol_frame(f, -h_offset + 300, v_offset + 100, h_offset - 300, v_offset - height - 100)

    # Plot all the banks except VSS and VDD
    direction = 'R'
    counter = 0
    for bank in sorted(banks.keys()):
        if not (bank == "VSS" or bank == "VDD"):
            if direction == 'R':
                symbol_bank(f, banks[bank], -h_offset, v_offset + (-100 * 17) * counter, 100, direction)
                direction = 'L'
            elif direction == 'L':
                symbol_bank(f, banks[bank], h_offset, v_offset + (-100 * 17) * counter, 100, direction)
                direction = 'R'
                counter += 1

    # If the last bank was on the left side then the VDD bank would go on the right side in theory,
    # this is not what we want though, we want both VDD and VSS to be on the same height, so we are moving down
    # to the next bank row
    if direction == 'L':
        counter += 1

    symbol_bank(f, banks['VDD'], -h_offset, v_offset + (-100 * 17) * counter, 100, 'R')
    symbol_bank(f, banks['VSS'],  h_offset, v_offset + (-100 * 17) * counter, 100, 'L')

    symbol_foot(f)

# Open pin definition file
source_filename = "../compact/stm32-pinout-STM32F437xx-and-STM32F439xx.txt"
sourcef = None
try:
    sourcef = open(source_filename, 'r')
except:
    print "failed to open source file"
    exit(1)

# Open library file
lib_filename = "../lib/stm32.lib"
lib_dir = os.path.dirname(lib_filename)

try:
    os.stat(lib_dir)
except:
    os.mkdir(lib_dir)

libf = open(lib_filename, 'w')

# Extract meta description section
metaf = StringIO.StringIO()
for line in sourcef:
    if re.match("^ *#", line):
        print "quoted line"
    elif re.match("^----", line):
        print "end of meta block"
        break
    else:
        print "Line: %s" % line
        metaf.write(line)

# Read in as a tab separated CSV
r = csv.DictReader(sourcef, delimiter='\t')

# Find footprints
footprints = []
for key in r.fieldnames:
    if re.match("(.*QFP.*)|(.*BGA.*)|(.*WLCSP.*)", key):
        footprints.append(key)

# Extract pin definitions
definitions = []
for line in r:
    definitions.append(line)

sourcef.close()

# print(footprints)

lib_head(libf)
for footprint in footprints:
    lib_symbol(libf, 'STM32F437xx-'+footprint, definitions, footprint)
lib_foot(libf)

#for row in r:
#    print(row['LQFP100'])
