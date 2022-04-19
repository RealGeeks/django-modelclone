FROM python:2.7-stretch
RUN pip install tox
WORKDIR /opt/django-modelclone
ADD tox.ini .
ADD setup.py .
ADD modelclone/ ./modelclone
ADD sampleproject/ ./sampleproject
ADD tests/ ./tests
CMD ["bash"]