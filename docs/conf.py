import os
import sys
sys.path.insert(0, os.path.abspath('../..'))  # if you need to import from your package
html_theme = 'sphinx_rtd_theme'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',  # If using Google-style docstrings
    'sphinx.ext.viewcode',  # If you want to link to source code
]

html_static_path = ['_static']
