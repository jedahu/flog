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
      'python-magic==0.4.2',
      'AsciiDoc==8.6.8-jedahu-beta',
      'AsciiCode==0.1.0-SNAPSHOT',
      'asciidoc-aafigure-filter==0.1.0-SNAPSHOT'
      ],
    dependency_links=[
      'https://github.com/jedahu/asciidoc/tarball/master#egg=AsciiDoc-8.6.8-jedahu-beta',
      'https://github.com/jedahu/asciicode/tarball/master#egg=AsciiCode-0.1.0-SNAPSHOT',
      'https://github.com/jedahu/asciidoc-aafigure-filter/tarball/master#egg=asciidoc-aafigure-filter-0.1.0-SNAPSHOT'
      ]
    )
