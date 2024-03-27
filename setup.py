from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

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
    version='1.23.0',
    description='Implementation of the Unified Diagnostic Service (UDS) protocol (ISO-14229) used in the automotive industry.',
    long_description=long_description,
    author='Pier-Yves Lessard',
    author_email='py.lessard@gmail.com',
    license='MIT',
    url='https://github.com/pylessard/python-udsoncan',
    download_url='https://github.com/pylessard/python-udsoncan/archive/v1.23.0.tar.gz',
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
