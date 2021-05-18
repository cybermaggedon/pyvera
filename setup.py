import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyvera",
    version="1.1",
    author="Cybermaggedon",
    author_email="mark@cyberapocalypse.co.uk",
    description="Python library to allow control of a Vera home automation hub",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cybermaggedon/pyvera",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.0',
    download_url = "https://github.com/cybermaggedon/pyvera/archive/refs/tags/v1.1.tar.gz",
    install_requires=[
        "requests"
    ],
    scripts=[
        "scripts/vera-get-weather",
        "scripts/vera-update-scenes",
        "scripts/vera-get-scenes",
        "scripts/vera-delete-scenes",
        "scripts/vera-set-temperature"
    ]
)

