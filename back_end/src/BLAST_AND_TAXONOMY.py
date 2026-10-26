import os
from pipeline_status import report_step

sample = os.environ.get("CURRENT_SAMPLE", "")
import sys
import time
from datetime import datetime
import subprocess
from Bio.Blast import NCBIWWW
from Bio import SeqIO
from Bio.Blast import NCBIXML
from Bio import Entrez
from urllib.error import URLError
import re
import numpy
import pandas as pd
import matplotlib.pyplot as plt
Entrez.email = "26869993@sun.ac.za"

class Hit:
    def __init__(self, species, database_type, num_of_hits):
        self.species = species
        self.database_type = database_type #0 - NCBI, 1 - UNITE
        self.num_hits = num_of_hits
        self.arr_bit_scores = []
        self.max_bit_score = 0
        self.arr_coverage = []
        self.arr_identity = []
        self.arr_scores = []
        self.avg_scores = 0
    
    def get_species(self):
        return self.species
    def add_num_hits(self):
        self.num_hits += 1
    def get_num_hits(self):
        return self.num_hits
    def update_average_score(self):
        sum = 0.00
        for i in range(0, len(self.arr_scores)):
            sum += self.arr_scores[i]
        self.avg_scores = sum/self.num_hits
    def get_average_score(self):
        return self.avg_scores
    def add_score(self, temp_score):
        self.arr_scores.append(temp_score)
        self.update_average_score()
    def update_score(self, index, score):
        self.arr_scores[index] = score
        self.update_average_score()
    def add_bit_score(self, temp_bit_score):
        self.arr_bit_scores.append(temp_bit_score)
        max_bit_score = self.get_max_bit_score()
        if (temp_bit_score > max_bit_score):
            self.max_bit_score = temp_bit_score
    def get_max_bit_score(self):
        max = 0
        for i in range(0, len(self.arr_bit_scores)):
            if (self.arr_bit_scores[i] > max):
                max = self.arr_bit_scores[i]
        return max
    def get_bit_score(self, index):
        return self.arr_bit_scores[index]
    def add_coverage(self, temp_coverage):
        self.arr_coverage.append(temp_coverage)
    def add_identity(self, temp_identity):
        self.arr_identity.append(temp_identity)

def main():
    """
        Takes 3 arguments, 
        sys.argv[1] = Name of input consensus file in format INT26_{}_CONSENSUS.fas
        sys.argv[2] = Mode: 0 - Just complete BLAST results and BLAST summary
                            1 - BLAST complete results, BLAST summary and taxonomy counting
        sys.argv[3] = Database search mode
                    0 - Search both databases
                    1 - Search just NCBI
                    2 - Search just UNITE
        sys.argv[4] = E-value threshold
        sys.argv[5] = Identity % threshold
        sys.argv[6] = Coverage % threshold
        sys.argv[7] = String extension added to files that need to be saved in the final directory
        sys.argv[8] = String extension added to files that need to be saved in the blast directory
        sys.argv[9] = String extension added to files that need to be saved in the comparison directory
    """
    print("CL: BLAST search and taxonomy starting")
    start_time = time.perf_counter()
    ################### Arguments initialisation ##############################
    s_input_file = sys.argv[1]
    s_file_identifier = sys.argv[2]
    taxonomy_mode = int(sys.argv[3])
    database_mode = int(sys.argv[4])
    f_e_value_threshold = float(sys.argv[5])
    identity_threshold = float(sys.argv[6])
    coverage_threshold = float(sys.argv[7])
    ncbi_word_size = float(sys.argv[8])
    if (f_e_value_threshold == None):
        f_e_value_threshold = 0.001
    final_directory_extension = sys.argv[9]
    blast_directory_extension = sys.argv[10]
    comparison_directory_extension = sys.argv[11]
    ######################### Starting values #################################
    # i_name_start = 0
    # i_name_end = 0
    s_blast_complete_ncbi = ""
    s_blast_summary_ncbi = ""
    s_blast_complete_unite = ""
    s_blast_summary_unite = ""
    s_taxonomy_counter_ncbi = ""
    s_taxonomy_counter_unite = ""
    s_performance_report = ""
    s_comparison_report = ""
    ncbi_start_time = 0
    ncbi_end_time = 0
    unite_start_time = 0
    unite_end_time = 0
    comparison_start_time = 0
    comparison_end_time = 0
    #################### Establish how files will be named #####################
    # i_name_start = s_input_file.find("_") + 1
    # i_name_end = s_input_file.find("_", i_name_start)
    if (s_file_identifier != ""):
        s_blast_complete_ncbi = blast_directory_extension + "/INT26_" + s_file_identifier + "_BLAST_COMPLETE_NCBI.xml"
        s_blast_summary_ncbi = final_directory_extension + "/INT26_" + s_file_identifier + "_BLAST_SUMMARY_NCBI.txt"
        s_blast_complete_unite = blast_directory_extension + "/INT26_" + s_file_identifier + "_BLAST_COMPLETE_UNITE.xml"
        s_blast_summary_unite = final_directory_extension + "/INT26_" + s_file_identifier + "_BLAST_SUMMARY_UNITE.txt"
        s_secondary_database_ncbi = final_directory_extension + "/INT26_" + s_file_identifier + "_REFSEQ_HITS.txt"
        s_taxonomy_counter_ncbi = final_directory_extension + "/INT26_" + s_file_identifier + "_TAXONOMY_COUNTER_NCBI.xml"
        s_taxonomy_counter_unite = final_directory_extension + "/INT26_" + s_file_identifier + "_TAXONOMY_COUNTER_UNITE.xml"
        s_performance_report = final_directory_extension + "/INT26_" + s_file_identifier + "_PERFORMANCE_REPORT.txt"
        s_comparison_report = comparison_directory_extension + "/INT26_" + s_file_identifier + "_COMPARISON_REPORT.txt"
        s_comparison_graph = comparison_directory_extension + "/INT26_" + s_file_identifier + "_COMPARISON_GRAPH.png"
    else: 
        sys.stderr.write("Error: Invalid starting file argument. Does not follow structure of INT26_{}_CONSENSUS.fas\n")
        return 1
        #sys.exit()
    ################### Perform BLAST on different databases ##################
    arr_hits_ncbi = []
    arr_hits_unite = []
    total_ncbi_hits = 0
    total_unite_hits = 0
    if (database_mode != 2):
        ncbi_start_time = time.perf_counter()
        arr_hits_ncbi, total_ncbi_hits = ncbi(s_input_file, s_blast_summary_ncbi, s_blast_complete_ncbi, s_taxonomy_counter_ncbi, s_secondary_database_ncbi, f_e_value_threshold, identity_threshold, coverage_threshold, ncbi_word_size, taxonomy_mode)
        ncbi_end_time = time.perf_counter()
    if (database_mode != 1):
        unite_start_time = time.perf_counter()
        arr_hits_unite, total_unite_hits = unite(s_input_file, s_blast_summary_unite, s_blast_complete_unite, s_taxonomy_counter_unite, f_e_value_threshold, identity_threshold, coverage_threshold, taxonomy_mode)
        unite_end_time = time.perf_counter()
    #################### Make performance report ###############################
    end_time = time.perf_counter()
    with open(s_performance_report, "a") as performance_output:
        performance_output.write("------------------------------ BLASTn report --------------------------------\n")
        performance_output.write(f"Date and time of BLASTn search end:\t{datetime.now():%Y-%m-%d %H:%M}\n")
        performance_output.write(f"Elapsed time for total search: \t{end_time-start_time:.2f} seconds\n")
        performance_output.write(f"Elapsed time for NCBI search: \t{ncbi_end_time-ncbi_start_time:.2f} seconds\n")
        performance_output.write(f"Elapsed time for UNITE search: \t{unite_end_time-unite_start_time:.2f} seconds\n")
        performance_output.write("Input file received: " + s_input_file + "\n")
        performance_output.write("Taxonomy mode chosen: " + str(taxonomy_mode) + "\n")
        performance_output.write("Database mode chosen: " + str(database_mode) + "\n")
        performance_output.write(f"E-value threshold: E-value < {f_e_value_threshold:.20f} \n")
        performance_output.write(f"Identity threshold (%): Identities % > {identity_threshold:.4f} \n")
        performance_output.write(f"Coverage threshold (%): Coverage % > {coverage_threshold:.4f} \n")
        performance_output.write("------------------------------ BLASTn report -------------------------------\n")
        #performance_output.write("Computer where search was run: " + socket.gethostbyname())
    performance_output.close()
    print("CL: BLAST search and taxonomy ending.")
    ###################### Comparison between databases ########################
    print("CL: Begin comparison between databases.")
    report_step(sample, "interpretation", "running")
    comparison_start_time = time.perf_counter()
    print("CL: NCBI hits: " + str(len(arr_hits_ncbi)))
    print("CL: UNITE hits: " + str(len(arr_hits_unite)))
    comparison(s_comparison_report, s_comparison_graph, arr_hits_ncbi, arr_hits_unite, len(arr_hits_ncbi), len(arr_hits_unite))
    comparison_end_time = time.perf_counter()
    report_step(sample, "interpretation", "done")
    with open(s_performance_report, "a") as performance_output:
        performance_output.write("------------------------------ Comparison report -------------------------------\n")
        performance_output.write(f"Date and time of comparison end:\t{datetime.now():%Y-%m-%d %H:%M}\n")
        performance_output.write(f"Elapsed time for total comparison: \t{comparison_end_time-comparison_start_time:.2f} seconds\n")
        performance_output.write("Comparison data saved to: " + s_comparison_report + "\n")
        performance_output.write("Comparison graph saved to: " + s_comparison_graph + "\n")
        performance_output.write("------------------------------ Comparison report -------------------------------\n")
    performance_output.close()
    print("CL: End comparison between databases.")
    if ((len(arr_hits_ncbi) == 0) and (len(arr_hits_unite) == 0)):
        return 2
    else:
        return 0

def ncbi(s_input_file, s_blast_summary_ncbi, s_blast_complete_ncbi, s_taxonomy_counter_ncbi, s_secondary_database_ncbi, f_e_value_threshold, identity_threshold, coverage_threshold, ncbi_word_size, taxonomy_mode):
    """
        This method handles all computation related to BLASTn searching on the NCBI database. First does a 
        blastn search and then builds up a summary report that can report the taxonomy found in the search.
    """
    print("CL: Start with BLASTn summary for NCBI.")
    table_tax_count = {}
    counter = 0
    arr_hits_ncbi = []
    obj_hit = None
    blastn_ncbi(s_input_file, s_blast_complete_ncbi, f_e_value_threshold, ncbi_word_size)
    ############ Make summary of BLASTn report using NCBI DATABASE #########
    report_step(sample, "summary", "running")
    with open(s_blast_summary_ncbi, "w") as summary_out:
        with open(s_blast_complete_ncbi) as result_handle:
            blast_records = NCBIXML.parse(result_handle)
            for record in blast_records:
                for alignment in record.alignments:
                    for hsp in alignment.hsps:
                        if ((hsp.expect < f_e_value_threshold) and (((hsp.identities/hsp.align_length)*100) > identity_threshold) and (((hsp.align_length/record.query_length) * 100)> coverage_threshold)):
                            species = extract_species_ncbi(alignment.title)
                            if (species != None):
                                summary_out.write(f"Accession: {alignment.accession}\t\t")
                                summary_out.write(f"Species: {species}\t\t\t\t")
                                summary_out.write(f"E-value: {hsp.expect:.10f}\t\t")
                                summary_out.write(f"%Identity: {((hsp.identities/hsp.align_length)*100):.4f}\t\t")
                                summary_out.write(f"%Coverage: {((hsp.align_length/record.query_length) * 100):.4f}\n")
                            else: 
                                print("taxonomy == NONE")

                            if "_" in alignment.accession:
                                print("CL: NCBI hit from secondary database found.")
                                with open(s_secondary_database_ncbi, "a") as secondary_database_output:
                                    secondary_database_output.write(f"Accession: {alignment.accession}\t\t")
                                    secondary_database_output.write(f"Species: {species}\t\t\t\t")
                                    secondary_database_output.write(f"E-value: {hsp.expect:.10f}\t\t")
                                    secondary_database_output.write(f"%Identity: {((hsp.identities/hsp.align_length)*100):.4f}\t\t")
                                    secondary_database_output.write(f"%Coverage: {((hsp.align_length/record.query_length) * 100):.4f}\n")
                                secondary_database_output.close()

                            obj_hit = find_hit_obj_in_arr(arr_hits_ncbi, species)
                            if (obj_hit == None):
                                obj_hit = add_new_obj(species, 0, hsp.bits, (hsp.align_length/record.query_length) * 100, (hsp.identities/hsp.align_length)*100)
                                arr_hits_ncbi.append(obj_hit)
                            else:
                                #TODO, don't think this will update the array, only the obj
                                add_additional_entry(obj_hit, hsp.bits, (hsp.align_length/record.query_length) * 100, (hsp.identities/hsp.align_length)*100)
                            if (taxonomy_mode == 1):
                                counter += 1
                                table_tax_count = get_taxonomy_count_ncbi_without_entrez(table_tax_count, species)
                                # table_tax_count = get_taxonomy_count_ncbi(table_tax_count, taxonomy)
    summary_out.close()
    for t in range(0, len(arr_hits_ncbi)):
        for a in range(0, arr_hits_ncbi[t].get_num_hits()):
            score = calculate_score(arr_hits_ncbi[t].get_bit_score(a), arr_hits_ncbi[t].get_max_bit_score())
            arr_hits_ncbi[t].update_score(a, score)
    report_step(sample, "summary", "done")
    print("CL: Done with BLASTn summary for NCBI.")
    ####################### Sort species with counts #################################
    sorted_table_tax_count = dict(sorted(table_tax_count.items(), key = lambda x: x[1], reverse=True))
    ################### Print NCBI taxonomy counter report ##########################
    if (taxonomy_mode == 1):
        with open(s_taxonomy_counter_ncbi, "w") as taxonomy_counter_output:
            taxonomy_counter_output.write("Species name\t\t\t\t\tCount of species hit\t\t'%'of " + str(counter) +" hits for species\n")
            for key, value in sorted_table_tax_count.items():
                taxonomy_counter_output.write(key + "\t\t\t\t" + str(value) + "\t\t\t\t\t" + str(value/counter*100) + "\n")
        print("CL: Done with NCBI taxonomy counter.")
    return arr_hits_ncbi, counter
        
def unite(s_input_file, s_blast_summary_unite, s_blast_complete_unite, s_taxonomy_counter_unite, f_e_value_threshold, identity_threshold, coverage_threshold, taxonomy_mode):
    """
        This method handles all computation related to BLASTn searching on the locally downloaded UNITE database. 
        First does a blastn search on the local database and then builds up a summary report that can report the 
        taxonomy found in the search.
    """
    print("CL: Start with BLASTn summary for UNITE.")
    blastn_unite(s_input_file, s_blast_complete_unite)
    table_tax_count = {}
    counter = 0
    arr_hits_unite = []
    ############ Make summary of BLASTn report using UNITE DATABASE #########
    with open(s_blast_summary_unite, "w") as summary_out:
        with open(s_blast_complete_unite) as result_handle:
            blast_records = NCBIXML.parse(result_handle)
            for record in blast_records:
                for alignment in record.alignments:
                    for hsp in alignment.hsps:
                        if ((hsp.expect < f_e_value_threshold) and (((hsp.identities/hsp.align_length)*100) > identity_threshold) and (((hsp.align_length/record.query_length) * 100)> coverage_threshold)):
                        #if (hsp.expect < f_e_value_threshold): # and ((hsp.identities/hsp.align_length)*100 > 90) and ((hsp.align_length/record.query_length) *100 > 85)):
                            # e_value and %identity and %coverage
                            species = get_taxonomy_unite(alignment.title)
                            species = species.replace("_", " ")
                            if (species != None):
                                summary_out.write(f"Accession: {alignment.accession}\t\t")
                                summary_out.write(f"Species: {species}\t\t")
                                summary_out.write(f"E-value: {hsp.expect:.10f}\t\t")
                                summary_out.write(f"%Identity: {((hsp.identities/hsp.align_length)*100):.4f}\t\t")
                                summary_out.write(f"%Coverage: {((hsp.align_length/record.query_length) * 100):.4f}\n")
                            # print("bit score: " + str(hsp.bits))
                            # print("identity: " + str((hsp.align_length/record.query_length) * 100))
                            # print("coverage: " + str((hsp.identities/hsp.align_length) * 100))
                            obj_hit = find_hit_obj_in_arr(arr_hits_unite, species)
                            if (obj_hit == None):
                                obj_hit = add_new_obj(species, 1, hsp.bits, (hsp.align_length/record.query_length) * 100, (hsp.identities/hsp.align_length)*100)
                                arr_hits_unite.append(obj_hit)
                            else:
                                #TODO, don't think this will update the array, only the obj
                                add_additional_entry(obj_hit, hsp.bits, (hsp.align_length/record.query_length) * 100, (hsp.identities/hsp.align_length) * 100)
                            if (taxonomy_mode == 1):
                                counter += 1
                                table_tax_count = get_taxonomy_count_unite(table_tax_count, species)
    summary_out.close()
    for t in range(0, len(arr_hits_unite)):
        for a in range(0, arr_hits_unite[t].get_num_hits()):
            score = calculate_score(arr_hits_unite[t].get_bit_score(a), arr_hits_unite[t].get_max_bit_score())
            arr_hits_unite[t].update_score(a, score)
    print("CL: Done with BLASTn summary for UNITE.")
    ####################### Sort species with counts #################################
    sorted_table_tax_count = dict(sorted(table_tax_count.items(), key = lambda x: x[1], reverse=True))
    ################### Print UNITE taxonomy counter report ##########################
    if (taxonomy_mode == 1):
        with open(s_taxonomy_counter_unite, "w") as taxonomy_counter_output:
            taxonomy_counter_output.write("Species name\t\t\t\t\tCount of species hit\t\t'%'of " + str(counter) + " hits for species\n")
            for key, value in sorted_table_tax_count.items():
                taxonomy_counter_output.write(key + "\t\t\t\t" + str(value) + "\t\t\t\t\t" + str(value/counter*100) + "\n")
        print("CL: Done with UNITE taxonomy counter.")
    #print(len(arr_hits_unite))
    # for a in range(0, len(arr_hits_unite)):
    #     for y in range(0, arr_hits_unite[a].get_num_hits()):
    #         print(arr_hits_unite[a].get_species())
    #         print(arr_hits_unite[a].get_bit_score(y))
    return arr_hits_unite, counter

def blastn_ncbi(s_input_file, s_blast_complete, f_e_value_threshold, ncbi_word_size):
    """
        Does the BLASTn search online using the NCBI database.
    """
    report_step(sample, "blast", "running")

    record = SeqIO.read(s_input_file, format="fasta")
    try:
        result_handle = NCBIWWW.qblast(
            program="blastn", 
            database="nt", 
            sequence=record.seq,
            word_size=int(ncbi_word_size),
            megablast=False,
            entrez_query='"Fungi"[Organism] NOT uncultured[Title]',
        )
        #result_handle = NCBIWWW.qblast(program="blastn", database="rRNA_typestrains/ITS_RefSeq_Fungi", sequence=record.seq)
    except URLError as e:
        sys.stderr.write("Error: Connection error occured\n")
        sys.exit()
    except Exception as e:
        sys.stderr.write(f"Error: {e}")
        sys.exit()
    ############## Write complete BLASTn report to output file ##################
    with open(s_blast_complete, "w") as out_handle:
        out_handle.write(result_handle.read())
    result_handle.close()

    report_step(sample, "blast", "done")
    print("CL: Writing of complete NCBI BLASTn report done.")
    
def blastn_unite(s_input_file, s_blast_complete):
    """
        Does a BLASTn search locally using the UNITE database.
    """
    UNITE_database = "./database/unite/unite_its_database"
    command = ["blastn", "-query", s_input_file, "-db", UNITE_database, "-out", s_blast_complete, "-outfmt", "5"]
    #"-evalue", str(f_e_value_threshold), "-max_target_seqs", "10"]
    
    blast_result = subprocess.run(command, capture_output=True, text=True)
    print("CL: Writing of complete UNITE BLASTn report done.")

def extract_species_ncbi(title):
    """
        This method receives the title from a NCBI BLASTn hit and then extracts the species name
        found in the title. It returns the species as a string.
    """
    species = re.search(r'([A-Z][a-z]+ [a-z]+)', title)
    if species:
        return species.group(1)
    return None

def get_taxonomy_count_ncbi_without_entrez(table_tax_count, species):
    """
        This method is used to build up a dictionary of species that have been found in the BLASTn search
        and how many times it has been found. If the species already exists in the dictionary, the count 
        for that species is just increased. The new dictionary is then returned. This is done using data 
        from the complete .xml file after the BLAST search instead of starting a new Entrez search. 
    """
    if (species) in table_tax_count:
        cur_value = table_tax_count.get(species)
        cur_value += 1
        table_tax_count[species] = cur_value
    else:
        table_tax_count.update({species: 1})
    return table_tax_count

def get_taxonomy_ncbi(accession):
    """
        Does an Entrez search to find the taxonomy of the received accession number.
        Returns array tax_records that contains the taxonomy of specificied accession number.
    """
    tax_handle = Entrez.efetch(db="nucleotide", id=accession, retmode="xml")        
    records = Entrez.read(tax_handle)
    tax_handle.close()
    #extracting ID
    #tax_id = records[0]["GBSeq_feature-table"][0]["GBFeature_quals"][0]["GBQualifier_value"]
    features = records[0]["GBSeq_feature-table"]
    
    tax_id = None
    for feature in features:
        if "GBFeature_quals" in feature:
            for qual in feature["GBFeature_quals"]:
                if qual["GBQualifier_name"] == "db_xref" and "taxon:" in qual["GBQualifier_value"]:
                    tax_id = qual["GBQualifier_value"].split(":")[1]
    if tax_id is None:
        raise ValueError("Tax_id not found")

    #fetch taxonomy
    tax_handle = Entrez.efetch(db="taxonomy", id=tax_id, retmode="xml")
    tax_records = Entrez.read(tax_handle)
    tax_handle.close()
    return tax_records[0]

def parse_taxonomy_ncbi(tax_records):
    """
        Organise data from tax_records to be more readible.
        Returns taxonomy array that you can search using keywords like 'species'
    """
    linaeage = tax_records["LineageEx"]

    taxonomy = {
        "species": tax_records.get("ScientificName", "NA"),
        "genus": "NA",
        "family": "NA",
        "order": "NA",
        "class": "NA",
        "phylum": "NA",
        "kingdom": "NA"
    }

    for rank in linaeage:
        if rank["Rank"] in taxonomy:
            taxonomy[rank["Rank"]] = rank["ScientificName"]

    return taxonomy

def get_taxonomy_count_ncbi(table_tax_count, taxonomy):
    """
        Gets counter of how much each species match occurs.
        Returns arr_tax_count where you can search for species name and get count.
    """
    cur_value = 0

    if (taxonomy['species']) in table_tax_count:
        cur_value = table_tax_count.get(taxonomy['species'])
        cur_value += 1
        table_tax_count[taxonomy['species']] = cur_value
    else:
        table_tax_count.update({taxonomy['species']: 1})

    return table_tax_count

def get_taxonomy_unite(title):
    """
        Takes the title of the fasta file entry and finds the species name in the string. Returns only the species name.
    """
    title_parts = title.split("|")
    id = None
    taxonomy = None

    for p in title_parts:
        if (p.startswith("UDB")):
            id = p
        if ("s__") in p:
            count = p.find("s__")
            taxonomy = p[count+3:]
    
    return taxonomy

def get_taxonomy_count_unite(table_tax_count, taxonomy):
    """
        Gets counter of how much each species match occurs.
        Returns arr_tax_count where you can search for species name and get count.
    """
    cur_value = 0

    if (taxonomy) in table_tax_count:
        cur_value = table_tax_count.get(taxonomy)
        cur_value += 1
        table_tax_count[taxonomy] = cur_value
    else:
        table_tax_count.update({taxonomy: 1})

    return table_tax_count

def calculate_score(bit_score, max_bit_score):
    """
        Calculates a score based on the bit score and maximum bit score. Returns the score. 
    """
    score = 0
    score = bit_score/max_bit_score
    return score

def add_new_obj(species, database_type, bit_score, coverage, identity):
    """
        Makes a new object when a new species hit is found in the complete BLAST search report.
        This contains all the values associated to this new species hit. The object is then returned.
    """
    obj_hit = Hit(species, database_type, 1)
    obj_hit.add_bit_score(bit_score)
    obj_hit.add_coverage(coverage)
    obj_hit.add_identity(identity)
    obj_hit.add_score(0)
    return obj_hit

def add_additional_entry(obj_hit, bit_score, coverage, identity):
    """"
        An object for this species already exists but now a different hit for this 
        species has been found. The data for this hit should also be added to the arrays.
    """
    obj_hit.add_num_hits()
    obj_hit.add_bit_score(bit_score)
    obj_hit.add_coverage(coverage)
    obj_hit.add_identity(identity)
    obj_hit.add_score(0)
    return obj_hit

def find_hit_obj_in_arr(arr_hits, species):
    """
        Check if an object for a certain species is already in the array. If it is, 
        then return the object. If not, then return None.
    """
    obj_hit = Hit("",0,0)
    for b in range(0, len(arr_hits)):
        obj_hit = arr_hits[b]
        if (obj_hit.get_species() == species):
            return obj_hit
    return None

def comparison(s_comparison_report, s_comparison_graph, arr_hits_ncbi, arr_hits_unite, total_ncbi_hits, total_unite_hits):
    """
        This method is used to compare the hit results between the different databases. It compares the scores
        for each species from each database. The average scores for each species found in either database is written 
        to a .txt file if the average score is more than or equal to 0.5 (50%).
    """
    total_score_dict = {}
    with open(s_comparison_report, "w") as comparison_output:
        comparison_output.write("Species\tNCBI score\tUNITE score\tTotal score\n")
        if ((len(arr_hits_ncbi) > 0) and (len(arr_hits_unite) > 0)):
            for b in range(len(arr_hits_ncbi)):
                for t in range(len(arr_hits_unite)):
                    arr_score = []
                    if (arr_hits_unite[t].get_species() == arr_hits_ncbi[b].get_species()):
                        ncbi_score = arr_hits_ncbi[b].get_average_score()
                        unite_score = arr_hits_unite[t].get_average_score()
                        total_score = (ncbi_score + unite_score)/2
                        comparison_output.write(f"{arr_hits_ncbi[b].get_species()}\t{ncbi_score:.4f}\t{unite_score:.4f}\t{total_score:.4f}\n")
                        arr_score = [ncbi_score, unite_score, total_score, (arr_hits_ncbi[b].get_num_hits()/total_ncbi_hits)*100, (arr_hits_unite[t].get_num_hits()/total_unite_hits)*100, ((arr_hits_ncbi[b].get_num_hits() + arr_hits_unite[t].get_num_hits())/(total_ncbi_hits+total_unite_hits))*100]
                        if (arr_hits_ncbi[b].get_species()) not in total_score_dict:
                            total_score_dict.update({arr_hits_ncbi[b].get_species(): arr_score})
                    else:
                        if (arr_hits_ncbi[b].get_species()) not in total_score_dict:
                            ncbi_score = arr_hits_ncbi[b].get_average_score()
                            unite_score = 0
                            total_score = ncbi_score/2
                            if (total_score > 0.5):
                                comparison_output.write(f"{arr_hits_ncbi[b].get_species()}\t{ncbi_score:.4f}\t{unite_score:.4f}\t{total_score:.4f}\n")
                                arr_score = [ncbi_score, unite_score, total_score, (arr_hits_ncbi[b].get_num_hits()/total_ncbi_hits)*100, (0/total_unite_hits)*100, ((arr_hits_ncbi[b].get_num_hits() + 0)/(total_ncbi_hits+total_unite_hits))*100]
                                total_score_dict.update({arr_hits_ncbi[b].get_species(): arr_score})
                        if (arr_hits_unite[t].get_species()) not in total_score_dict:
                            ncbi_score = 0
                            unite_score = arr_hits_unite[t].get_average_score()
                            total_score = unite_score/2
                            if (total_score > 0.5):
                                comparison_output.write(f"{arr_hits_ncbi[b].get_species()}\t{ncbi_score:.4f}\t{unite_score:.4f}\t{total_score:.4f}\n")
                                arr_score = [ncbi_score, unite_score, total_score, (0/total_ncbi_hits)*100, (arr_hits_unite[t].get_num_hits()/total_unite_hits)*100, ((0 + arr_hits_unite[t].get_num_hits())/(total_ncbi_hits+total_unite_hits))*100]
                                total_score_dict.update({arr_hits_ncbi[b].get_species(): arr_score})
        else:
            if (len(arr_hits_ncbi) > 0):
                for b in range(len(arr_hits_ncbi)):
                    if (arr_hits_ncbi[b].get_species()) not in total_score_dict:
                        ncbi_score = arr_hits_ncbi[b].get_average_score()
                        unite_score = 0
                        total_score = ncbi_score/2
                        if (total_score > 0.5):
                            comparison_output.write(f"{arr_hits_ncbi[b].get_species()}\t{ncbi_score:.4f}\t{unite_score:.4f}\t{total_score:.4f}\n")
                            arr_score = [ncbi_score, unite_score, total_score, (arr_hits_ncbi[b].get_num_hits()/total_ncbi_hits)*100, (0/total_unite_hits)*100, ((arr_hits_ncbi[b].get_num_hits() + 0)/(total_ncbi_hits+total_unite_hits))*100]
                            total_score_dict.update({arr_hits_ncbi[b].get_species(): arr_score})
            if (len(arr_hits_unite) > 0):
                for t in range(len(arr_hits_unite)):
                    if (arr_hits_unite[t].get_species()) not in total_score_dict:
                        ncbi_score = 0
                        unite_score = arr_hits_unite[t].get_average_score()
                        total_score = unite_score/2
                        if (total_score > 0.5):
                            comparison_output.write(f"{arr_hits_ncbi[b].get_species()}\t{ncbi_score:.4f}\t{unite_score:.4f}\t{total_score:.4f}\n")
                            arr_score = [ncbi_score, unite_score, total_score, (0/total_ncbi_hits)*100, (arr_hits_unite[t].get_num_hits()/total_unite_hits)*100, ((0 + arr_hits_unite[t].get_num_hits())/(total_ncbi_hits+total_unite_hits))*100]
                            total_score_dict.update({arr_hits_ncbi[b].get_species(): arr_score})
    comparison_output.close()
    comparison_plotting(total_score_dict, s_comparison_graph)

def comparison_plotting(total_score_dict, s_comparison_graph):
    """
        This method plots a graph displaying all the database scores for each species. This is 
        then saved to easily identify which species provides the most promising hit.
    """
    print("CL: Start with plotting species score")
    species = list(total_score_dict.keys())
    scores = numpy.array(list(total_score_dict.values()))
    ncbi_score = [scores[0] for scores in total_score_dict.values()] #scores[:, 0]
    unite_score = [scores[1] for scores in total_score_dict.values()]#scores[:, 1]
    total_score = [scores[2] for scores in total_score_dict.values()]#scores[:, 2]

    ncbi_pct  = [scores[3] for scores in total_score_dict.values()]
    unite_pct = [scores[4] for scores in total_score_dict.values()]
    total_pct = [scores[5] for scores in total_score_dict.values()]
    
    location = numpy.arange(len(species))
    width = 0.25

    # Plot bar graph
    figure, axes1 = plt.subplots(figsize=(10,6))
    bar1 = axes1.bar(location - width, ncbi_score, width, alpha=0.7, label="NCBI bit score")
    bar2 = axes1.bar(location, unite_score, width, alpha=0.7, label="UNITE bit score")
    bar3 = axes1.bar(location + width, total_score, width, alpha=0.7, label="Average bit score")
    
    # Labeling for Bar graph
    labels1 = [f"{score:.2f}" for score in ncbi_score]
    axes1.bar_label(bar1, labels=labels1, padding=3, fontsize=8)

    labels2 = [f"{score:.2f}" for score in unite_score]
    axes1.bar_label(bar2, labels=labels2, padding=3, fontsize=8)

    labels3 = [f"{score:.2f}" for score in total_score]
    axes1.bar_label(bar3, labels=labels3, padding=3, fontsize=8)


    axes1.set_xlabel("Species")
    axes1.set_ylabel("Score")
    axes1.set_ylim(0.5,1)
    axes1.set_xticks(location)
    axes1.set_xticklabels(species, rotation=30, ha="right")
    axes1.legend()

    # Plot line graph
    axes2 = axes1.twinx()

    line1 = axes2.plot(location - width, ncbi_pct, color="black", linestyle="-", marker='o', linewidth=2, label="% NCBI hit coverage")
    line2 = axes2.plot(location, unite_pct, color="black", linestyle="--", marker='s', linewidth=2, label="% Unite hit coverage")
    line3 = axes2.plot(location + width, total_pct, color="black", linestyle=":", marker='^', linewidth=2, label="% Average hit coverage")

    axes2.set_ylabel("Percentage (%)")
    axes2.set_ylim(0, 100)

    # Labeling for line graph
    for x,y in zip(location - width, ncbi_pct):
        axes2.text(x, y+2, f"{y:.1f}", ha="center", fontsize=8)
    for x,y in zip(location, unite_pct):
        axes2.text(x, y+2, f"{y:.1f}", ha="center", fontsize=8)
    for x,y in zip(location + width, total_pct):
        axes2.text(x, y+2, f"{y:.1f}", ha="center", fontsize=8)

    # labels1 = [f"{score:.2f}\n({pct:.2f}%)"
    #         for score, pct in zip(ncbi_score, ncbi_pct)]
    # axes1.bar_label(bar1, labels=labels1, padding=3, fontsize=8)

    # labels2 = [f"{score:.2f}\n({pct:.2f}%)"
    #         for score, pct in zip(unite_score, unite_pct)]
    # axes1.bar_label(bar2, labels=labels2, padding=3, fontsize=8)

    # labels3 = [f"{score:.2f}\n({pct:.2f}%)"
    #         for score, pct in zip(total_score, total_pct)]
    # axes1.bar_label(bar3, labels=labels3, padding=3, fontsize=8)

    # Combined
    handles1, labelsax1 = axes1.get_legend_handles_labels()
    handles2, labelsax2 = axes2.get_legend_handles_labels()

    axes1.legend(handles1 + handles2, labelsax1 + labelsax2, loc="upper left")
    axes1.set_title("Species score comparison with coverage %", pad=20)
    plt.tight_layout()
    plt.savefig(s_comparison_graph, dpi=300)
    print("CL: End with plotting species score")
    
if __name__ == "__main__" : sys.exit(main())