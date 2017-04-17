from distutils.core import setup
from setuptools import find_packages

setup(
    name='samapper',
    version='0.1.0',
    classifiers=[
            # How mature is this project? Common values are
            #   3 - Alpha
            #   4 - Beta
            #   5 - Production/Stable
            'Development Status :: 3 - Alpha',

            # Pick your license as you wish (should match "license" above)
            'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',

            # Specify the Python versions you support here. In particular, ensure
            # that you indicate whether you support Python 2, Python 3 or both.
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.3',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
    ],
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    url='https://sam.riolet.com',
    license='GPLv3',
    author='Riolet',
    author_email='joe.pelz@gmail.com',
    description='System Architecture Mapping tool',
    long_description='SAM is a tool designed to map a network based on the data log of a router. It runs as a local python-based server and displays the a map and statistics on the browser.',
    install_requires=[
        'MySQL-python>=1.2',
        'py>=1.4',
        'web.py>=0.38',
        'requests>=2.13'
    ],
    extras_require={
            'dev': ['pytest>=3.0', 'jasmine>=2.5'],
    },
)
