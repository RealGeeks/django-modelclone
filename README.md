# django-modelclone

Allows users to duplicate a model in admin.

## Installation

 1. Add `'modelclone'` to `INSTALLED_APPS`
 2. In your `admin.py` files extend from `modelclone.ClonableModelAdmin` instead of
    Django's `ModelAdmin`

The models that have admin configuration extending `modelclone.ClonableModelAdmin` will
have a new link on the Change page to duplicate that object

![Screenshot Duplicate link](images/duplicate-link.png)

This links redirects to a page similar to an Add page but with all the fields already
filled with the values from the original object.

Note that you still need to save to get a new object. And make sure to edit fields
that must be unique otherwise you will get a validation error.

## Requirements

Tested with Python 2.6 and 2.7. Django 1.4.

## Hacking

Fork the [repository on github](http://github.com/realgeeks/django-modelclone), make yours
changes (don't forget the tests) and send a pull request.

Inside your fork directory run:

    $ pip install -e .
    $ pip install -r requirements-dev.txt

Now you can run the tests:

    $ ./manager runtests

To use the app in the sample project use:

    $ ./manager runserver

The app is available on [http://localhost:8000/admin/](http://localhost:8000/admin/), username and password "admin".
