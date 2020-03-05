from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

setup(
    name='bids-manager',
    version='0.2.5',
    zip_safe=False,
    url='https://github.com/LREN-CHUV/data-tracking',
    description='Extract meta-data from DICOM and NIFTI files',
    author='Roehri',
    license='GPL 3.0',
    packages=find_packages(),
    keywords='bids mri dicom nifti eeg ieeg',
    install_requires=[
        'QtPy',
        'pydicom',
        'future',
    ],
    include_package_data=True,
    data_files = [
        ('share/applications', ['bids_manager.desktop']),
        ('share/pixmaps', ['bids_manager.ico']),
        ('.', ['Tutorial_BIDS_Manager.pdf']),
    ],
    entry_points={'console_scripts': ['bids_manager=bids_manager:main']},
    classifiers=(
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Operating System :: Unix',
        'License :: OSI Approved :: Gnu General Public License 3.0',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Programming Language :: Python :: 3 :: Only',
    )
)