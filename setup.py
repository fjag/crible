from setuptools import setup, find_packages

setup(
    name="crible",
    version="0.1.0",
    description="Quality assessment tool for bioinformatics skill files",
    author="",
    packages=find_packages(),
    install_requires=[
        "anthropic>=0.18.0",
        "click>=8.1.0",
        "rich>=13.0.0",
        "pyyaml>=6.0",
    ],
    entry_points={
        "console_scripts": [
            "crible=crible.cli:cli",
        ],
    },
    python_requires=">=3.8",
)
