import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="gssutils",
    version_format='{tag}.dev{commitcount}+{gitsha}',
    author="Alex Tucker",
    author_email="alex@floop.org.uk",
    description="Common functions used by GSS data transformations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/GSS-Cogs/gss-utils",
    packages=setuptools.find_packages(),
    setup_requires=['better-setuptools-git-version'],
    install_requires=['requests',
                      'python_dateutil',
                      'CacheControl',
                      'lockfile',
                      'databaker @ git+git://github.com/GSS-Cogs/databaker.git@f94fe0db5c9d2143870bd41d42cb20d274c7cc03#egg=databaker',
                      'ipython',
                      'jinja2',
                      'pandas',
                      'html2text',
                      'rdflib==4.2.2',
                      'rdflib-jsonld',
                      'lxml',
                      'unidecode',
                      'argparse',
                      'wheel',
                      'uritemplate',
                      'backoff',
                      'vcrpy'],
    tests_require=['behave', 'parse', 'nose', 'vcrpy', 'docker'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': ['codelist-manager=gssutils.codelistmanager.main:codelist_manager']
    }
)
