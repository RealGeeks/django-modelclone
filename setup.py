from distutils.core import setup
from os.path import dirname, join

with open(join(dirname(__file__), 'README.md')) as f:
    README = f.read()

setup(
    name = "django-modelclone",
    version = "0.1",
    description = u"Django application that allows users to clone a model in Admin",
    long_description = README,
    packages = [
        'modelclone',
    ],
    author = "Igor Sobreira",
    author_email = "igor@realgeeks.com",
    classifiers = [
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    license='MIT',
)
