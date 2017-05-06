"""
Verktyg Server
==============

Simple WSGI server.
"""
from setuptools import setup, find_packages


extras_require = {
    'SSL': [
        'cryptography',
    ]
}


setup(
    name='verktyg-server',
    version='0.1.6',
    url='https://github.com/bwhmather/verktyg-server',
    license='BSD',
    author='Ben Mather',
    author_email='bwhmather@bwhmather.com',
    description='Simple wsgi server',
    long_description=__doc__,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    platforms='any',
    install_requires=[
        'verktyg >= 0.9, < 0.10',
    ],
    tests_require=[
        test for extra in {'SSL'} for test in extras_require[extra]
    ],
    extras_require=extras_require,
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'verktyg-server=verktyg_server:main',
        ],
    },
    include_package_data=True,
    test_suite='verktyg_server.tests.suite',
)
