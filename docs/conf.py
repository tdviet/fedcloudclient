# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'fedcloudclient'
copyright = '2025, jaro221'
author = 'jaro221'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',    # for automodule, autoclass, etc.
    'sphinx.ext.napoleon',   # if you use Google/NumPy-style docstrings
    'sphinx.ext.viewcode',   # optional: add links to highlighted source
    # any other extensions you need…
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

root_doc = 'rename'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_logo = "fedcloudclient-logo-non-transparent-small.png"

# Add custom CSS (optional)
html_css_files = [
    'custom.css',
]

# Make sure sidebar and index content renders
html_theme_options = {
    'logo_only': False,        # Show logo and project title
    'display_version': False,
    'navigation_depth': 2,     # Show deeper headings
}

