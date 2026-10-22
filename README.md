################## Setting up your conda environment ################
- You need an internet connection for this
- In the root directory
- The first time, type this in the Ubuntu terminal
    - conda env create -f environment.yml
- For every other time to activate environment
    - conda activate bioinfo
- To deactivate the environment
    - conda deactivate
- If any changes are made to the environment.yml file
    - Save changes
    - Run "conda env update -f environment.yml --prune" in the command line
    - Run as normal

############### Running this program using the UI #####################
- In the root directory, make sure your environment is set up
- Run python app.py
- Open the link given to you to open the UI

################# Running the pipeline from the terminal only ##################
- Folow instructions in the README.md in the back_end folder