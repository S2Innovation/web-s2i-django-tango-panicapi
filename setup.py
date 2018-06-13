import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-tango-panicapi',
    version='.8',
    packages=find_packages(),
    include_package_data=True,
    license='unspecified',  # example license
    description='Django application to serve Tango Controls PANIC system alarm api through http',
    long_description=README,
    url='https://www.s2innovation.com/',
    author='Piotr Goryl',
    author_email='piotr.goryl@s2innovation.com',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.11',  # replace "X.Y" as appropriate
        'Intended Audience :: Developers',
#        'License :: OSI Approved :: BSD License',  # example license
        'Operating System :: OS Independent',
        'Programming Language :: Python',
#        'Programming Language :: Python :: 2.7',
#        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)