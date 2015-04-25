#!/usr/bin/env python2
"""Kicad library file generator for the machine readable MCU description files."""

__author__ = 'esdentem'

import csv
import re


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


def lib_head():
    print "EESchema-Library Version 2.3"
    print "#encoding utf-8"


def lib_foot():
    print "#"
    print "#End Library"


def symbol_head(name, footprint):
    print "#"
    print "# ", name
    print "#"
    print "DEF %s U 0 50 Y Y 1 F N" % (name)
    print "F0 \"U\" 0 100 50 H V C CNN"
    print "F1 \"%s\" 0 -100 50 H V C CNN" % (name)
    print "F2 \"%s\" 0 -200 50 H V C CIN" % (footprint)
    print "F3 \"\" 0 0 50 H V C CNN"
    print "DRAW"


def symbol_frame(startx, starty, endx, endy):
    print "S %s %s %s %s 0 1 10 N" % (startx, starty, endx, endy)


def symbol_pin(name, num, x, y, dir):
    print "X %s %s %s %s 300 %s 50 50 1 1 I" % (name, num, x, y, dir)


def symbol_bank(pins, x_offset, y_offset, spacing, dir):
    counter = 0
    for pin in sorted(pins, key=lambda p: p['Pin_name']):
        name = pin['Pin_name']
        if pin['Pin_functions'] != []:
            name += "/" + '/'.join(pin['Pin_functions'])
        if dir == 'R' or dir == 'L':
            symbol_pin(name, pin['Pin'], x_offset, y_offset - (counter * spacing), dir)
        elif dir == 'U' or dir == 'D':
            symbol_pin(name, pin['Pin'], x_offset, y_offset - (counter * spacing), dir)
        else:
            print "Unknown direction!!!"
        counter += 1


def symbol_foot():
    print "ENDDRAW"
    print "ENDDEF"


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


def lib_symbol(name, all_data, footprint):
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
    symbol_head(name, footprint)

    height = vertical_height(banks)
    v_offset = height / 2
    v_offset -= v_offset % 100

    width = 7000
    h_offset = width / 2

    symbol_frame(-h_offset + 300, v_offset + 100, h_offset - 300, v_offset - height - 100)

    # Plot all the banks except VSS and VDD
    dir = 'R'
    counter = 0
    for bank in sorted(banks.keys()):
        if not (bank == "VSS" or bank == "VDD"):
            if dir == 'R':
                symbol_bank(banks[bank], -h_offset, v_offset + (-100 * 17) * counter, 100, dir)
                dir = 'L'
            elif dir == 'L':
                symbol_bank(banks[bank], h_offset, v_offset + (-100 * 17) * counter, 100, dir)
                dir = 'R'
                counter += 1

    # If the last bank was on the left side then the VDD bank would go on the right side in theory,
    # this is not what we want though, we want both VDD and VSS to be on the same height, so we are moving down
    # to the next bank row
    if dir == 'L':
        counter += 1

    symbol_bank(banks['VDD'], -h_offset, v_offset + (-100 * 17) * counter, 100, 'R')
    symbol_bank(banks['VSS'],  h_offset, v_offset + (-100 * 17) * counter, 100, 'L')

    symbol_foot()

# Open pin definition file
f = open('../compact/stm32-pinout-STM32F437xx-and-STM32F439xx.txt', 'r')

# Read in as a tab separated CSV
r = csv.DictReader(f, delimiter='\t')

# Find footprints
footprints = []
for key in r.fieldnames:
    if re.match("(.*QFP.*)|(.*BGA.*)|(.*WLCSP.*)", key):
        footprints.append(key)

definitions = []
for line in r:
    definitions.append(line)

f.close()

# print(footprints)

lib_head()
for footprint in footprints:
    lib_symbol('STM32F437xx-'+footprint, definitions, footprint)
lib_foot()

#for row in r:
#    print(row['LQFP100'])
