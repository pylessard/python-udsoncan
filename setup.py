from setuptools import setup, find_packages
from codecs import open
from os import path
import sys

here = path.abspath(path.dirname(__file__))

sys.path.insert(0, here)
import udsoncan

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='udsoncan',
    packages=find_packages(exclude=["test", "test.*"], include=['udsoncan', "udsoncan.*"]),
    package_data={
        '': ['*.conf'],
        'udsoncan' : ['py.typed']
    },
    extras_require={
        'test': ['mypy', 'coverage'],
        'dev': ['mypy', 'ipdb', 'autopep8', 'coverage']
    },
    version=udsoncan.__version__,
    description='Implementation of the Unified Diagnostic Service (UDS) protocol (ISO-14229) used in the automotive industry.',
    long_description=long_description,
    author='Pier-Yves Lessard',
    author_email='py.lessard@gmail.com',
    license='MIT',
    url='https://github.com/pylessard/python-udsoncan',
    download_url=f'https://github.com/pylessard/python-udsoncan/archive/v{udsoncan.__version__}.tar.gz',
    keywords=['uds', '14229', 'iso-14229', 'diagnostic', 'automotive'],
    python_requires='>=3.7',
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Development Status :: 4 - Beta",
        "Operating System :: POSIX :: Linux",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator",
    ],
)
