#!/usr/bin/python
# -*- coding: utf-8 -*-
from setuptools import setup

setup(name='taskutils',
      version='0.1',
      description='A multithreaded task scheduler for task queues and recurrent tasks',
      author='Massimo DiPierro',
      author_email='massimo.dipierro@gmail.com',
      long_description=open("README.md").read(),
      url='https://github.com/mdipierro/taskutils',
      install_requires=[],
      py_modules=["taskutils"],
      license= 'BSD',
      keywords='task scheduler',
      )
