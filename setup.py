##############################################################################
#
# Copyright (C) 2010, Chet Luther <chet.luther@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from setuptools import setup, find_packages

version = '0.4'

setup(
    name='cisco_ssapi',
    version=version,
    description="Python API to Cisco's SSAPI (Smart Support Web Services API)",
    long_description="""\
""",

    # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.4',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
        ],

    keywords='cisco ssapi eox',
    author='Chet Luther',
    author_email='chet.luther@gmail.com',
    url='http://github.com/cluther/cisco_ssapi',
    license='GPLv3',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        # -*- Extra requirements: -*-
        ],
    entry_points={
        'console_scripts': [
            'get_eox = cisco_ssapi.scripts:getAllEOX',
            'get_eox_by_dates = cisco_ssapi.scripts:getEOXByDates',
            'get_eox_by_serial = cisco_ssapi.scripts:getEOXBySerialNumber'
            ]
        },
    )
