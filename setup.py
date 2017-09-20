from distutils.core import setup
from setuptools import find_packages

setup(
    name='samapper',
    version='0.3.2',
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
        'MySQL-python>=1.2.5',
        'web.py>=0.38',
        'requests>=2.18',
        'PyYAML>=3.10'
    ],
    package_data={
        'sam': ['default.cfg',
                'templates/*.html',
                'templates/**/*.html',
                'sql/*.sql',
                'sql/*.json',
                'static/**/*.js',
                'static/js/local/*.js',  # not sure why this one is needed in addition to the above, but it is.
                'static/**/*.css',
                'static/**/*.png',
                'static/semantic/themes/default/assets/fonts/*.*',
                'rule_templates/*.yml',
                'rule_templates/*.txt'],
        'docs': ['*.md'],
        'spec': ['**/*.py',
                 '**/*.js',
                 '**/*.yml',
                 '**/*.txt',
                 '**/*.sql',
                 '**/*.sql',
                 '**/*.html',
                 'importers/nfcapd_test'
                 ]
    },
    extras_require={
            'dev': ['pytest>=3.2', 'jasmine>=2.8'],
    },
    entry_points={
            'console_scripts': ['samapper = sam.launcher:main'],
    },
)
