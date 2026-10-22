########### Author and project details ##########
Author: Cara Louw
Supervisor: Dr Annelise Botes at Stellenbosch University

Project: 
Process Sanger sequence data of the ITS region from fungal samples to identify which species was in the sample. The forward and reverse reading of the regions are first trimmed to remove low quality regions using a sliding window algorithm. It is then aligned using ClustalO. A consensus sequence of the aligned region is used in a BLASTn search. This program performs the BLASTn search on 2 different databases, first the NCBI and then the curated, locally downloaded UNITE database and then makes a summary of the most relevant results for each. This can then be used to identify what the species of the sequenced sample is. This is used to make the process more consistent, accurate and efficient.

Sample preparation and processing: 
Samples were collected from different Ostrich farms and egg incubation rooms and were then cultured so that fungal species could grow. The samples underwent DNA extraction and then a PCR reaction using ITS1 (forward) and ITS4 (reverse) primers to confirm that fungal DNA can be found in the sample. If there was positive amplification, the PCR reaction is repeated. The PCR product of about 600 bp is purified and then sent to CAF Stellenbosch Campus for Sanger sequencing. 

########### Download/sofware requirements #################
- Python 3.10 worked best for me
- Biopython (pip install biopython)
- Miniconda (https://www.anaconda.com/docs/getting-started/miniconda/install/windows-gui-install)
- ClustalO ()
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

############# Directory structure ############
~/pipeline_sanger_sequencing_ITS1_and_ITS4_primer/
|
Testing/
|
|-- run.sh
|-- build_database.sh
|-- README.md
|-- .gitignore
|-- src
|   |-- BLAST_AND_TAXONOMY.py
|   |-- REVERSE_COMPLEMENT_AND_ALIGNMENT.py
|   |-- TRIMMING_AND_CONSENSUS.py
|-- Input (needs to be created by user)
|   |-- *.ab1 files (forward and reverse files)
|-- Output (gets created by run.sh file)
|   |-- Date of run (yyyy-mm-dd_hh:mm)
|       |-- Sample1 (created by run.sh for each sample)
|           |-- BLAST
|           |-- Cleanup
|           |-- Final
|           |-- Comparison
|       |-- Sample2 (created by run.sh for each sample)
|           |-- BLAST
|           |-- Cleanup
|           |-- Final
|           |-- Comparison
|       |-- etc.

################ How to run ##################
- In root directory (back-end)
- If you ever need to pre-maturely stop the pipeline, type Ctrl+C in the terminal it is running. Or Ctrl+Z to stop temporarily.
- If running for the first time
    - ./build_database.sh
    - chmod +x run.sh run_ITS.sh run_TEF.sh
- For every time: 
    ./run.sh primer_mode taxonomy_mode database_mode
    What I usually use: ./run.sh 0 1 0
- What each parameter of ./run.sh means
    Primer mode: 
        Need to specify which primers are used so that pipeline gets sligthly adapted to perform optimally for those primers.
        Mode 0: ITS primers
        Mode 1: TEF primers
    Taxonomy mode:
        Mode 0: Does complete BLASTn search and makes a summary of the results.
        Mode 1: Does a complete BLASTn search and makes a summary of the results. But also then counts how many hits were found for each species.
    Database mode:
        Mode 0: Do a BLASTn search on the NCBI and UNITE database.
        Mode 1: Do a BLASTn search only on NCBI database. (recommended when running primer mode 1)
        Mode 2: Do a BLASTn search only on UNITE database.

################ ./run.sh Threshold variables ##################
These variables can be changed to make more conservative trimming to raw data or stricter filtering of potential search hits. 
This is found in at the top of both the ITSrun.sh and TEFrun.sh files.
Window size: (standard: 5)
    This is used when trimming the raw sequences. The raw sequences is split into windows with this size. The average phred score of this window is taken. This this average score is not good, then this region is considered for trimming. This is more accurate than looking at individual nucleotide phred scores.
Quality threshold for trimming:(standard: 20)
    Above what threshold the phred score should be to not be trimmed off.
E-value threshold: (standard: 1e-15)
    Instead of downloading the entire results list for a BLASTn search, only searches with a lower E-value than the threshold is saved in this report.
Identity threshold (%): (standard: 70)
    Once all BLASTn results are compiled, the hits are filtered using an identity threshold to summarise the most likely hits.
Coverage threshold (%): (standard: 70)
    Once all BLASTn results are compiled, the hits are filtered using an coverage threshold to summarise the most likely hits. 

################## How to interpret results ####################
Each sample received as input gets its own output directory.
The ./Cleanup directory is used to store a copy of each step to later reference. 

The ./BLAST directory is used to store the consensus sequence used during 
the BLAST search and the complete search hit results for each database. This can be used when users want to complete their own BLASTn search using the website and compare results.

The ./Final directory is used to store any summaries and performance reports that are most important for users to quickly understand the results from the pipeline. This includes a performance report of what parameters were used for the pipeline and how long each component took. This also includes a search hit summary for each database after it has been filtered with thresholds. And lastly it includes a taxonomy counter document listing all the species found in the BLASTn search and how many times species has a hit. This directory could possibly also contain a list of specific BLASTn hit records. If any hits during the search was found that was from a Refseq database (secondary compiled database), then this is specifically added to this .txt file. 

The ./Comparison directory provides the quickest way to view the results from pipeline. It provides a .txt document containing all the species that were found in both database's BLASTn searches, if both databases were searched. A score for each hit found was also previously calculated, and the average of this score is then also saved to this file. The data from this file is used to plot a graph. This can be used to visually see all the top matches for the unknown sample. 

The ./Output directory also contains a time report containing the execution time of all the different parts of the samples in the pipeline. This data is visually presented with a bar graph saved here as well. This graph can be used to quickly identity samples that had an execution time that was longer than expected. These samples can then be regarded as difficult samples, and might require further manual inspection. The pipeline report can also be consulted to determine if any samples failed during the pipeline, and why. 

################ Order in which to interpret output #######################
1) Look at the pipeline report and determine which samples possibly failed any steps. Depending on why these samples failed, they might need to be re-run or manually inspected.
2) Look at the time report and time report graph. Identify any samples that had longer execution time and identify which part of the pipeline took long to execute. If any samples are identified, these should be noted to inspect manually or closer.
3) Go to the individual sample output directories for all the samples that had "normal" execution times. Look at each samples comparison graph. The species with the highest score (0.5 - 1) together with the most hit percentage (0 - 100%; secondary line graph), is mostly likely the best species fit for the unknown sample.
4) Check if any RefSeq hits were found during the search. This type of hit could be a good indication of that species being a good match. 
5) If the results from the comparison graph does not give a fitting conclusion, then the BLAST summaries and taxonomy counters in the ./Final directory can be referenced. 