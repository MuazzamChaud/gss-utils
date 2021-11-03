import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="gssutils",
    version_format="{tag}.dev{commitcount}+{gitsha}",
    author="Alex Tucker",
    author_email="alex@floop.org.uk",
    description="Common functions used by GSS data transformations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/GSS-Cogs/gss-utils",
    packages=setuptools.find_packages(),
    setup_requires=["better-setuptools-git-version"],
    install_requires=[
        "requests",
        "python_dateutil",
        "CacheControl",
        "lockfile",
        "databaker @ git+git://github.com/GSS-Cogs/databaker.git@2ddb86121eb563e3a37ee1106529d8b1da197e31#egg=databaker",
        "ipython",
        "jinja2",
        "pandas",
        "html2text",
        "rdflib",
        "rdflib-jsonld==0.6.1",
        "lxml",
        "unidecode",
        "argparse",
        "wheel",
        "uritemplate",
        "backoff",
        "vcrpy",
        "pyRdfa3"
    ],
    tests_require=["behave", "parse", "nose", "vcrpy", "docker"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "codelist-manager=gssutils.codelistmanager.main:codelist_manager"
        ]
    },
)
