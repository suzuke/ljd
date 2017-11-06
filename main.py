#!/usr/bin/python3
#
# The MIT License (MIT)
#
# Copyright (c) 2013 Andrian Nord
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import csv
import os
import sys
from time import time

import ljd.ast.builder
import ljd.ast.locals
import ljd.ast.mutator
import ljd.ast.slotworks
import ljd.ast.unwarper
import ljd.ast.validator
import ljd.lua.writer
import ljd.pseudoasm.writer
import ljd.rawdump.parser


def dump(name, obj, level=0):
    indent = level * '\t'

    if name is not None:
        prefix = indent + name + " = "
    else:
        prefix = indent

    if isinstance(obj, (int, float, str)):
        print(prefix + str(obj))
    elif isinstance(obj, list):
        print(prefix + "[")

        for value in obj:
            dump(None, value, level + 1)

        print(indent + "]")
    elif isinstance(obj, dict):
        print(prefix + "{")

        for key, value in obj.items():
            dump(key, value, level + 1)

        print(indent + "}")
    else:
        print(prefix + obj.__class__.__name__)

        for key in dir(obj):
            if key.startswith("__"):
                continue

            val = getattr(obj, key)
            dump(key, val, level + 1)


def decompile_lua(fin):

    header, prototype = ljd.rawdump.parser.parse(fin)

    if not prototype:
        return 1

    # TODO: args
    # ljd.pseudoasm.writer.write(sys.stdout, header, prototype)

    ast = ljd.ast.builder.build(prototype)

    assert ast is not None

    ljd.ast.validator.validate(ast, warped=True)

    ljd.ast.mutator.pre_pass(ast)

    # ljd.ast.validator.validate(ast, warped=True)

    ljd.ast.locals.mark_locals(ast)

    # ljd.ast.validator.validate(ast, warped=True)

    ljd.ast.slotworks.eliminate_temporary(ast)

    # ljd.ast.validator.validate(ast, warped=True)

    if True:
        ljd.ast.unwarper.unwarp(ast)

        # ljd.ast.validator.validate(ast, warped=False)

        if True:
            ljd.ast.locals.mark_local_definitions(ast)

            # ljd.ast.validator.validate(ast, warped=False)

            ljd.ast.mutator.primary_pass(ast)

            ljd.ast.validator.validate(ast, warped=False)
    return ast


def batch_log(row):
    with open('log.csv', mode='a', encoding='utf-8', newline='\n') as csvout:
        csv_writer = csv.writer(csvout)
        csv_writer.writerow(row)


def batch_folder(folder):
    # Non recursive batch
    files_decompiled = 0
    files_failed = 0
    script_start = time()
    files = os.listdir(folder)
    with open('log.csv', mode='w') as fout:
        pass
    batch_log(['file', 'status', 'time_elapsed', 'fail_reason'])
    print(files)
    for file in files:
        print('decompiling ' + file)
        if os.path.isdir(folder + '\\' + file):
            continue

        start_time = time()

        try:
            ast = decompile_lua(folder + '\\' + file)
            os.makedirs(folder + '\\decompiled_lua', exist_ok=True)

            with open(folder + '\\decompiled_lua\\' + file + '.lua',
                      mode='w', encoding='utf-8') as fout:
                ljd.lua.writer.write(fout, ast)

            time_elapsed = time() - start_time
            print('decompiled in {} seconds'.format(time_elapsed))
            batch_log([file, 'passed', time_elapsed, ])
            files_decompiled += 1

        except Exception as exp:
            time_elapsed = time() - start_time
            print('failed to decompiled ' + file + '\nreason: ' + str(exp))
            batch_log([file, 'failed', time_elapsed, exp])
            files_failed += 1

    print('total files: {}\nfiles decomplied: {}\nfiles failed: {}\n\
time elapsed: {}'.format(files_decompiled + files_failed, files_decompiled,
                         files_failed, time() - script_start))


def single_file(ast):
    with open(sys.argv[1] + '_decompile.lua',
              mode='w', encoding='utf-8') as fout:
        ljd.lua.writer.write(fout, ast)


def print_header_info(fin):
    header, prototype = ljd.rawdump.parser.parse(fin)
    print('\
version: {}\n\
origin: {}\n\
name: {}\n\
bigendian: {}\n\
hasffi: {}\n\
isstripped: {}\n'.format(header.version, header.origin, header.name, header.flags.is_big_endian, header.flags.has_ffi, header.flags.is_stripped))


if __name__ == "__main__":
    file_in = sys.argv[1]
    batch_folder(file_in)
    # single_file(decompile_lua(file_in))
    # print_header_info(file_in)
    
    sys.exit()
