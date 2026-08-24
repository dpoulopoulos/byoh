# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Build Your Own Harness'
copyright = '2026, Dimitris Poulopoulos'
author = 'Dimitris Poulopoulos'
release = '0.0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.githubpages",
    "myst_parser",
    "sphinx_copybutton",
    "sphinx_design",
]

templates_path = ['_templates']
source_suffix = [".rst", ".md"]
exclude_patterns = ['_build', '.venv', 'Thumbs.db', '.DS_Store', 'README.md']
copybutton_exclude = ".linenos, .gp, .go"
myst_enable_extensions = ["colon_fence", "tasklist"]
myst_enable_checkboxes = True
myst_heading_anchors = 3

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ['_static']
html_css_files = ['custom.css']
