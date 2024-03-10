# -*- coding: utf-8 -*-
"""
Created on Fri Mar  1 2024

@author: Yu-Chen Wang
"""

import warnings

def pause_and_warn(message=' ', choose='Proceed?', default = 'n', yes_message='', no_message='raise', warn=True, timeout=None):
    '''
    calling this function will do something like this:
            [print]  <message>
            [print]  <choose> y/n >>> 
    default choice is <default>
    if yes:
            [print] <yes_message>
    if no:
            [print] <no_message>
        if no_message is 'raise':
            [raise] Error: <message>
    [return] the choise, True for yes, False for no.
    '''
    print('{:-^40}'.format('[WARNING]'))
    
    if isinstance(message, Exception):
        message = str(type(message)).replace('<class \'','').replace('\'>', '')+': '+'. '.join(message.args)
    if warn:
        warnings.warn(message, stacklevel=3)
    print(message)
    
    question = '{} {} >>> '.format(choose, '[y]/n' if default == 'y' else 'y/[n]')
    if timeout is None:
        cont = input(question)
    else:
        raise NotImplementedError
    if not cont in ['y', 'n']:
        cont = default
    if cont == 'y':
        print(yes_message)
        return True
    elif cont == 'n':
        if no_message == 'raise':
            raise RuntimeError(message)
        else:
            print(no_message)
            return False        
    