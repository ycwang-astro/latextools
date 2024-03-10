# -*- coding: utf-8 -*-
"""
Created on Tue Mar  5  2024

@author: Yu-Chen Wang
"""

# import subprocess
import os
from latextools.authmanage import Authors

latex_file = r'''
\documentclass{%s}
\usepackage{hyperref}
\usepackage{amsmath}
\def\mailto#1{\href{mailto:#1}{#1}}
\begin{document}
\title{Title}

\input{author.tex}

\maketitle

\section{Section}
\end{document}
'''

def test(classfile, authorfile, authortemplate, mainfile=None):
    if classfile.endswith('.cls'):
        classfile = classfile.replace('.cls', '')
    with open('temp/main.tex', 'w') as f:
        if not mainfile:
            f.write(latex_file % classfile)
        else:
            with open(mainfile) as fr:
                f.write(fr.read())
    authors = Authors.load(authorfile)
    authors.generate(style=authortemplate, path='temp/author.tex', overwrite=True)
    os.chdir('temp')
    r = os.system("pdflatex -interaction=nonstopmode main.tex")
    os.chdir('..')
    return r
    
r = test('sn-jnl', '../templates/authors-template.yaml', 'sn-jnl')

r = test('aastex631', '../templates/authors-template.yaml', 'aastex', mainfile='aastex631.tex')

r = test('mnras', '../templates/authors-template.yaml', 'mnras', mainfile='mnras.tex')

r = test('aa', '../templates/authors-template.yaml', 'aa')

r = test('raa', '../templates/authors-template.yaml', 'raa')
