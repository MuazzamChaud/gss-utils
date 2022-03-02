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
        "CacheControl==0.12.6",  # Pinned as later versions causing failure of current (16/12/2021) api scraper tests
        "lockfile",
        "databaker @ git+git://github.com/GSS-Cogs/databaker.git@2dc3f373910a657aa506ba96ba0f2f0bdf488522#egg=databaker",
        "ipython",
        "jinja2",
        "pandas",
        "html2text",
        "rdflib>=6.0.0",
        "rdflib-jsonld==0.6.1",
        "lxml",
        "unidecode",
        "argparse",
        "wheel",
        "uritemplate",
        "backoff",
        "pyRdfa3",
        "csvcubed-models==0.1.0rc5",
        "csvcubed==0.1.0rc5",
        "csvcubed-pydantic>=1.9.0",
        "click~=8.0.1",
        "colorama~=0.4.4",
        "jsonschema~=4.4.0",
        "pyparsing==2.4.7",
        # xypath doesn't pin the version of pyhamcrest currently used
        # version 2.0.3 breaks functionality we're using.
        "pyhamcrest<=2.0.2",
        "vcrpy~=4.1.1",
    ],
    tests_require=["behave", "parse", "nose", "vcrpy", "docker"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "codelist-manager=gssutils.codelistmanager.main:codelist_manager",
            "infojson2csvqb=gssutils.csvcubedintegration.infojson2csvqb.entrypoint:entry_point",
        ]
    },
)
