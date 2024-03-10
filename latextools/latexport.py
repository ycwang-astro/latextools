# -*- coding: utf-8 -*-
"""
Created on Mon May  1 2023

@author: Yu-Chen Wang
"""

from argparse import ArgumentParser
import os
import sys
import glob
from zipfile import ZipFile, ZIP_DEFLATED
import subprocess
try:
    import regex as re
except ModuleNotFoundError:
    import re

# default config file
default_config = \
r'''## The configuration file consists of lines of options.
## A line typically starts with a command, followed by several parameters.
## commands and parameters are seperated by whitespace characters (e.g. spaces).
## If a parameter itself contains whitespace characters, there should be a backslash ('\') before each of the whitespace characters.

## [echo] printing information on the screen
# echo using a config file # this will print "using a config file" on the screen

## [args] adding arguments
# args -b file\ name.tex # this is equivalent to adding arguments "-b file\ name.tex" before the arguments you pass in the terminal.
# if argument values contains whitespaces, you must use backslashs ('\'). Quotation marks (e.g. "argunemt with spaces") are not supported.

## [add] manually adding files to the zip
# add filepath # filepath is RELATIVE TO THE MAIN TEX FILE.

## [replace] text replacement
# replace <pattern> <replacement> # Replace <pattern> to <replacement> in the merged tex file. 
# Regular expressions are supported. Here '.' matches any character INCLUDING A NEW LINE.
# Below are some examples.

# if you have installed package 'regex':
# replace \\added\{(?P<added_txt>(?P<t>[^{}]|\{(?&t)*\})*)\} \g<added_txt>  # \added{<added_txt>} -> <added_txt>
# replace \\replaced\{(?P<old_txt>(?P<t>[^{}]|\{(?&t)*\})*)\}\{(?P<replaced_txt>(?&t)*)\} \g<replaced_txt>  # \replaced{<old_txt>}{<replaced_txt>} -> <replaced_txt>
# replace ^[\ \t]*\\deleted\{(?P<deleted_txt_>(?P<t>[^{}]|\{(?&t)*\})*)\}[\ \t]*(\r\n|\r|\n)|\\deleted\{(?P<deleted_txt>(?&t)*)\}  # \deleted{<deleted_txt>} ->  # note: if the only content on a line/several lines is '\deleted{<deleted_txt>}', remove the line(s) altogether
# replace ^[\ \t]*\\explain\{(?P<explain_txt_>(?P<t>[^{}]|\{(?&t)*\})*)\}[\ \t]*(\r\n|\r|\n)|\\explain\{(?P<explain_txt>(?&t)*)\}  # \explain{<explain_txt>} ->  # note: if the only content on a line/several lines is '\explain{<explain_txt>}', remove the line(s) altogether
    
# without 'regex':
# This script supports a '\c<number>c' synctex, which will be converted to the regular expression that matches text with up to <number> level(s) of balanced '{}'. For example, '\c0c' only matches text without '{' or '}', '\c1c' can also match something like 'text{text}text', '\c2c' can also match something like 'text{text{text}text}text', etc.
# replace \\added\{(?P<added_txt>\c5c)\} \g<added_txt>  # \added{<added_txt>} -> <added_txt>
# replace \\replaced\{(?P<old_txt>\c5c)\}\{(?P<replaced_txt>\c5c)\} \g<replaced_txt>  # \replaced{<old_txt>}{<replaced_txt>} -> <replaced_txt>
# replace ^[\ \t]*\\deleted\{(?P<deleted_txt_>\c5c)\}[\ \t]*(\r\n|\r|\n)|\\deleted\{(?P<deleted_txt>\c5c)\}  # \deleted{<deleted_txt>} ->  # note: if the only content on a line/several lines is '\deleted{<deleted_txt>}', remove the line(s) altogether
# replace ^[\ \t]*\\explain\{(?P<explain_txt_>\c5c)\}[\ \t]*(\r\n|\r|\n)|\\explain\{(?P<explain_txt>\c5c)\}  # \explain{<explain_txt>} ->  # note: if the only content on a line/several lines is '\explain{<explain_txt>}', remove the line(s) altogether
'''

def main():
    global maintex
    
    # define arguments
    parser = ArgumentParser()
    parser.add_argument('file', nargs="?", default=None, help='The main tex file. If not given, automatically use the .tex file (if there is only one) in the current working directory.')
    parser.add_argument('-o', '--out', help='The name of the output zip file. The default is the same as that of the main tex file.')
    parser.add_argument('-p', '--params', default='', help='The parameters passed to latexpand')
    parser.add_argument('-b', '--bibtex', action='store_true', help='Use bibtex (with .bst, .bib) files. By default, bibliography is expanded using the *.bbl file.')
    parser.add_argument('-c', '--config', default=None, help='The configuration file. The default file is "<main tex file name>.ltxpconfig". If the config file does not exist, a sample file will be automatically generated.')
    args = parser.parse_args()
    
    # the \c<number>c syntex
    def gen_curly_balanced_match(recursive_level=1):
        s = '.*' # a placeholder
        for _ in range(recursive_level):
            s = s.replace('.*', r'([^{}]|\{.*\})*')
        s = s.replace('.*', '[^{}]*')
        return s
    def rep(matchobj):
        return gen_curly_balanced_match(int(matchobj.group('level')))
    
    if args.file is None:
        files = os.listdir('.')
        texfiles = [f for f in files if f.endswith('.tex')]
        if len(texfiles) != 1:
            raise ValueError('Please input the main tex file.')
        else:
            args.file = texfiles[0]
    
    # read config
    if args.config is None:
        args.config = args.file[:-4] + '.ltxpconfig'
    if not os.path.exists(args.config):
        with open(args.config, 'w') as f:
            f.write(default_config)
    with open(args.config) as f:
        config = f.readlines()
    
    # parse config
    print(f"parsing config file '{args.config}'")
    add_files = []
    replacements = []
    args = []
    def split(string): # split string but recognizes '\' + whitespace
        return [re.sub(r'\\(\s)', r'\1', s) for s in re.split(r'(?<!\\)\s+', string)]
    for line in config:
        line = line.split('#')[0]
        line = split(line)
        line = [re.sub(r'\\c(?P<level>[0-9]+)c', rep, s) for s in line]
        if line[0] == 'add':
            add_files.append(line[1])
            print(f"config: add file '{line[1]}'")
        if line[0] == 'replace':
            replacements.append((line[1], line[2]))
            print(f"config: replace:  {line[1]}   ->   {line[2]}")
        if line[0] == 'args':
            args += [l for l in line[1:] if l != '']
            
            # args = parser.parse_args(args)
            # if argname == 'config':
            #     print("WARNING: argument 'config' cannot be set in a config file")
            # elif not hasattr(args, argname):
            #     print(f"WARNING: unrecognized argunemt '{argname}' in config file, ignored")
            # elif 
        
        if line[0] == 'echo':
            print(' '.join(line[1:]))
            
    # re-parse args
    args += sys.argv[1:]
    print('parsing args', args)
    args = parser.parse_args(args)
    
    # handle arguments
    if args.file is None:
        files = os.listdir('.')
        texfiles = [f for f in files if f.endswith('.tex')]
        if len(texfiles) != 1:
            raise ValueError('Please input the main tex file.')
        else:
            args.file = texfiles[0]
    print(f"main tex file: '{args.file}'")
    
    if args.out is None:
        args.out = args.file[:-4] + '.merged.zip'
    print(f"output zip file: '{args.out}'")
    if os.path.exists(args.out):
        overwrite = input(f'"{args.out}" already exists. Do you want to overwrite it? y/[n] >>> ')
        if overwrite not in ['y']:
            raise FileExistsError(f'"{args.out}" already exists. Nothing done.')
    
    # expand bbl?
    if '--expand-bbl' not in args.params and not args.bibtex:
        bblfile = args.file[:-4] + '.bbl'
        if not os.path.exists(bblfile):
            raise FileNotFoundError(f"{bblfile} not found. You may consider passing `--bibtex` or `-p \"--expand-bbl BBLFILE\"` or generating a bbl file.")
        args.params += f' --expand-bbl {bblfile}'
    print(f"latexpand args: '{args.params}'")
    
    output = subprocess.check_output(['latexpand'] + args.params.split() + [args.file]) # split(args.params)
    maintex = output.decode()
    
    includegraphics = r"\\includegraphics(?:\[[^\]]*\])?\{[^\}]*\}"
    graphics = re.findall(includegraphics, maintex, flags=re.DOTALL)
    imgpaths = [t.split('{')[1].split('}')[0] for t in graphics]
    
    documentclass = r"\\documentclass(?:\[[^\]]*\])?\{[^\}]*\}"
    clsfile = re.findall(documentclass, maintex, flags=re.DOTALL)[0].split('{')[1].split('}')[0]
    
    def get_rel_path(mainpath, relpath):
        return os.path.relpath(os.path.join(os.path.dirname(mainpath), relpath))
    def move(relpath, f, ext='.*', prefix=''):
        global maintex
        path = get_rel_path(args.file, relpath)
        newpath = prefix + os.path.basename(path)
        maintex = maintex.replace(relpath, newpath)
        if not os.path.exists(path):
            paths = glob.glob(path + ext)
            if len(paths) == 0:
                raise FileNotFoundError(path)
            elif len(paths) >= 2:
                raise ValueError(f'I do not know which to use: {paths}')
            path = paths[0]
            newpath += '.' + path.split('.')[-1]
        f.write(path, arcname=newpath)
    
    with ZipFile(args.out, 'w', compression=ZIP_DEFLATED) as f:
        # cls file
        try:
            move(clsfile, f, ext='.cls')
        except FileNotFoundError:
            pass
        
        # bst, bib file
        if args.bibtex:
            bibliography = r"\\bibliography(?:\[[^\]]*\])?\{[^\}]*\}"
            bibfiles = [t.split('{')[1].split('}')[0] for t in re.findall(bibliography, maintex, flags=re.DOTALL)]
            
            bibliographystyle = r"\\bibliographystyle(?:\[[^\]]*\])?\{[^\}]*\}"
            bstfiles = [t.split('{')[1].split('}')[0] for t in re.findall(bibliographystyle, maintex, flags=re.DOTALL)]
            
            for bibfile in bibfiles:
                move(bibfile, f, ext='.bib')
            for bstfile in bstfiles:
                try:
                    move(bstfile, f, ext='.bst')
                except FileNotFoundError:
                    pass
        
        # img file
        for i, imgpath in enumerate(imgpaths):
            move(imgpath, f, prefix=f'fig{i+1}_')
    
        # added file in config
        for add_file in add_files:
            move(add_file, f)
    
        # replacements in config
        for pattern, repl in replacements:
            try:
                maintex = re.sub(pattern, repl, maintex, flags=re.DOTALL|re.MULTILINE)
            except Exception as e:
                raise RuntimeError(f"Error occurred for replacement:  {pattern}   ->   {repl}") from e
        
        with f.open(os.path.basename(args.file), mode='w') as texf:
            texf.write(maintex.encode())
