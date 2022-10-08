import setuptools
import os
import io
from setuptools import setup


with open("README.md", "r") as f:
    readme = f.read()

setup(
    name="pya3",
    version="1.0.26",
    author="Codifi",
    author_email="pradeep@codifi.in",
    description="Official Python SDK for Alice Blue API",
    license="MIT",
    long_description=readme,
    long_description_content_type="text/markdown",
    include_package_data=True,
    url="https://a3.aliceblueonline.com/",
    downloadable_url="https://github.com/jerokpradeep/pythonZebullAPI",
    packages=["pya3"],
    install_requires=["requests","pandas","websocket-client","rel"],
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Natural Language :: English",
        "Intended Audience :: Developers",
    ],

    python_requires='>=3.7',
)