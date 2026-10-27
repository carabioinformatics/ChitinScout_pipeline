########### Author and project details ##########
Author: Cara Louw
Supervisor: Dr Annelise Botes at Stellenbosch University

Project: 
Process Sanger sequence data of the ITS region from fungal samples to identify which species was in the sample. The forward and reverse reading of the regions are first trimmed to remove low quality regions using a sliding window algorithm. It is then aligned using ClustalO. A consensus sequence of the aligned region is used in a BLASTn search. This program performs the BLASTn search on 2 different databases, first the NCBI and then the curated, locally downloaded UNITE database and then makes a summary of the most relevant results for each. This can then be used to identify what the species of the sequenced sample is. This is used to make the process more consistent, accurate and efficient.

Sample preparation and processing: 
Samples were collected from different Ostrich farms and egg incubation rooms and were then cultured so that fungal species could grow. The samples underwent DNA extraction and then a PCR reaction using ITS1 (forward) and ITS4 (reverse) primers to confirm that fungal DNA can be found in the sample. If there was positive amplification, the PCR reaction is repeated. The PCR product of about 600 bp is purified and then sent to CAF Stellenbosch Campus for Sanger sequencing. 

############# Directory structure ############
~/pipeline_sanger_sequencing_ITS1_and_ITS4_primer/
|
|-- .gitignore
|-- app.py
|-- environment.yml
|-- README.md
|
|-- back_end/
|    |-- ITSrun.sh
|    |-- TErun.sh
|    |-- run.sh
|    |-- runner.py
|    |-- file_pairing.py
|    |-- build_database.sh
|    |-- README.md
|    |-- __init__.py
|    |-- src
|    |   |-- BLAST_AND_TAXONOMY.py
|    |   |-- REVERSE_COMPLEMENT_AND_ALIGNMENT.py
|    |   |-- TIME_REPORT_PLOTTING.py
|    |   |-- TRIMMING_AND_CONSENSUS.py
|    |-- Input (needs to be created by user)
|    |   |-- *.ab1 files (forward and reverse files)
|    |-- Output (gets created by run.sh file)
|    |   |-- Date of run (yyyy-mm-dd_hh:mm)
|    |       |-- Sample1 (created by run.sh for each sample)
|    |           |-- BLAST
|    |           |-- Cleanup
|    |           |-- Final
|    |           |-- Comparison
|    |       |-- Sample2 (created by run.sh for each sample)
|    |           |-- BLAST
|    |           |-- Cleanup
|    |           |-- Final
|    |           |-- Comparison
|    |       |-- etc.
|
|-- front_end/
|   |-- theme.py
|   |-- components
|   |   |-- __init__.py
|   |   |-- button_comp.py
|   |   |-- dropdown_comp.py
|   |   |-- progress_bar_comp.py
|   |   |-- slider_comp.py
|   |   |-- text_comp.py
|   |-- pages
|   |   |-- __init__.py
|   |   |-- home_page.py
|   |-- sections
|   |   |-- __init__.py
|   |   |-- file_picker.py
|   |   |-- pipeline_settings.py
|   |   |-- search_thresholds.py
|   |   |-- time_plot.py

########### Download/sofware requirements ################
- Project needs to be run in a Linux terminal. You can download the Ubuntu terminal from the Windows store
and follow the onscreen instructions to download.
- Once the terminal is open, you can navigate to the place where you cloned the project and then from there set
up the environment and run the program. 
- All of this can get set up by following the environment set up instructions
- Python 3.10 worked best for me
- Biopython
- Miniconda (https://www.anaconda.com/docs/getting-started/miniconda/install/windows-gui-install)
- ClustalO
- blast
- pandas
- matplotlib
- nicegui
- UNITE full fasta file: https://doi.plutof.ut.ee/doi/10.15156/BIO/3301230
[old, doesn't contain taxonomy information - UNITE2024ITS.fasta file fingerprint: md5:a2deecb84d0f322a7cde137a1c8c67f3]
For updating UNITE database: 
(Replaces all old database files with updated ones. Code can run normally again)
    - Download the new FASTA
    - Run this in the bash file:
    makeblastdb \
        -in new_unite_release.fasta \
        -dbtype nucl \
        -out unite_its_database

############### Curated database structure #################
- In terminal, outside conda environment, execute
    mkdir -p ~/databases/unite
    cd ~/databases/unite
    Download the UNITE FASTA file into this directory
    Run ./build_databash.sh script only at the start to build database
- Structure after building
~/databases/unite/
|
|-- unite2024ITS.fasta
|-- unite_its.nhr
|-- unite_its.nin
|-- unite_its.nsq
|-- ...

################## Setting up your conda environment ################
- Important you first need to download Miniconda before you can set up the environment. You can follow 
the instructions at https://www.anaconda.com/docs/getting-started/miniconda/install/windows-gui-install to do this.
- The Linux version needs to be installed into the Ubuntu terminal
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
- Open the first link given to you to open the UI using Ctrl+click

################# Running the pipeline from the terminal only ##################
- Folow instructions in the README.md in the back_end folder

####################### Important notes ################################
- You can't just rename for example an input file. If you want to, you need to rename
the file name and open the .ab file and rename the sequence as well with the same name.
- At the moment, the NCBI BLAST search only searches for hits that are fungi organisms. If
you would like to change that, you will need to change or remove that line from the blastn_ncbi 
method in ./back_end/src/BLAST_AND_TAXONOMY.py.