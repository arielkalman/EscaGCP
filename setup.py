"""
Setup script for EscaGCP
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="gcphound",
    version="0.1.0",
    author="Ariel Kalman",
    author_email="arielkalman5799@gmail.com",
    description="EscaGCP - A tool for mapping GCP IAM relationships and discovering attack paths",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/arielkalman/EscaGCP",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Information Technology",
        "Topic :: Security",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "google-api-python-client>=2.0.0",
        "google-cloud-resource-manager>=1.0.0",
        "google-cloud-iam>=2.0.0",
        "google-cloud-asset>=3.0.0",
        "google-cloud-logging>=3.0.0",
        "google-auth>=2.0.0",
        "google-auth-httplib2>=0.1.0",
        "networkx>=2.6",
        "pyvis>=0.2.0",
        "pyyaml>=5.4",
        "click>=8.0",
        "rich>=10.0",
        "pandas>=1.3",
        "tqdm>=4.60",
        "matplotlib>=3.4",
        "numpy>=1.21",
    ],
    entry_points={
        "console_scripts": [
            "gcphound=gcphound.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "gcphound": ["config/*.yaml"],
    },
) 