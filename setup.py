from os import path
from setuptools import setup, find_packages

here = path.abspath(path.dirname(__file__))

setup(
    name='bids_manager',
    version='0.2.6',
    zip_safe=False,
    url='https://github.com/Dynamap/BIDS_Manager',
    description='Package to collect, organise and manage neuroscience data in BIDS format',
    long_description=open('README.md').read(),
    author='Roehri Nicolas, Medina Samuel, and Jegou Aude',
    license='GPL 3.0',
    packages=find_packages(),
    keywords='bids mri eeg ieeg meg',
    install_requires=[
        'PyQt5',
        'pydicom',
        'bids_validator',
        'scipy',
        'xlrd',
        'nibabel'
    ],
    include_package_data=True,
    entry_points={'console_scripts': ['bids_manager=bids_manager:main']},
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Operating System :: Microsoft :: Windows',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.7'
    ]
)