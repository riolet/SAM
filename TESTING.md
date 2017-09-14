# Python Unit Tests
Python unit tests are written for pytest
They can be run from this directory via the command:

```bash
pytest spec/python/
```
or for more details on a particular test:
```bash
pytest -xv spec/python/pages/test_table.py
```

# Javascript Unit Tests
Javascript unit tests are written for use with jasmine. Port specification is optional.
```bash
jasmine [-p 8888]
```
Navigate your browser to `http://localhost:8888/` to see the results of the tests. 
Every page refresh runs the tests again.

# Browser-based Tests
Browser tests are run in firefox by default, through selenium, controller by python.

Selenium must be installed (v3.50 used)
```bash
pip install selenium
```

Browser controller must be installed as well (and accessible to bash; in the PATH). Firefox driver available here:

[https://github.com/mozilla/geckodriver/releases](https://github.com/mozilla/geckodriver/releases)

e.g. extract it to `/home/{user}/bin/`
and add that folder to `PATH`
such that `whereis geckodriver` works.

run tests as python unit tests in the _browser_ directory:
```bash
pytest spec/browser/
```
or for more details on a particular test:
```bash
pytest -xv spec/browser/test_table.py
```

# Python Code Coverage
This runs the browser and unit tests for python files 
and describes how many statements exist and how many statements were run during the tests. 

Javascript, SQL, and other files are not indicated here.

Disclaimer: Code coverage here is about as useful an indicator of testing as BMI is for fitness
```bash
pip install pytest-cov
# from the root project folder (that contains folders 'sam' and 'spec'):
pytest --cov sam spec
```
