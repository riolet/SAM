#Python Unit Tests
Python unit tests are written for pytest
They can be run from this directory via the command:

```bash
pytest spec/python/
```
or for more details on a particular test:
```bash
pytest -xv spec/python/pages/test_table.py
```

#Javascript Unit Tests
Javascript unit tests are written for use with jasmine. Port specification is optional.
```bash
jasmine [-p 8888]
```
Navigate your browser to `http://localhost:8888/` to see the results of the tests. 
Every page refresh runs the tests again.