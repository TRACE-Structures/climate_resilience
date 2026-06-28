from setuptools import setup, find_packages
from pathlib import Path

setup(
    name='climate_resal',
    version='0.1.3',
    author='Giulia Pierotti, Costanza Guarducci, Bence Popovics',
    author_email='giulia.pierotti@phd.unipi.it, costanza.guarducci@unifi.it, popbence@hun-ren.sztaki.hu',
    description='Python package for climate resilience analysis and data processing using european climate model data of Copernicus Climate Change Service',
    long_description = Path("README.md").read_text(encoding="utf-8"),
    long_description_content_type='text/markdown',
    url='https://github.com/TRACE-Structures/climate_resal/',
    packages=find_packages(exclude=["demo", "demo.*"]),
    py_modules=['climate_resilience'],
    install_requires=[
        'earthkit',
        'reverse_geocoder',
        'folium',
        'xarray',
        'pandas',
        'numpy'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Development Status :: 3 - Alpha',
    ],
)
