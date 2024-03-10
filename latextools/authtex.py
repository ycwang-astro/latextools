# -*- coding: utf-8 -*-
"""
Created on Fri Mar  1 2024

@author: Yu-Chen Wang

main script
"""

from argparse import ArgumentParser
import os
import sys
import yaml
import re
from .utils import pause_and_warn
from .authmanage import Authors

def authtex(authors=None, style=None, out=None, organize='copy', no_confirm=False, quiet=False):
    if authors is None:
        raise NotImplementedError('please input your author file (-a/--authors)')
    if style is None:
        raise NotImplementedError('please specify the style (-s/--style)')
    if out is None:
        authors_fname = os.path.basename(authors)
        root, ext = os.path.splitext(authors_fname)
        if ext in ['.yaml', '.yml', '.toml', '.json']:
            out = root + '.tex'
        else:
            out = authors + '.tex'
    authors = Authors.load(authors)
    if os.path.exists(out):
        if not no_confirm:
            pause_and_warn(f"'{out}' exists", 'overwrite?')
        elif not quiet:
            print(f"file overwritten: '{out}'")
    authors.generate(style=style, path=out, overwrite=True)
    if not quiet:
        print(f"output file '{out}'")
    
def split(string): # split string but recognizes '\' + whitespace
    return [re.sub(r'\\(\s)', r'\1', s) for s in re.split(r'(?<!\\)\s+', string)]

def main(argv=None):
    parser = ArgumentParser(
        )
    parser.add_argument('-a', '--authors', # required=True,
                        help='path to your author specification file')
    parser.add_argument('-s', '--style', # required=True,
                        help='style name, or path to your style file')
    parser.add_argument('-o', '--out', # required=True,
                        help='path to the output tex file')
    parser.add_argument('--organize', default='copy', choices=('none', 'copy', 'inplace'),
                        help='what to do with the auto-organized author information {'
                        'none: do not save anything; '
                        'copy: save to a copy of the author file; '
                        'inplace: overwrite your input author file (WARNING: some information may be lost)}')
    parser.add_argument('--no-confirm', action='store_true',
                        help='suppress prompts for user confirmation (WARNING: files may be automatically overwritten)')
    parser.add_argument('-q', '--quiet', action='store_true',
                        help='suppress information output')
    
    args = parser.parse_args(argv)
    if args.authors:
        with open(args.authors) as f:
            authors = yaml.load(f, yaml.Loader)
        # re-parse arguments
        if authors['args']:
            new_argv = split(authors['args']) + sys.argv[1:]
            args = parser.parse_args(new_argv)
            if not args.quiet and authors['args']:
                print('args:', ' '.join([f'"{s}"' if re.search(r'\s', s) else s for s in new_argv]))
    
    authtex(authors=args.authors, style=args.style, out=args.out,
            organize=args.organize, no_confirm=args.no_confirm, quiet=args.quiet)

if __name__ == '__main__':
    main()
    