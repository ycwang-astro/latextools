## authtex
### Introduction
`authtex` is a simple tool that helps you manage authors and affiliations in a unified manner. Author and affiliation information is stored in a separate file with a clear format. `authtex` can generate LaTeX code required for any journal, provided that a corresponding "style" file for that journal is available (see [Style files](#Style-files) for details).

This tool is particularly useful when you need to submit to different journals, either resubmitting a rejected manuscript or drafting a new manuscript that reuses authors/affiliations from your previous manuscripts. 

The LaTeX format for authors and affiliations varies significantly between different journals. For example, the code for `aastex631.cls` is:
```latex
\author[0000-0000-0000-0000]{A Author}
\affiliation{University of Somewhere; \mailto{authorA@email.com}; \mailto{authorB@email.com}}
\affiliation{University of Elsewhere}

\author{B Author}\altaffiliation{These authors contributed equally to this work.}
\affiliation{University of Somewhere; \mailto{authorA@email.com}; \mailto{authorB@email.com}}

\author{C Author}\altaffiliation{These authors contributed equally to this work.}
\affiliation{University of Elsewhere}
```
while the code for `mnras.cls` is:
```latex
\author{
A Author,$^{[1, 2]}$\thanks{E-mail: authorA@email.com}
B Author,$^{[1]}$\thanks{E-mail: authorB@email.com}
C Author,$^{[2]}$
\\ $^{1}$University of Somewhere
\\ $^{2}$University of Elsewhere
}
```
and for `sn-jnl.cls`:
```latex
\author*[1, 2]{\fnm{A}  \sur{Author}}\email{authorA@email.com}

\author*[1]{\fnm{B}  \sur{Author}}\email{authorB@email.com}\equalcont{These authors contributed equally to this work.}

\author[2]{\fnm{C}  \sur{Author}}\email{authorC@email.com}\equalcont{These authors contributed equally to this work.}

\affil[1]{University of Somewhere}
\affil[2]{University of Elsewhere}
```
It is clear that the formats for different journals are significantly different. Switching between different formats can be tedious and time-consuming, which is why `authtex` was developed.

With `authtex`, one only needs to maintain an author list like this (see [authors-template](../templates/authors-template.yaml) for a full template with explanations):
```yaml
authors:
- name: A Author
  name.givenName: A
  name.surname: Author
  order: 1
  affiliation: [uns, une] 
  corresponding: true
  email: authorA@email.com
  orcid: 0000-0000-0000-0000
  
- name: B Author
  name.givenName: B
  name.surname: Author
  order: 2
  affiliation: [uns]
  corresponding: true
  email: authorB@email.com
  equalContribution: true
  
- name: C Author
  name.givenName: C
  name.surname: Author
  order: 3
  affiliation: [une]
  email: authorC@email.com
  equalContribution: true


affiliations:
- alias: uns
  affil: University of Somewhere
  
- alias: une
  affil: University of Elsewhere
```
Using a file like the one above, `authtex` generates the LaTeX code for you. In fact, the LaTeX code examples for different journals mentioned earlier were generated using `authtex`.

Since `authtex` uses a unified format to store author and affiliation information, one may maintain a library of this information for easy reuse in future manuscripts.

### Quick start
To start using `authtex`, first create an author file (e.g., `authors.yaml`) containing information about the authors and the affiliations. The simplest way to do this is by modifying the template provided [here](../templates/authors-template.yaml). Guidelines are included in the template file.

Then, you can generate LaTeX code to a .tex file (e.g., `authors.tex`) with the desired format. For example, to generate code for AASTeX, execute the following command in your terminal:
```
authtex --authors authors.yaml --style aastex --out authors.tex
```
or more concisely:
```
authtex -a authors.yaml -s aastex -o authors.tex
```
The arguments (except `--authors`) can be added in your author file, e.g.:
```yaml
# this is added to authors.yaml
args:
  -s aastex -o authors.tex
```
This allows you to further simplify the command:
```
authtex -a authors.yaml
```

After generating `authors.tex`, you can include the LaTeX code in your main .tex file by:
```latex
\input{authors.tex}
```

The built-in styles currently included in `authtex` are:
- `aa`. Used for [A&A](https://www.aanda.org/for-authors).
- `aastex`. Used for [AAS journals](https://journals.aas.org/aastex-package-for-manuscript-preparation/#_download)
- `mnras`. Used for [MNRAS](https://academic.oup.com/mnras/pages/general_instructions#2.1%20LaTeX).
- `raa`. Used for [RAA journal](https://www.raa-journal.org/sub/macro/).
- `sn-jnl`. A LaTeX class provided by [Springer Nature](https://www.springernature.com/gp/authors/campaigns/latex-author-support#c17590862)

If the style you need is not included, you may:
- Request for addition [here](https://github.com/ycwang-astro/latextools/issues).
- Write your own style file (see [Style files](#Style-files)), and pass it to `authtex` like:
```
-s path/to/custom-style.yaml
```
You are encouraged to contribute by adding your style file and creating a [pull request](https://github.com/ycwang-astro/latextools/pulls).


### Style files
A style file is a YAML file that should include at least 3 keys: `author`, `affiliation` and `format`. You may get an idea of the sturcture by reading the built-in style files [here](../latextools/styles).

#### `format`

This is the primary field that defines the sturcture of the desired LaTeX string for authors and affiliations. The `format` should be defined as a list. Below is an example of how `format` is structured: 
```yaml
# excerpt from latextools/styles/mnras.yaml 

# defines strings for "prefix" and "suffix"
prefix: |
    \author{

suffix: |
    }

format: 
    - prefix # inserts the content of "prefix"
    - authors: # iterates over authors
        author # adds the author string
    - affiliations: # iterates over affiliations
        affiliation # adds the affiliation string
    - suffix # inserts the content of "suffix"
```
Each element in the `format` list can either be a "name" or an "iteration", defined as follows:
- **name**: You can define any custom strings in the style file as:
```yaml
name: |
    % LaTeX string to be included
```
Adding `- name` under `format:` includes the specified LaTeX string in the output. The name cannot be `format` itself. There are two special names, `author` and `affiliation`.
- **iteration**: You can iterate over authors or affiliations to output LaTeX strings. For example, the following iterates over each author, adding thier respective author string (defined in the `author` key) and affiliation string (defined in the `affiliation` key):
```yaml
# excerpt from latextools/styles/aastex.yaml 
format: 
    authors: # for each author:
        - author # adds string for this author
        - affiliation # adds string for the affiliations of this author
        - newline # adds a new line
```

#### Syntax for strings
As mentioned earlier, you can define strings with names in the style file. The strings support several syntax patterns, as shown below.

- **Variable expansions**: `&(varname)` retrieves the value of the variable named `varname` from the namespace. Supported variables in the namespace are detailed [here](#`author`-and-`affiliation`).
- **Evaluation**: `&EVAL <expr> &ENDEVAL` evaluates an expression `<expr>`, where variables from the namespace can be included. This is often used within an if-else statement.
- **Insertion**: `&INS(varname)` adds the value of `varname` to the output string if `bool(varname) is True` (similar to `&(varname)`); otherwise, it adds nothing to the output string. For example, if the value of `varname` is `''` or `None`, `&INS(varname)` adds nothing to the string.
- **if-else statement**: `&IF <condition> : <true string> | <false string> &ENDIF` conditionally adds `<true string>` if `<condition>` is True; otherwise, it adds `<false string>`. For example:
```
&IF &EVAL order == 1 &ENDEVAL : 
    \author{ 
| 
    \and 
&ENDIF 
```
This statement behaves as follows:
```
if order == 1: # 'order' is a variable
    # add "\author{ " to the output string
else:
    # add "\and " to the output string
```

Newlines and leading whitespace at the beginning of each line of the string are always ignored (deleted). Therefore, the above statement is equivalent to:
```
&IF &EVAL order == 1 &ENDEVAL : \author{ | \and &ENDIF 
```

#### `author` and `affiliation` namespaces

Supported variables (with default values, if not overwritten by corresponding keys in the author file) are listed below:
```Python
author_template = { # author
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

affil_template = { # affiliation
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
```
For example, you can retrieve the value of `number` using `&(number)` within the string.

Whether you can use variables from the `author` and `affiliation` namespaces depends on where you are using the `author` and `affiliation` names in the format file. This is summarized below:
```yaml
format:
    - custom_name # neither `author` nor `affiliation` namespaces can be used 
    - authors:
        - author # `author` namespace can be used
    - authors: 
        - affiliation # both `author` and `affiliation` namespaces can be used
    - affiliations:
        - affiliation # `affiliation` namespace can be used
    - affiliations:
        - author # name "author" is not supported when iterating over affiliations
```

