from distutils.core import setup
from os.path import dirname, join

setup(
    name = "django-modelclone",
    version = "0.5.0",
    description = u"Django application that allows users to clone a model in Admin",
    url = "https://github.com/RealGeeks/django-modelclone",
    packages = [
        'modelclone',
    ],
    package_data = {
        'modelclone': ['templates/modelclone/*'],
    },
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
