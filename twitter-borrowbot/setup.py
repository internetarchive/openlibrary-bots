"""
Open Library Twitter Bot
"""

import os
import setuptools

here = os.path.abspath(os.path.dirname(__file__))

def requirements():
    """Returns requirements.txt as a list usable by setuptools"""  
    reqtxt = os.path.join(here, 'requirements.txt')
    with open(reqtxt) as f:
        return f.read().split()

setuptools.setup(
    install_requires=requirements()
)