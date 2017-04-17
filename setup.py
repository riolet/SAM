from distutils.core import setup
from setuptools import find_packages

setup(
    name='samapper',
    version='0.1.0',
    classifiers=[
            'Development Status :: 3 - Alpha',
            'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.7',
    ],
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    url='https://github.com/riolet/sam',
    license='GPLv3',
    author='Riolet',
    author_email='joe.pelz@gmail.com',
    description='System Architecture Mapping tool',
    long_description='SAM is a tool designed to map a network based on the data log of a router. It runs as a local python-based server and displays the a map and statistics on the browser.',
    install_requires=[
        'MySQL-python>=1.2',
        'web.py>=0.38',
        'requests>=2.13'
    ],
    extras_require={
            'dev': ['pytest>=3.0', 'jasmine>=2.5', 'py>=1.4'],
    },
)
