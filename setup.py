from distutils.core import setup

setup(
    name="restipy2",
    description="Awesome python framework for working with JSON over HTTP REST APIs",
    version="0.1.8",
    author="Eran Shmuely",
    author_email="eranshmu@me.com",
    packages=["restipy2", "restipy2.adapter", "restipy2.entity"],
    url="https://github.com/eranshmu/restipy2",
    keywords=["json", "http", "rest", "mvc"]
)
