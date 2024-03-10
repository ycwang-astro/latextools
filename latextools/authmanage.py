# -*- coding: utf-8 -*-
"""
Created on Fri Mar  1 2024

@author: Yu-Chen Wang
"""

# from utils import objdict
import yaml
# import toml
# import json
# from collections.abc import Iterable
# from collections import OrderedDict
import re
import os
# import pkgutil
from pkg_resources import resource_filename

class AuthorInfoError(Exception):
    pass
class DuplicationError(ValueError):
    pass
class AffilNotFoundError(Exception):
    pass

class Authors:
    def __init__(self, s=None, format='yaml'):
        if s is None: # generate empty one
            self.authaff = ({
                'authors': [],
                'affiliations': [],
                })
        else:
            raise NotImplementedError()
    
    author_template = {
        'name': None,
        'name.givenName': None,
        'name.surnamePrefix': None,
        'name.surname': None,
        'name.suffix': None,
        'name.abbrev': None, 
        'order': None,
        'affiliation': (),
        'affil_number': (),
        'corresponding': False,
        'email': None,
        'orcid': None,
        'equalContribution': False,
        }
    
    affil_template = {
        'number': None,
        'alias': None,
        'affil': None,
        'affil.division': None,
        'affil.organization': None,
        'affil.street': None,
        'affil.city': None,
        'affil.postcode': None,
        'affil.state': None,
        'affil.country': None,
        
        # for use when generating latex code:
        'affil_emails': None,
        }
    
    @classmethod
    def parse_args(cls, template):
        pass
    
    def add_author(self, 
                   name=None, givenName=None, surnamePrefix=None, surname=None, suffix=None,
                   order=None,
                   affiliation: list | tuple | dict = (),
                   corresponding=False, email=None, orcid=None, equalContribution=False,
                   ):
        if isinstance(affiliation, str):
            affiliation = (affiliation,)
        name_types = ('givenName', 'surnamePrefix', 'surname', 'suffix')
        names = {key: val for key, val in locals().items() if key in name_types}
        if name and not any(names.values()):
            # parse names and update 
            parsed_names = self.__class__.parse_names(name)
            names.update(parsed_names)
        # if not name and any((givenName, surnamePrefix, surname, suffix)):
        #     name = f'{givenName} {surnamePrefix} {surname} {suffix}'
        name = ' '.join([n for n in names.values() if n])
        
        # get author dict
        author = self.__class__.author_template.copy()
        for key, val in locals().items():
            if key in author:
                author[key] = val
        for key, val in names.items():
            key = 'name.' + key
            if key in author:
                author[key] = val
        
        self.authaff['authors'].append(author)
        
    @staticmethod
    def parse_names(name):
        if ', ' in name:
            names = name.split(', ')
            if len(names) == 2:
                return dict(
                    surname=names[0],
                    givenName=names[1],
                    )
        raise ValueError(f"name not recognized: '{name}'")
    
    def _sort_authors(self, update_order=True):
        pass
        
    def add_affil(self, 
                  affil='',
                  alias=None, number=None,
                  division='', organization='',
                  street='',
                  city='', postcode='',
                  state='', country='',
                  ):
        affil_types = ('division', 'organization', 'street', 'city', 'postcode', 'state', 'country')
        affils = {key: str(val) if val else val for key, val in locals().items() if key in affil_types}
        if not affil and any(affils):
            citypostcode = affils['city'] + ' ' + affils['postcode']
            affil_components = (division, organization, street, citypostcode, state, country)
            affil = ', '.join([s for s in affil_components if s])
        if affil and not any(affils):
            # not implemented: auto detect address
            pass
            
        affiliation = self.__class__.affil_template.copy()
        for key, val in locals().items():
            if key in affiliation:
                affiliation[key] = val
        for key, val in affils.items():
            key = 'affil.' + key
            if key in affiliation:
                affiliation[key] = val
        
        self.authaff['affiliations'].append(affiliation)
      
    def get_affil(self, affil_keys):
        # get affil given a list of number or alias
        if len(affil_keys) != len(set(affil_keys)):
            raise DuplicationError(f"duplication found for '{affil_keys}'")
            
        affiliations = [None] * len(affil_keys)
        
        for affiliation in self.affiliations:
            if affiliation['alias'] in affil_keys:
                affiliations[affil_keys.index(affiliation['alias'])] = affiliation
            elif affiliation['number'] in affil_keys:
                affiliations[affil_keys.index(affiliation['number'])] = affiliation
        
        if None in affiliations:
            raise AffilNotFoundError('affiliation not found: ' + affil_keys[affiliations.index(None)])
        
        return affiliations
      
    @staticmethod
    def _autonumber(l, key):
        # sort list of dict, l, by the value of dict key `key`, and re-number them to 1, 2, 3, etc. 
        # None values are sorted to the end.
        l.sort(
            key = lambda d: (not d[key], d[key])
            )
        renumber_map = {}
        for i, d in enumerate(l, start=1):
            if d[key]:
                renumber_map[d[key]] = i
            d[key] = i
        return renumber_map
    
    def organize(self, autonumber=True, sort=True):
        ## authors
        self.__class__._autonumber(self.authors, 'order')
        renumber_map = self.__class__._autonumber(self.affiliations, 'number')
        for affiliation in self.affiliations:
            affiliation['affil_emails'] = ''
        for author in self.authors:
            author['affiliation'] = [renumber_map[a] if a in renumber_map else a for a in author['affiliation']]
            affiliations = self.get_affil(author['affiliation'])
            author['affil_number'] = [a['number'] for a in affiliations]
            if author['corresponding'] and author['email']:
                affiliations[0]['affil_emails'] += r'; \mailto{' + author['email'] + '}'
        
    @classmethod
    def load(cls, path, format='yaml'):
        if format == 'yaml':
            with open(path) as f:
                authaff = yaml.load(f, yaml.Loader) 
        else:
            raise NotImplementedError()
        newobj = cls()
        for author in authaff['authors']:
            keys = [k[5:] if k.startswith('name.') else k for k in author.keys()]
            author_kwargs = dict(zip(keys, author.values()))
            newobj.add_author(**author_kwargs)
        for affiliation in authaff['affiliations']:
            keys = [k[6:] if k.startswith('affil.') else k for k in affiliation.keys()]
            affiliation_kwargs = dict(zip(keys, affiliation.values()))
            newobj.add_affil(**affiliation_kwargs)
        return newobj
    
    # def load_library(self, people=None, address=None)
    # def from_library(cls, library)
    
    def dumps(self, format='yaml', organize=True, compact=True):
        self.organize()
        if format == 'yaml':
            def list_representer(dumper, data):
                if all((isinstance(d, (str, int, float)) for d in data)):
                    return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=True)
                else:
                    return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=False)
            yaml.add_representer(list, list_representer)
            
            return yaml.dump(self.authaff, sort_keys=False, default_flow_style=False)
        elif format == 'toml':
            return toml.dumps(self.authaff)
        elif format == 'json':
            return json.dumps(self.authaff, indent=4)
    
    def save(self, path, format='yaml', overwrite=False, authorlist=None):
        # if authorlist is given, generate according to this
        # save the processed (organized) author file
        pass
    
    @property
    def authors(self):
        return self.authaff['authors']
    
    @property
    def affiliations(self):
        return self.authaff['affiliations']
    
    def parse_template(self, template, *dicts):
        s = template
        
        # val &(<...>)
        val_pattern = r'&\(\s*(?P<key>.*?)\s*\)'
        def val_sub(match):
            expr = match.group('key')
            
            for d in dicts:
                if expr in d:
                    value = d[expr]
                    break
            else:
                raise KeyError(expr)
            
            if value:
                return str(value)
            else:
                return '&FALSE'
        s = re.sub(val_pattern, val_sub, s)
        
        # eval expression &EVAL <expr> %ENDEVAL
        eval_pattern = r'&EVAL\s*(?P<expr>.*?)\s*&ENDEVAL'
        def eval_sub(match):
            expr = match.group('expr')
            namespace = {}
            for d in dicts:
                namespace.update(d)
            value = eval(expr, namespace)
            if value:
                return str(value)
            else:
                return '&FALSE'
        s = re.sub(eval_pattern, eval_sub, s)
        
        # ins &INS(<...>)
        ins_pattern = r'&INS\(\s*(?P<str>.*?)\s*\)'
        def ins_sub(match):
            str_ = match.group('str')
            if '&FALSE' in str_:
                return ''
            else:
                return str_
        s = re.sub(ins_pattern, ins_sub, s)
            
        if_pattern = r'&IF\s*(?P<cond>.*?)\s*:\s*(?P<true>.*?)\s*\|\s*(?P<false>.*?)\s*&ENDIF'
        def if_sub(match):
            cond, true, false = match.groups()
            if '&FALSE' in cond:
                return false
            else:
                return true
        
        s = re.sub(if_pattern, if_sub, s)
   
        return s
    
    def load_template(self, path, format='yaml'):
        if format == 'yaml':
            with open(path) as f:
                template = yaml.load(f, yaml.Loader)
            for key, val in template.items():
                if key in ['format']:
                    continue
                template[key] = re.sub('\n\s*', '', val)
            # template['author'] = re.sub('\n\s*', '', template['author'])
            # template['affiliation'] = re.sub('\n\s*', '', template['affiliation'])
        return template
    
    def generate(self, style=None, path=None, overwrite=False):
        self.organize()
        if style is None:
            raise NotImplementedError
        elif os.path.exists(style):
            self.template = self.load_template(style)
        # elif '/' not in style and '\\' not in style:
        elif os.path.exists(f'styles/{style}.yaml'):
            self.template = self.load_template(f'styles/{style}.yaml')
        else:
            if style.endswith('.yaml'):
                style = style[:-len('.yaml')]
            # stylefile = pkgutil.get_data(__name__, f'styles/{style}.yaml')
            try:
                stylepath = resource_filename(__name__, f'styles/{style}.yaml')
                self.template = self.load_template(stylepath)
            except FileNotFoundError as e:
                raise FileNotFoundError(f"cannot find style '{style}'") from e
            
        tempvars = {} # variables presented in the template file
        
        format = self.template['format']
        self.export_str = ''
        
        def execute_format(format, itername='author'):
            # execute according to the "format" given in the style file
            if isinstance(format, dict):
                # iterate over authors or affiliations
                for kind, contents in format.items():
                    if kind in ['authors', 'author']:
                        for author in self.authors:
                            self.author = author
                            execute_format(contents, 'author')
                    elif kind in ['affiliations', 'affiliation']:
                        for affiliation in self.affiliations:
                            self.affiliation = affiliation
                            execute_format(contents, 'affiliation')
                    # self.export_str += '\n'
            elif isinstance(format, list):
                # in interation: what content to add?
                for content_kind in format:
                    execute_format(content_kind, itername=itername)
                    # if isinstance(content_kind, (list, dict)):
                    #     execute_format(content_kind)
            elif isinstance(format, str):
                if format == 'author':
                    if itername == 'author':
                        self.export_str += self.parse_template(self.template['author'], self.author, tempvars) + '\n'
                    elif itername == 'affiliation':
                        raise NotImplementedError()
                elif format == 'affiliation':
                    if itername == 'author':
                        for affiliation in self.get_affil(self.author['affiliation']):
                            self.export_str += self.parse_template(self.template['affiliation'], self.author, affiliation, tempvars) + '\n'
                    elif itername == 'affiliation':
                        self.export_str += self.parse_template(self.template['affiliation'], self.affiliation, tempvars) + '\n'
                elif format in (key for key in self.template.keys() if key not in ['format']):
                    self.export_str += self.parse_template(self.template[format], tempvars) + '\n'
                elif format in ['newline']:
                    self.export_str += '\n'
                else:
                    raise ValueError(f"unknown format string '{format}': have you defined it in your format file?")
                    
        execute_format(format)
        
        # for kind, contents in format.items():
        #     if kind in ['authors', 'author']:
        #         for author in self.authors:
        #             for content_kind in contents:
        #                 if content_kind == 'author':
        #                     authaff += self.parse_template(self.template['author'], author, tempvars) + '\n'
        #                 elif content_kind == 'affiliation':
        #                     for affiliation in self.get_affil(author['affiliation']):
        #                         authaff += self.parse_template(self.template['affiliation'], author, affiliation, tempvars) + '\n'
        #     elif kind in ['affiliations', 'affiliation']:
        #         for affiliation in self.affiliations:
        #             for content_kind in contents:
        #                 if content_kind == 'author':
        #                     raise NotImplementedError()
        #                 elif content_kind == 'affiliation':
        #                     authaff += self.parse_template(self.template['affiliation'], affiliation, tempvars) + '\n'
        #     authaff += '\n'
        
        if path:
            if os.path.exists(path) and not overwrite:
                raise FileExistsError(path)
            with open(path, 'w') as f:
                f.write(self.export_str)
        
        return self.export_str
