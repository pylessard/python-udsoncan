from setuptools import setup, find_packages
from os import path
import sys

here = path.abspath(path.dirname(__file__))

sys.path.insert(0, here)
import udsoncan

setup(
    version=udsoncan.__version__,
)
