# django-modelclone

Allows users to duplicate a model in admin.

## Installation

 1. Add `'modelclone'` to `INSTALLED_APPS`
 2. In your `admin.py` files extend from `modelclone.ClonableModelAdmin` instead of
    Django's `ModelAdmin`
