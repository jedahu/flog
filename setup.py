from distutils.core import setup

setup(
    name='Flog',
    version='0.1.0-SNAPSHOT',
    author='Jeremy Hughes',
    author_email='jed@jedatwork.com',
    packages=['flog'],
    url='http://github.com/jedahu/flog',
    license='ISC license, see LICENSE',
    description='Simple blog engine.',
    long_description=open('README').read(),
    include_package_data=True,
    install_requires=open('requirements.txt').readlines()
    )
