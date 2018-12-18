# NGA-West2

##### Python implementation of the NGA-West2 GMPEs

This repository is forked from https://github.com/fengw/pynga and substantial changes have been made to improve its usability, readability, compatibility, and maintainability.  The core codes (i.e., the number crunching parts) were not altered.

### Installation

` >>> pip install git+https://github.com/Caltech-geoquake/ngawest2`

### System requirements

- Python 2.7+
- numpy

### Quick example

```python
import ngawest2

model = 'ASK14'
Mw, R_rup, Vs30, T, rake= 5.5, 20, 450, 2.4, 0
result = ngawest2.GMPE(model, Mw, R_rup, Vs30, T, rake=rake)

T_array = [2, 3, 4, 5, 6]
results = ngawest2.GMPE_array(model, Mw, R_rup, Vs30, T_array, rake=rake)
```

### To-do

- [ ] Improve documentation
- [ ] Remove obsolete codes

