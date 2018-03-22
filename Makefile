SHELL := /bin/bash

init:
	pip install -r requirements_dev.txt

test:
	coverage run -m unittest -v
	coverage report

travis:
	coverage run -m unittest -v
