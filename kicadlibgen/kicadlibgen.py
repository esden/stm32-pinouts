#!/usr/bin/env python2
"""Kicad library file generator for the machine readable MCU description files."""

__author__ = 'esdentem'

import csv
import re
import StringIO
import os
import glob


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


def symbol_head(f, names, footprint):
    print >>f, "#"
    print >>f, "# " + names[0]
    print >>f, "#"
    print >>f, "DEF " + names[0] + " U 0 50 Y Y 1 F N"
    print >>f, "F0 \"U\" 0 100 50 H V C CNN"
    print >>f, "F1 \"" + names[0] + "\" 0 -100 50 H V C CNN"
    print >>f, "F2 \"" + footprint + "\" 0 -200 50 H V C CIN"
    print >>f, "F3 \"\" 0 0 50 H V C CNN"
    if len(names) > 1:
        print >>f, "ALIAS",
        for name in names[1:]:
            f.write(" " + name)
        print >>f, "\n",
    print >>f, "DRAW"


def symbol_frame(f, startx, starty, endx, endy):
    print >>f, "S %s %s %s %s 0 1 10 N" % (startx, starty, endx, endy)


def symbol_pin(f, name, num, x, y, direction):
    print >>f, "X %s %s %s %s 300 %s 50 50 1 1 I" % (name, num, x, y, direction)


def symbol_bank(f, pins, x_offset, y_offset, spacing, direction):
    counter = 0

    def pin_sort_key(pin_key):
        m = re.match("(\D*)(\d*)", pin_key['Pin_name'])
        return '{}{:0>3}'.format(m.group(1), m.group(2))

    for pin in sorted(pins, key=pin_sort_key):
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


def symbol_pin_height(banks):
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

    left_height = 17 * (len(left_banks) - 1)
    left_height += len(banks[left_banks[-1]])
    right_height = 17 * (len(right_banks) - 1)
    right_height += len(banks[right_banks[-1]])

    full_height = max(left_height, right_height) + 1 + max(len(banks['VSS']), len(banks['VDD']))

    return full_height * 100


def symbol_body_width(pins):
    max_char_count = 0;

    for pin in pins:
        name = pin['Pin_name']
        if pin['Pin_functions']:
            name += "/" + '/'.join(pin['Pin_functions'])
        max_char_count = max(len(name), max_char_count)

    return 55 * (max_char_count * 2 + 2)


def pin_append_combine(footprint, pin_list, new_pin):
    # Extract the record with the same Pin number from the pin_list if available
    pin = None
    pin_index = 0
    for p in pin_list:
        if p['Pin'] == new_pin['Pin']:
            pin = p
            break
        pin_index += 1

    if pin:
        old_functions = list(pin['Pin_functions'])
        # If the new pin's name is different than the old we add it's name to the function list
        if pin['Pin_name'] != new_pin['Pin_name']:
            pin['Pin_functions'].append(new_pin['Pin_name'])
        # If the new pin has some additional functions we add that too to the old pins function list.
        for function in new_pin['Pin_functions']:
            if function not in pin['Pin_functions']:
                pin['Pin_functions'].append(function)
        # Merge pin type
        old_t = pin['Pin_type']
        new_t = new_pin['Pin_type']
        # If they are different then we just assume the result will be I/O (Yes I know that might be wrong but ...)
        if old_t != new_t:
            pin["Pin_type"] = "I/O"
        pin_list[pin_index] = pin
        # Report the merging action
        print "Merge " + footprint + "\tpin\t", pin['Pin'], \
            "\tName:", pin['Pin_name'], \
            "\tType:", old_t, "+", new_t, "=", pin['Pin_type'], \
            "\tFunc:", old_functions, "+", new_pin['Pin_functions'],
        if pin['Pin_name'] != new_pin['Pin_name']:
            print "+", new_pin['Pin_name'],
        print "=", pin['Pin_functions']
    else:
        pin_list.append(new_pin)


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
            pin_append_combine(footprint,
                               data, {'Pin': pin,
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

    height = symbol_pin_height(banks)
    v_offset = height / 2
    v_offset -= v_offset % 100

    width = symbol_body_width(data)
    h_offset = width / 2
    h_offset += h_offset % 100

    symbol_frame(f, -h_offset + 300, v_offset + 100, h_offset - 300, v_offset - height - 0)

    # Plot all the banks except VSS and VDD
    direction = 'R'
    counter = 0
    last_left_bank_height = 0
    last_right_bank_height = 0
    for bank in sorted(banks.keys()):
        if not (bank == "VSS" or bank == "VDD"):
            if direction == 'R':
                last_left_bank_height = len(banks[bank])
                last_right_bank_height = 0
                symbol_bank(f, banks[bank], -h_offset, v_offset + (-100 * 17) * counter, 100, direction)
                direction = 'L'
            elif direction == 'L':
                last_right_bank_height = len(banks[bank])
                symbol_bank(f, banks[bank], h_offset, v_offset + (-100 * 17) * counter, 100, direction)
                direction = 'R'
                counter += 1

    # If the last bank was on the left side then the VDD bank would go on the right side in theory,
    # this is not what we want though, we want both VDD and VSS to be on the same height, so we are moving down
    # to the next bank row
    if direction == 'R':
        counter -= 1

    last_bank_offset = -100 * (max(last_left_bank_height, last_right_bank_height) + 1)

    symbol_bank(f, banks['VDD'], -h_offset, v_offset + (-100 * 17) * counter + last_bank_offset, 100, 'R')
    symbol_bank(f, banks['VSS'],  h_offset, v_offset + (-100 * 17) * counter + last_bank_offset, 100, 'L')

    symbol_foot(f)


def symbols_from_file(source_filename, target_file):
    # Open pin definition file
    print "Loading source file: " + source_filename
    sourcef = None
    try:
        sourcef = open(source_filename, 'r')
    except:
        print "failed to open source file"
        print "Exiting!"
        exit(1)
    # Extract meta description section
    metaf = StringIO.StringIO()
    for line in sourcef:
        if re.match("^ *#", line):
            print line,
            # Nothing to do just ignore
        elif re.match("^----", line):
            # End of metadata block
            break
        else:
            metaf.write(line)

    # Read in metadata as a tab separated CSV
    metaf.seek(0)
    metadata_csv = csv.DictReader(metaf, delimiter='\t')

    metadata = {}
    for line in metadata_csv:
        metadata[line['Footprint']] = line['Names'].split(' ')

    # Read pin descriptions in as a tab separated CSV
    pin_csv = csv.DictReader(sourcef, delimiter='\t')

    # Find footprints
    footprints = []
    for key in pin_csv.fieldnames:
        if re.match("(.*QFP.*)|(.*BGA.*)|(.*WLCSP.*)", key):
            footprints.append(key)

    # Extract pin definitions
    definitions = []
    for line in pin_csv:
        definitions.append(line)

    sourcef.close()
    for footprint in footprints:
        if footprint not in metadata:
            print "Could not find metadata for the '" + footprint + "' footprint."
            print "Exiting!"
            exit(1)
        lib_symbol(target_file, metadata[footprint], definitions, footprint)


# Open library file
lib_filename = "../lib/stm32.lib"

print "Opening '" + lib_filename + "' as our target library file"

lib_dir = os.path.dirname(lib_filename)

try:
    os.stat(lib_dir)
except:
    os.mkdir(lib_dir)

try:
    libf = open(lib_filename, 'w')
except:
    print "could not open target library file"
    print "Exiting!"
    exit(1)

source_dir = "../compact"
source_filenames = glob.glob(source_dir + "/*")

lib_head(libf)
for source_filename in source_filenames:
    symbols_from_file(source_filename, libf)
lib_foot(libf)

libf.close()

