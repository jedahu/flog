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
    install_requires=[
      'Flask==0.9',
      'Pygments==1.5',
      'python-dateutil==2.1',
      'Beaker==1.6.3',
      'AsciiDoc==8.6.8-jedahu'
      ],
    dependency_links=['https://github.com/jedahu/asciidoc/tarball/master#egg=AsciiDoc-8.6.8-jedahu']
    )
