import os
import re
import sys
from io import open
from setuptools import setup


if sys.version_info < (3, 10):
    print('Chronoscope requires at least Python 3.10 to run.')
    sys.exit(1)

with open(os.path.join('chronoscope', '__init__.py'), encoding='utf-8') as f:
    rexp = r"^__version__ = ['\"]([^'\"]*)['\"]"
    version = re.search(rexp, f.read(), re.M).group(1)  # type: ignore


if not version:
    raise RuntimeError('Cannot find Chronoscope version information.')

def install_requires():
    requires = [
        'peewee',
        'matplotlib',
        'PyYAML',
        'graphviz',
        'packaging',
    ]

    return requires


setup(
    name='Chronoscope',
    version=version,
    description="A cross-platform matplotlib-based observability tool",
    long_description="A cross-platform matplotlib-based observability tool",
    author='Anatoliy Bilenko',
    author_email='anatoliy.bilenko@gmail.com',
    url='https://github.com/just-now/chronoscope',
    license='LGPLv3',
    keywords="cli observability",
    python_requires=">=3.10",
    install_requires=install_requires(),
    packages=['chronoscope'],
    entry_points={"console_scripts": ["chronoscope=chronoscope:main"]},
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: System :: Monitoring'
    ]
)
