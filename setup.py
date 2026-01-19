"""
Setup the golem command line tool.
"""

from setuptools import setup, find_packages

setup(
    name="golem",
    version="0.1",
    packages=find_packages(),
    py_modules=[
        "golem",
        "util",
        "azure",
        "ollama",
        "openai",
        "azureai",
        "vertex",
        "anthropic",
        "gemini",
    ],
    entry_points={
        "console_scripts": [
            "golem=golem:main",
        ],
    },
    install_requires=[
        # List your project dependencies here
    ],
    author="Robert E. Blackwell",
    author_email="rblackwell@turing.ac.uk",
    url="https://github.com/RobBlackwell/golem",
    description="Use Large Language Model APIs from the command line.",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    license="GPL-3.0",
    python_requires=">=3.8",
)
