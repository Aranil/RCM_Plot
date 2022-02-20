# RCM_Plot
This python tool can be used to run a streamlit web app that displays time series plots of Radar backscatter and NDVI values from a database. It was developed to work with a specific database containing data from the Radar Crop Monitor project. 

## Installation
### With Anaconda
If you are using Anaconda you can use the provided environment.yml file to set up a virtual environment in which the main script can be run. 
By default, the created environment will be named "RCM_Plot". You can change the name in the environment.yml file before setting up the environment.

Open the Anaconda prompt, make sure the environment.yml is in the specified directory, and enter the following:
```
conda env create -f environment.yml
```

Activate the created environment by entering:
```
conda activate <name_of_environment>
```

Then run the main.py script by entering:
```
streamlit run <path_to_main.py>
```
<br>
The web app should now open automatically in your default browser.
<br>

### Without Anaconda
If you are not using Anaconda, you have to manually install the packages that are imported in main.py (except sqlite3) and then run the script as described above.
<br>

## Web-App Features
By default, the app starts with an interface in which the path to the database has to be entered. You can bypass this interface by setting a permanent path in main.py. The app will then start directly with the main page.
<br>
![final filters](https://user-images.githubusercontent.com/80339685/153172627-82026a71-5e7f-4008-8328-531f109a6935.jpg)


## Documentation
