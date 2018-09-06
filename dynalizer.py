import os, sys
import inflection
import clang.cindex
import argparse

def list_functions(tu, name):
    """List the function declarations in a C header."""
    class reader:
        file_path = ""
        functions = []

        def recurse(self, node):
            cld = node.get_children()
            while 1:
                try:
                    c = next(cld)
                except StopIteration:
                    break

                if(c.location.file is not None):
                    if(c.location.file.name == self.file_path):
                        if(c.kind == clang.cindex.CursorKind.FUNCTION_DECL):
                            self.functions.append(c.spelling)

                self.recurse(c)

        def process(self, tu, fp):
            self.file_path = fp
            self.recurse(tu.cursor)

    r = reader()
    r.process(tu, name)
    return r.functions


def no_prettify(str):
    return str
def prettify(str):
    """Transforms an API that looks like Lib_WhateverFunc into whatever_func"""
    return inflection.underscore(fun.replace(prefix, '', 1))

def eager(hpp, file, functions):
    init = ""
    funlist = ""
    for fun in functions:
        pretty_fun = fun[1]
        init = init + "  {}_WRAP_INIT({})\n".format(name.upper(), fun[0])
        funlist = funlist + "  {}_WRAP_FUNCTION({}, {})\n".format(name.upper(), fun[0], fun[1])

    with open(hpp, 'r') as f:
        output_file = f.read()
        output_file = output_file.replace('$HEADER', header)
        output_file = output_file.replace('$CLASS', name)
        output_file = output_file.replace('$UCLASS', name.upper())
        output_file = output_file.replace('$INIT', init)
        output_file = output_file.replace('$FUNCTIONS', funlist)

    return output_file

def lazy(hpp, file, functions):
    output = ""
    for fun in functions:
        output = output + "  {}_WRAP_FUNCTION({}, {})\n".format(name.upper(), fun[0], fun[1])

    with open(hpp, 'r') as f:
        output_file = f.read()
        output_file = output_file.replace('$HEADER', header)
        output_file = output_file.replace('$CLASS', name)
        output_file = output_file.replace('$UCLASS', name.upper())
        output_file = output_file.replace('$FUNCTIONS', output)

    return output_file


def eager_throw(file, functions):
    return eager('configurations/library-eager-throw.hpp.in', file, functions)

def eager_abort(file, functions):
    return eager('configurations/library-eager-abort.hpp.in', file, functions)


def lazy_throw(file, functions):
    return lazy('configurations/library-lazy-throw.hpp.in', file, functions)

def lazy_abort(file, functions):
    return lazy('configurations/library-lazy-abort.hpp.in', file, functions)


parser = argparse.ArgumentParser(description='Generate a dynamic loader class for a C API.')
parser.add_argument('file', type=str, help='C header to parse')
parser.add_argument('name', type=str, nargs='?', help='Name to give to the class')
parser.add_argument('include', type=str, nargs='?', help='Header to include')
parser.add_argument('--pretty', action='store_const', const=True, default=False, help='Prettify')

eagerness = parser.add_mutually_exclusive_group()
eagerness.add_argument('--eager', action='store_true', default=True, help='Load symbols eagerly')
eagerness.add_argument('--lazy', action='store_false', help='Load symbols lazily')

reporting = parser.add_mutually_exclusive_group()
reporting.add_argument('--throw', action='store_true', default=True, help='Throw on missing symbol')
reporting.add_argument('--abort', action='store_false', help='Abort on missing symbol')
args = parser.parse_args()

index = clang.cindex.Index.create()

filename = args.file
name = args.name
if name == None:
    name = os.path.splitext(os.path.basename(args.file))[0]

header = args.include
if header == None:
    include_idx = args.file.find("include/")
    if include_idx != -1:
        header = args.file[include_idx + 8:]
    else:
        header = os.path.basename(args.file)
    
    
try:
    with open(filename, 'r') as content_file:
        source_file = content_file.read()

    tu = index.parse(filename, [], options=clang.cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD)

    functions = list_functions(tu, filename)

    fun_map = []
    
    if(args.pretty):
        prefix = os.path.commonprefix(functions)
        for f in functions:
            fun_map.append([f, inflection.underscore(f.replace(prefix, '', 1))])
    else:
        for f in functions:
            fun_map.append([f, f])

    if(args.eager):
        if(args.throw):
            output = eager_throw(filename, fun_map)
        elif(args.abort):
            output = eager_abort(filename, fun_map)
    elif(args.lazy):
        if(args.throw):
            output = lazy_throw(filename, fun_map)
        elif(args.abort):
            output = lazy_abort(filename, fun_map)

    print(output)
except clang.cindex.TranslationUnitLoadError as e:
    print("Error: ", e.args)


