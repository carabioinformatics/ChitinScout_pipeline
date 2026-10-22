#s_consensus_file = $1
#s_blast_complete = $2
echo "Start database building script"
makeblastdb -in ./database/unite/UNITE_DB_WITH_TAX_19.02.2025.fasta -dbtype nucl -out ./database/unite/unite_its_database
echo "End database building script"
#echo "Start blastn search"
#blastn -query $1 -db ./database/unite/unite_its_database -out $2 -outfmt 5
#blastn -query ./Output/CLS5/BLAST/INT26_CLS5_CONSENSUS.fas -db ./database/unite/unite_its_database -out results.xml -outfmt 5
#echo "End blastn search"