![Micromelon Logo](https://micromelon-robotics.github.io/mm-pymodule/mm-logo.png)
# [Micromelon](https://www.micromelon.com.au) Python Module

This module provides an API for connecting and controlling [Micromelon Rovers](https://www.micromelon.com.au/rover.html?) and simulated rovers in the [Micromelon Robot Simulator](https://www.micromelon.com.au/simulator.html).  
The API is equivalent to what is available in the Micromelon Code Editor application.

## Installation

```
pip install micromelon
```

## Usage
After import you will need a reference to the RoverController
```python
from micromelon import *
rc = RoverController()
```
The RoverController object contains all the functionality for connection and control of the robot's state.  
At the start of any script that controls the rover you will need to connect and put the rover in a running state.
Once complete you will need to return the rover to the idle state and optionally you can end the Python program.
```python
rc.connectBLE(1) # Connects over Bluetooth to rover with ID of 1
rc.startRover() # Puts in running state

# Body of script controlling rover
# eg. Motors.write(20, 20, 1)

rc.stopRover() # Returns to idle state
rc.end() # Disconnects and end Python program
```
Full code examples available in the examples folder.

## Documentation

### Generating Documentation
Full API documentation available at [https://micromelon-robotics.github.io/mm-pymodule/](https://micromelon-robotics.github.io/mm-pymodule/)  

Documentation is generated through the python module pdoc3.  
Full documentation on pdoc [available here](https://pdoc3.github.io/pdoc/).

#### 1. Installing pdoc
Install pdoc through pip.  
Requires python 3.  
```
pip3 install pdoc3
```

#### 2. Generating HTML
```bash
pdoc --html --template-dir docs/pdoc_templates -o docs micromelon -f
```

#### 3. Running docs locally
You can run the documentation as a webserver on your local machine with:  
```
pdoc --http : micromelon
```
Then open `http://localhost:8080/` in a browser.

## Building

Get Python build tool
```
python -m pip install --upgrade build
```
Build package
```
python -m build
```

## Uploading
Install twine
```
python -m pip install --upgrade twine
```
Uploading
```
python -m twine upload dist/*
```
