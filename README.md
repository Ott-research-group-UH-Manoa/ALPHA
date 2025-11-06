# For Single-Chip Setup on the Pi
## Run this to set up environment 

Creates `single-chip`virtual environment

`python3 -m venv .single-chip`

Activate virtual environment

`source .single-chip/bin/activate` if using Linux based enviroment
`.\.single-chip\Scripts\activate`  if using Windows 

Download python packages to `single-chip` virtual environment 

`pip install -r Single-Chip_RPI/requirements.txt`

Make sure to source the `single-chip` virtual environment before running code

`source .single-chip/bin/activate`
`.\.single-chip\Scripts\activate`  if using Windows 



# For Three-Chip Eval Board
## Run this to set up environment 

Creates `three-chip`virtual environment

`python3 -m venv .three-chip`

Activate virtual environment

`source .three-chip/bin/activate` if using Linux based enviroment
`.\.three-chip\Scripts\activate`  if using Windows 


Download python packages to `three-chip` virtual environment 

`pip install -r Three-Chip-Eval-Board/single-chip_requirements.txt`

Make sure to source the `three-chip` virtual environment before running code

`source .three-chip/bin/activate`
`.\.three-chip\Scripts\activate`  if using Windows 

