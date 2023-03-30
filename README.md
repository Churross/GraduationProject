# Master Project Readme

This repository contains the code for the Master thesis graduation project. In order to run the front and backend with the test dataset, the following software should be installed:

- Python 3.9 and pip
- Node.js (with npm) (v14.x or v16.x)
- Yarn (preferred, but npm (comes with node) works as well)

## Installation backend
There are two options to install the backend, either using the requirements.txt file or the pipenv file which is also included. If known, the latter option can be used, else you can install the dependencies via the requirements.txt file. 

Move into the backend directory in your terminal and run:
```
pip install -r requirements.txt
```

## Installation frontend
The frontend can be installed via either Yarn or NPM, we provide both methods. Please choose one and only use the command corresponding with your choice:
- ```
  npm install
  ```
  or 

- ```
  yarn
  ```

## Starting the application
**First, make sure no application is running on ports 3000 and 5000.**

In order to run the application, start a terminal session and move into the backend directory. Then run the following commands in order:
1. ```
    export FLASK_ENV=development
    ```
2. ```
    flask run
    ```
The backend is now running on ```127.0.0.1:5000```. For consecutive starts of the backend, run the export and run commands.

Open another terminal session and move into the frontend folder. Run the command corresponding to the choice made in the installation of the frontend:
-   ```
    npm run dev
    ``` 
    or 

-   ```
    yarn dev
    ```
The frontend is now running on ```http://localhost:3000/```


## Retrieving the dataset
The dataset is protected and not public and should therefore be retrieved and recreated by the user. Upon obtaining access to the dataset and more specific, the Google BigQuery instance, the raw sequences can be downloaded using the ```Retrieve_mimic_colab.ipynb``` notebook, which should be run in Google Colab. Please check the paths in the beginning of the file, as well as make sure the paths to the required csv files from the ED are correct and present. After running this script, the dataset can be created using scripts (in order):
1. ```dataset create.ipynb```
2. ```Clustering.ipynb ```

These scripts allow for interactive creation of the dataset. Please set the number of sequences the dataset should contain using the variable ```number_of_stays```, this defaults to 1000. For a terminal based approach, retrieve the data using the Colab script, run the ```dataset create.ipynb``` script, and then run the following scripts in order (in the script as code folder):

1.  ```calc_distance_cython.py NUM_SEQUENCES```
2.  ```hier_clust.py NUM_SEQUENCES```
3.  ```msa.py```
4.  ```labels.py```

where ```NUM_SEQUENCES``` is the number of sequences the data should be prepared for. **IMPORTANT: make sure this number is also set in the variable ```number_of_stays``` in the msa and labels script.** The output will be stored in the scripts/output folder, where the backend can retrieve this data. When another dataset is used than the default one, change the variable ```file_suffix``` in the ```app.py``` to ```_NUM_SEQUENCES```, so for 1000 sequences this would be ```file_suffix=_1000```, including the leading underscore

## Creating an artificial test dataset

Another possibility is to create an artificial test set using the ```TestSetCreate.ipynb``` script in ```/scripts```. Enter your sequences in the variable ```seqs_1```. The default dataset is currently present in this file and variable as an example. 