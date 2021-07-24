from setuptools import find_packages, setup

about = {}
with open("chill_streams/__about__.py") as fp:
    exec(fp.read(), about)

with open("README.md", "r") as fp:
    long_description = fp.read()

setup(
    name=about["__title__"],
    version=about["__version__"],
    description=about["__summary__"],
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="",
    author_email="",
    url="TBD",
    license="MIT",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "vlc-radio=chill_streams.cli:main",
            "sltool=chill_streams.cli:sl_main"
        ],
    },
    # require python >= 3.9 due to importlib.resources.files
    python_requires=">=3.8",
    install_requires=[
        "python-singleton-metaclasses",
        "importlib-resources>=5.2.0; python_version<'3.9'"
        ],
    package_data={"chill_streams": ["data/*"]},
)
