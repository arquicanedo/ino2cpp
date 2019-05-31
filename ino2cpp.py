import os
import glob
import clang.cindex
import shutil
import argparse

# Mac needs explicit reference to clang
import platform
if platform.system() == 'Darwin':
    clang.cindex.Config.set_library_path('/Library/Developer/CommandLineTools/usr/lib/')

def filter_by_type(translation_unit, filter=None):
    cursor = translation_unit.cursor
    filtered_elts = []
    for child in cursor.get_children(): 
        if filter:
            if child.kind == filter:
                filtered_elts.append(child)
    return filtered_elts

def convert(ino_file, targetdir=None):
    if not targetdir:
        targetdir = '.'
    index = clang.cindex.Index.create()
    
    # Necessary arguments for clang to parse the translation unit
    compilation_arguments = ['-E', '-x', 'c++']

    # Parse ino file to generate function signatures and populate the header definitions file
    tu = index.parse(ino_file, compilation_arguments)
    function_definitions = []
    functions = []
    functions = filter_by_type(tu, clang.cindex.CursorKind.FUNCTION_DECL)
    for f in functions:
        function_definitions.append('%s %s;' % (f.result_type.spelling, f.displayname))
    
    # Write to header file
    ino_file_name = ino_file.split('/')[-1].split('.')[0]
    print('writing to %s/%s.cpp' % (targetdir, ino_file_name))
    with open(targetdir + '/' + ino_file_name + '.h', 'w') as f:
        f.writelines(['%s\n' % x for x in function_definitions])

    # Copy INO file to targetdir
    shutil.copy(ino_file, targetdir + '/' + ino_file_name + '.cpp')

    # Insert #include <Arduino.h> and #include <self.h> in target CPP files)
    with open(targetdir + '/' + ino_file_name + '.cpp', 'r+') as f:
        content = f.read()
        f.seek(0, 0)
        f.write('#include <Arduino.h>\n#include \"%s\"\n%s' % (ino_file_name + '.h', content))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='ino2cpp converts arduino INO files to C++ files')
    parser.add_argument('ino_file', nargs='+', help='INO file')
    parser.add_argument('-o', '--output', help='Target directory')

    args = parser.parse_args()

    # Output directory
    if args.output and not os.path.exists(args.output):
        print('Creating output directory %s' % (args.output))
        os.makedirs(args.output)

    # Generate .cpp and .h files
    for f in args.ino_file:
        convert(f, args.output)
