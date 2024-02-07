lint:
	black *.py
	flake8 *.py --ignore E501
	mypy *.py
