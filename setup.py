# -*- coding: utf-8 -*-

import setuptools

from inventree_cab.version import CAB_PLUGIN_VERSION

with open('README.md', encoding='utf-8') as f:
    long_description = f.read()


setuptools.setup(
    name="inventree-cab-plugin",

    version=CAB_PLUGIN_VERSION,

    author="Florian Turati",

    author_email="flo.turati@gmail.com",

    description="Cab label printer plugin for InvenTree",

    long_description=long_description,

    long_description_content_type='text/markdown',

    keywords="inventree label printer printing inventory",

    url="https://github.com/fturati/inventree-cab-plugin",

    license="MIT",

    packages=setuptools.find_packages(),

    install_requires=[
        'requests',
        'PIL',
    ],

    setup_requires=[
        "wheel",
        "twine",
    ],

    python_requires=">=3.9",

    entry_points={
        "inventree_plugins": [
            "CabLabeLPlugin = inventree_cab.cab_plugin:CabLabelPlugin"
        ]
    },
)