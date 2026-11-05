# Used to build the UNITE database locally using the input files
echo "Start database building script"
makeblastdb -in ./database/unite/UNITE_DB_WITH_TAX_19.02.2025.fasta -dbtype nucl -out ./database/unite/unite_its_database
echo "End database building script"