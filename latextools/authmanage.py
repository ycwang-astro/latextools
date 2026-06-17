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
from jinja2 import Environment, StrictUndefined
from importlib import resources

class AuthorInfoError(Exception):
    pass
class DuplicationError(ValueError):
    pass
class AffilNotFoundError(Exception):
    pass

class Namespace():
    '''
    A namespace used for `name` and `affil`
    '''
    def __init__(self, data, name):
        self._name = name
        self._data = data
    
    def __getattr__(self, key):
        try:
            return self._data[key]
        except KeyError:
            raise AttributeError(key)
    
    def __getitem__(self, key):
        return self._data[key]

    def __repr__(self):
        subfields = ', '.join(f'{k}={v}' for k, v in self._data.items())
        return f'<{self._name}({subfields})>' 

    def __str__(self):
        return self._name


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
        'corresponding': False,
        'email': None,
        'orcid': None,
        'equalContribution': False,

        # below are used when generating latex code, but should not be included in authors.yaml
        'affil_number': (),
        }
    
    affil_template = {
        'alias': None,
        'affil': None,
        'affil.division': None,
        'affil.organization': None,
        'affil.street': None,
        'affil.city': None,
        'affil.postcode': None,
        'affil.state': None,
        'affil.country': None,
        'postcode_before_city': False,

        # below are used when generating latex code, but should not be included in authors.yaml
        'number': None,
        'affil_emails': None,
        }
    
    jinja_env = Environment(
        block_start_string='((*',
        block_end_string='*))',

        variable_start_string='[[',
        variable_end_string=']]',

        comment_start_string='((=',
        comment_end_string='=))',

        undefined=StrictUndefined,
        autoescape=False,
        trim_blocks=False,
        lstrip_blocks=False,
        )
    
    @classmethod
    def parse_args(cls, template):
        pass
    
    def add_author(self, author_info: dict = {}, **kwargs):
        # preprocess author info dict and add to self.authaff
        # see author_template for supported fields
        author_info = self.__class__.author_template.copy() | author_info | kwargs
        if isinstance(author_info['affiliation'], str):
            author_info['affiliation'] = (author_info['affiliation'],)
        name_subfields = {key[5:]: val for key, val in author_info.items() if key.startswith('name.')}
        if author_info['name'] and not any(name_subfields.values()):
            # parse names and update 
            try:
                parsed_names = self.__class__.parse_names(author_info['name'])
            except ValueError:
                pass
            else:
                name_subfields.update(parsed_names)
        # if not name and any((givenName, surnamePrefix, surname, suffix)):
        #     name = f'{givenName} {surnamePrefix} {surname} {suffix}'
        author_info['name'] = ' '.join([n for n in name_subfields.values() if n])
        
        # create the author namespace used in templates
        author = {key: value for key, value in author_info.items() if '.' not in key}
        author['name'] = Namespace(name_subfields, author_info['name'])
        
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
        
    def add_affil(self, affil_info: dict = {}, **kwargs):
        # preprocess affil info dict and add to self.authaff
        # see affil_template for supported fields
        affil_info = self.__class__.affil_template.copy() | affil_info | kwargs

        affil_subfields = {key[6:]: val for key, val in affil_info.items() if key.startswith('affil.')}        

        if not affil_info['affil'] and any(affil_subfields):
            if isinstance(affil_subfields['postcode'], (int, float)):
                affil_subfields['postcode'] = str(affil_subfields['postcode'])
            if affil_info['postcode_before_city']:
                affil_subfields['citystatepostcode'] = (affil_subfields['postcode'] + ' ' if affil_subfields['postcode'] else '') + affil_subfields['city'] + (f', {affil_subfields["state"]}' if affil_subfields['state'] else '')
            else:
                affil_subfields['citystatepostcode'] = affil_subfields['city'] + (f', {affil_subfields["state"]}' if affil_subfields['state'] else '') + (' ' + affil_subfields['postcode'] if affil_subfields['postcode'] else '')
            affil_components = ('division', 'organization', 'street', 'citystatepostcode', 'country')
            affil_info['affil'] = ', '.join([affil_subfields[s] for s in affil_components if s if affil_subfields[s]])
        if affil_info['affil'] and not any(affil_subfields):
            # not implemented: auto detect address
            pass
            
        # create the affiliation namespace used in templates        
        affiliation = {key: value for key, value in affil_info.items() if '.' not in key}
        affiliation['affil'] = Namespace(affil_subfields, affil_info['affil'])
        
        self.authaff['affiliations'].append(affiliation)
      
    def get_affil(self, affil_keys):
        # get affil given a list of alias
        if len(affil_keys) != len(set(affil_keys)):
            raise DuplicationError(f"duplication found for '{affil_keys}'")
            
        affiliations = [None] * len(affil_keys)
        
        for affiliation in self.affiliations:
            if affiliation['alias'] in affil_keys:
                affiliations[affil_keys.index(affiliation['alias'])] = affiliation
        
        if None in affiliations:
            raise AffilNotFoundError('affiliation not found: ' + affil_keys[affiliations.index(None)])
        
        return affiliations
      
    @staticmethod
    def _autonumber(l, key):
        # sort list of dict, l, by the value of dict key `key`, and re-number them to 1, 2, 3, etc. 
        l.sort(
            key = lambda d: (d[key] is None, d[key]) # None values are sorted to the end.
            # key = lambda d: d[key]
            )
        renumber_map = {}
        for i, d in enumerate(l, start=1):
            if d[key]:
                renumber_map[d[key]] = i
            d[key] = i
        return renumber_map
    
    def organize(self, autonumber=True, sort=True):
        ## reset numbers for authors
        self.__class__._autonumber(self.authors, 'order')
        
        ## set affiliation numbers and trim unused entries
        author_affiliations = [] # lists of affiliations for each author
        used_affiliations = [] # a list of affiliations used by authors
        for author in self.authors:
            affiliations = self.get_affil(author['affiliation'])
            author_affiliations.append(affiliations)
            for affiliation in affiliations:
                if affiliation not in used_affiliations:
                    used_affiliations.append(affiliation)
        for i, affiliation in enumerate(used_affiliations, start=1):
            affiliation['number'] = i
        self.authaff['affiliations'] = used_affiliations
        
        for affiliation in self.affiliations:
            affiliation['affil_emails'] = ''
        
        for author, affiliations in zip(self.authors, author_affiliations):
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
        
        author_list = re.split(r',\s*', authaff.get('author_list')) if authaff.get('author_list') else None
        author_set = re.split(r',\s*', authaff.get('author_set')) if authaff.get('author_set') else None
        
        known_names = []
        
        for author in authaff['authors']:
            name = author.get('name')
            if not name:
                name = ' '.join(n for n in (author.get('name.givenName'), author.get('name.surname')) if n)
            known_names.append(name)
            
            if author_list:
                if name not in author_list:
                    continue
                else:
                    # overwrites order
                    author['order'] = author_list.index(name)
            
            if author_set and name not in author_set:
                continue
            
            # skip order=None
            if author['order'] is None:
                continue
            
            newobj.add_author(**author)
        
        if author_list:
            for name in author_list:
                if name and name not in known_names:
                    raise ValueError(f'name "{name}" not found')
        if author_set:
            for name in author_set:
                if name and name not in known_names:
                    raise ValueError(f'name "{name}" not found')
        
        for affiliation in authaff['affiliations']:
            newobj.add_affil(**affiliation)
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
        # elif format == 'toml':
        #     return toml.dumps(self.authaff)
        # elif format == 'json':
        #     return json.dumps(self.authaff, indent=4)
    
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
        
        # expand ((* INS <content> *))
        # supresses <content> unless all [[ variable ]] are truthy
        VAR_PATTERN = re.compile(r'\[\[\s*(.*?)\s*\]\]')
        INS_PATTERN = re.compile(
            r'\(\(\*\s*INS\s+(.*?)\s*\*\)\)',
            re.DOTALL
            )
        
        def repl(match):
            content = match.group(1)
    
            # find all variables inside [[ ... ]]
            vars_ = VAR_PATTERN.findall(content)
    
            # remove duplicates while preserving order
            seen = set()
            vars_unique = []
            for v in vars_:
                if v not in seen:
                    seen.add(v)
                    vars_unique.append(v)
    
            if not vars_unique:
                # no variables → keep content directly
                return content
    
            condition = " and ".join(vars_unique)
    
            return f"((* if {condition} *)){content}((* endif *))"
        
        s = INS_PATTERN.sub(repl, s)
        
        namespace = {}
        for d in dicts:
            namespace |= d
        tmpl = self.__class__.jinja_env.from_string(s)
        s = tmpl.render(**namespace)
        
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
                with resources.as_file(resources.files(__package__) / 'styles' / f'{style}.yaml') as stylepath:
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
