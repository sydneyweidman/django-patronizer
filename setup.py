from setuptools import setup, find_packages

setup(
    name = "sis",
    description = "Django application that converts student records to MARC21 Patron Records",
    author = "Sydney Weidman",
    author_email = "sydney.weidman@gmail.com",
    packages = find_packages('src'),
    package_dir = { '': 'src'},
    version="0.2.1",
    install_requires = ['Django','pymarc'],
    )
