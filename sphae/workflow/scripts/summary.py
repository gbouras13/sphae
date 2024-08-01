#!/usr/bin/env python 

from pathlib import Path
import shutil
import pandas as pd
from Bio import SeqIO
import os
import glob

#copying files if there is only one genome
def copy_files(input_files, params):
    shutil.copy(input_files['genome'], params['genomes'])
    shutil.copy(input_files['gbk'], params['gbks'])
    shutil.copy(input_files['plot'], params['plots'])

# Using a function to check file existence and count lines
def count_lines(filepath):
    file = Path(filepath) 
    return sum(1 for _ in open(filepath)) if file.is_file() else None

#copying multiple files if there are multiple genomes per sample
def copy_multiple_files(params):
    # Ensure the destination directory exists
    os.makedirs(outdir, exist_ok=True)
    
    # Use glob to find all .fasta files in the specified pattern
    source_files = glob.glob(f"{params['annot']}/{params['sample']}-*-genomes/*.fasta")
    # Copy each .fasta file to the destination directory
    for file in source_files:
        print(f"Copying {file} to {outdir}")
        shutil.copy(file, outdir)
    
    # Find and copy .gbk files with renaming
    gbk_files = glob.glob(f"{params['annot']}/phynteny-*/{params['sample']}_*_phynteny/*.gbk")
    for i, gbk in enumerate(gbk_files, start=1):
        samplenames = f"{params['sample']}_{i}"
        new_gbk_path = os.path.join(outdir, f"{samplenames}.gbk")
        print(f"Copying {gbk} to {new_gbk_path}")
        shutil.copy(gbk, new_gbk_path)

    # Find and copy _plot.png files with renaming
    plot_files = glob.glob(f"{params['annot']}/phynteny-*/{params['sample']}_*_phynteny/*_plot.png")
    for i, plt in enumerate(plot_files, start=1):
        samplenames = f"{params['sample']}_{i}"
        new_png_path = os.path.join(outdir, f"{samplenames}.png")
        print(f"Copying {plt} to {new_png_path}")
        shutil.copy(plt, new_png_path)

def count_hypothetical_proteins(gbk_file):
    count = 0
    for record in SeqIO.parse(gbk_file, "genbank"):
        for feature in record.features:
            if feature.type == "CDS":
                if "product" in feature.qualifiers:
                    if "hypothetical protein" in feature.qualifiers["product"]:
                        count += 1
    return count

def write_single_genome_summary(input_files, summary):
    with open(input_files['table'], 'r') as table_file:
        lines = table_file.readlines()
        if len(lines) > 1:  # Ensure there is at least one data line
            fields = lines[1].strip().split(',')  # Split the second line into fields

            filename = input_files['read']
            with open(filename, 'r') as file:
                contents = file.read()
            summary.write(f"Total length of reads after QC and subsampling: {contents}\n")
        
        # Ensure fields list has enough elements to access the desired indices
            if len(fields) >= 23:
                summary.write(f"Length: {lines[1].split(',')[2]}\n")

                if fields[3].strip() == 'True':
                    summary.write("Circular: True\n")
                else:
                    summary.write("Circular: False\n")

                summary.write(f"Graph connections: {lines[1].split(',')[4]}\n")
                
                if 'DTR' in fields[-4]:
                    summary.write("DTR found\n")
                
                summary.write(f"Completeness: {lines[1].split(',')[20]}\n")
                summary.write(f"Contamination: {lines[1].split(',')[22]}\n")
                
        with open(input_files['taxa'], 'r') as taxa_file:
            tax = pd.read_csv(taxa_file, sep='\t')
            summary.write("Taxa Description (Matching hashes):\t")
            for index, row in tax.iterrows():
                summary.write(f"{row['Description']}\t{row['mash_matching_hashes']}\n")
                summary.write(f"Lowest Taxa classification: {row['Lowest_Taxa']}\n")
                summary.write(f"Isolation host of described taxa: {row['Isolation_Host_(beware_inconsistent_and_nonsense_values)']}\n")

        with open(input_files['cds'], 'r') as cds:
            cds_df=pd.read_csv(cds, sep='\t')
            cds_data = cds_df[cds_df['Description'] == 'CDS']
            count_value = cds_data['Count'].values[0]
            summary.write(f"Number of CDS: {count_value}\n")
        
        hypothetical_protein_count = count_hypothetical_proteins(input_files['gbk'])
        summary.write(f"Total number of CDS annotated as 'hypothetical protein': {hypothetical_protein_count}\n")
        
        with open(input_files['cdden'], 'r') as cdden:
            cdn=pd.read_csv(cdden, sep='\t')
            gc_percent = cdn['gc_perc'].values[0]
            coding_density = cdn['cds_coding_density'].values[0]
            summary.write(f"GC percent: {gc_percent}\n")
            summary.write(f"Coding density: {coding_density}\n")

        found_gene = False
        gbk_records = SeqIO.parse(input_files['gbk'], 'genbank')
        for record in gbk_records:
            for feature in record.features:
                if feature.type == "CDS" and 'product' in feature.qualifiers and 'integra' in feature.qualifiers['product'][0].lower():
                    #print (feature)
                    found_gene = True
                    gene_id = feature.qualifiers['locus_tag'][0]
                    function = feature.qualifiers['function'][0]
                    product = feature.qualifiers['product'][0]
                    summary.write(f"Integrase found: \t{gene_id}: function=\"{function}\", product=\"{product}\"\n")

                elif feature.type == "CDS" and 'product' in feature.qualifiers and 'recombinase' in feature.qualifiers['product'][0].lower():
                    #print (feature)
                    found_gene = True
                    gene_id = feature.qualifiers['locus_tag'][0]
                    function = feature.qualifiers['function'][0]
                    product = feature.qualifiers['product'][0]
                    summary.write(f"Recombinase found: \t{gene_id}: function=\"{function}\", product=\"{product}\"\n")
                
                elif feature.type == "CDS" and 'product' in feature.qualifiers and 'transposase' in feature.qualifiers['product'][0].lower():
                    #print (feature)
                    found_gene = True
                    gene_id = feature.qualifiers['locus_tag'][0]
                    function = feature.qualifiers['function'][0]
                    product = feature.qualifiers['product'][0]
                    summary.write(f"Transposase found: \t{gene_id}: function=\"{function}\", product=\"{product}\"\n")

        if not found_gene:
            if 'integra' not in open(input_files['gbk']).read().lower():
                summary.write("No Integrases\n")
            else:
                summary.write("No Integrases\n")
                summary.write("\t...but Phynteny predicted a few unknown function genes to have some similarity with integrase genes but with low confidence. Maybe a false positive or a novel integrase gene\n")

            if 'recombinase' not in open(input_files['gbk']).read().lower():
                summary.write("No recombinase\n")
            else: 
                summary.write("Recombinases found in genome\n")
            
            if 'transposase' not in open(input_files['gbk']).read().lower():
                summary.write("No transposase\n")
            else: 
                summary.write("Transposases found in genome\n")
            
        #AMR genes 
        if (len(open(input_files['amr']).readlines()) == 1) and (len(open(input_files['card']).readlines()) == 0):
            summary.write("No AMR genes found\n")
        elif (len(open(input_files['amr']).readlines()) != 1):
            summary.write("AMR genes found\n")
            shutil.copy(input_files['amr'], outdir) 
        elif (len(open(input_files['card']).readlines()) != 0):
            summary.write("AMR genes found\n")
            shutil.copy(input_files['card'], outdir) 

        #Virulence genes 
        if (len(open(input_files['vfdb']).readlines()) == 1) and (len(open(input_files['vfdb_phold']).readlines()) == 0):
            summary.write("No virulence factor genes\n")
        elif (len(open(input_files['vfdb']).readlines()) != 1):
            summary.write("Virulence genes found\n")
            shutil.copy(input_files['vfdb'], outdir)
        elif (len(open(input_files['vfdb_phold']).readlines()) != 0):  
            summary.write("Virulence genes found\n")
            shutil.copy(input_files['vfdb_phold'], outdir) 

        #CRISPR spacers 
        if (len(open(input_files['spacers']).readlines()) == 0) and (len(open(input_files['acr']).readlines()) == 0):
            summary.write("No anti CRISPR spacers found\n")
        elif (len(open(input_files['spacers']).readlines()) != 0):
            summary.write("anti-CRISPR spacers found\n")
            shutil.copy(input_files['spacers'], outdir)
        elif (len(open(input_files['acr']).readlines()) != 0):
            summary.write("anti-CRISPR spacers found\n")
            shutil.copy(input_files['acr'], outdir)
                
        #Defense finder genes  
        if (len(open(input_files['defense']).readlines()) == 0):
            summary.write("No Defense genes found\n")
        else:
            summary.write("Defense genes found\n") 
            shutil.copy(input_files['defense'], outdir) 

def write_multiple_genome_summary(input_files, summary):
    summary.write("Multiple phages assembled from this sample\n")
    summary.write("Their characteristics are:\n")
    filename = input_files['read']
    with open(filename, 'r') as file:
        contents = file.read()
    summary.write(f"Total length of reads after QC and subsampling: {contents}\n")
    summary.write("\n\n")

    with open(input_files['table'], 'r') as table_file:
        lines = table_file.readlines()
        if len(lines) > 2:
            for i, line in enumerate(lines[1:], start=1):  # Skip header and enumerate starting from 1
                fields = line.split(',')
                samplenames = f"{params['sample']}_{i}"
                summary.write(f"Sample name: {samplenames}\n")
                summary.write(f"Length: {fields[2]}\n")
                if fields[3].strip() == 'True':
                    summary.write("Circular: True\t")
                else:
                    summary.write("Circular: False\n")
                
                summary.write(f"Graph connections: {fields[4]}\n")
                
                if len(fields) >= 23 and 'DTR' in fields[-4]:
                    summary.write("DTR found\n")
                
                summary.write(f"Completeness: {fields[20]}\n")
                summary.write(f"Contamination: {fields[22]}\n")
                
                taxa_pattern = f"{annot}/pharokka-pr/{samplenames}_pharokka/{samplenames}_top_hits_mash_inphared.tsv"
                for taxa_file in glob.glob(taxa_pattern):
                    tax = pd.read_csv(taxa_file, sep='\t')
                    summary.write("Taxa description (Matching hashes):\t")
                    for index, row in tax.iterrows():
                        summary.write(f"{row['Description']}\t{row['mash_matching_hashes']}\n")
                        summary.write(f"Lowest Taxa classification: {row['Lowest_Taxa']}\n")
                        summary.write(f"Isolation host of described taxa: {row['Isolation_Host_(beware_inconsistent_and_nonsense_values)']}\n")

                cds_pattern = f"{annot}/pharokka-pr/{samplenames}_pharokka/{samplenames}_cds_functions.tsv"
                for cds_file in glob.glob(cds_pattern):
                    cds_df=pd.read_csv(cds_file, sep='\t')
                    cds_data = cds_df[cds_df['Description'] == 'CDS']
                    count_value = cds_data['Count'].values[0]
                    summary.write(f"Number of CDS: {count_value}\n")
                
                gbk_pattern = f"{annot}/phynteny-pr/{samplenames}_phynteny/phynteny.gbk"
                for gbk_file in glob.glob(gbk_pattern):
                    hypothetical_protein_count = count_hypothetical_proteins(gbk_file)
                    summary.write(f"Total number of CDS annotated as 'hypothetical protein': {hypothetical_protein_count}\n")

                cds_dens_pattern = f"{annot}/pharokka-pr/{samplenames}_pharokka/{samplenames}_length_gc_cds_density.tsv"
                for cdsdens_file in glob.glob(cds_dens_pattern):
                    cdn=pd.read_csv(cdsdens_file, sep='\t')
                    gc_percent = cdn['gc_perc'].values[0]
                    coding_density = cdn['cds_coding_density'].values[0]
                    summary.write(f"GC percent: {gc_percent}\n")
                    summary.write(f"Coding density: {coding_density}\n")

                found_gene = False
                gbk_pattern = f"{annot}/phynteny-pr/{samplenames}_phynteny/phynteny.gbk"
                for gbk_file in glob.glob(gbk_pattern):
                    gbk_records = SeqIO.parse(gbk_file, 'genbank')
                    for record in gbk_records:
                        for feature in record.features:
                            if feature.type == "CDS" and 'product' in feature.qualifiers and 'integra' in feature.qualifiers['product'][0].lower():
                                #print (feature)
                                found_gene = True
                                gene_id = feature.qualifiers['locus_tag'][0]
                                function = feature.qualifiers['function'][0]
                                product = feature.qualifiers['product'][0]
                                summary.write(f"Integrase found: \t{gene_id}: function=\"{function}\", product=\"{product}\"\n")
                            elif feature.type == "CDS" and 'product' in feature.qualifiers and 'recombinase' in feature.qualifiers['product'][0].lower():
                                #print (feature)
                                found_gene = True
                                gene_id = feature.qualifiers['locus_tag'][0]
                                function = feature.qualifiers['function'][0]
                                product = feature.qualifiers['product'][0]
                                summary.write(f"Recombinase found: \t{gene_id}: function=\"{function}\", product=\"{product}\"\n")
                            elif feature.type == "CDS" and 'product' in feature.qualifiers and 'transposase' in feature.qualifiers['product'][0].lower():
                                #print (feature)
                                found_gene = True
                                gene_id = feature.qualifiers['locus_tag'][0]
                                function = feature.qualifiers['function'][0]
                                product = feature.qualifiers['product'][0]
                                summary.write(f"Transposase found:\t{gene_id}: function=\"{function}\", product=\"{product}\"\n")

                if not found_gene:
                    if 'integra' not in open(gbk_file).read().lower():
                        summary.write("No Integrases\n")
                    else:
                        summary.write("No Integrases\n")
                        summary.write("\t...but Phynteny predicted a few unknown function genes to have some similarity with integrase genes but with low confidence. Maybe a false positive or a novel integrase gene\n")

                    if 'recombinase' not in open(gbk_file).read().lower():
                        summary.write("No recombinase\n")
                    else: 
                        summary.write("Recombinases found in genome\n")
                        
                    if 'transposase' not in open(gbk_file).read().lower():
                        summary.write("No transposase\n")
                    else: 
                        summary.write("Transposases found in genome\n")

                #AMR genes 
                amr_pattern = f"{annot}/pharokka-pr/{samplenames}_pharokka/top_hits_card.tsv"
                card_pattern = f"{annot}/phold-pr/{samplenames}_phold/sub_db_tophits/card_cds_predictions.tsv"
                out_amr = f"{outdir}/{samplenames}_pharokka_card.tsv"
                out_card = f"{outdir}/{samplenames}_phold_card.tsv"
                amr_lines_count = count_lines(amr_pattern)
                card_lines_count = count_lines(card_pattern)
                if amr_lines_count == 1 and card_lines_count == 0:
                    summary.write("No AMR genes found\n")
                elif amr_lines_count != 1 :
                    summary.write("AMR genes found\n")
                    shutil.copy(amr_pattern, out_amr)
                elif card_lines_count != 0:
                    summary.write("AMR genes found\n")
                    shutil.copy(card_pattern, out_card)

                # Virulence genes
                vfdb_pattern = f"{annot}/pharokka-pr/{samplenames}_pharokka/top_hits_vfdb.tsv"
                vfdb_phold_pattern = f"{annot}/phold-pr/{samplenames}_phold/sub_db_tophits/vfdb_cds_predictions.tsv"
                vfdb_lines_count = count_lines(vfdb_pattern)
                phold_lines_count = count_lines(vfdb_phold_pattern)
                out_ph = f"{outdir}/{samplenames}_pharokka_vfdb.tsv"
                out_phold = f"{outdir}/{samplenames}_phold_vfdb.tsv"
                if vfdb_lines_count == 1 and phold_lines_count == 0:
                    summary.write("No virulence factor genes\n")
                elif vfdb_lines_count != 1:
                    summary.write("Virulence genes found\n")
                    shutil.copy(vfdb_pattern, out_ph)
                elif phold_lines_count != 0:
                    summary.write("Virulence genes found\n")
                    shutil.copy(vfdb_phold_pattern, out_phold)

                # CRISPR spacers
                spacers_pattern = f"{annot}/pharokka-pr/{samplenames}_pharokka/{samplenames}_minced_spacers.txt"
                acr_pattern = f"{annot}/phold-pr/{samplenames}_phold/sub_db_tophits/acr_cds_predictions.tsv"
                spacers_lines_count = count_lines(spacers_pattern)
                phold_lines_count = count_lines(acr_pattern)
                out_spacers = f"{outdir}/{samplenames}_pharokka_crispr.tsv"
                out_acr = f"{outdir}/{samplenames}_phold_acr.tsv"
                if spacers_lines_count == 0 and  phold_lines_count == 0:
                    summary.write("No anti CRISPR spacers found\n")
                elif spacers_lines_count != 0:
                    summary.write("anti-CRISPR spacers found\n")
                    shutil.copy(spacers_pattern, out_spacers)
                elif phold_lines_count != 0:
                    summary.write("anti-CRISPR spacers found\n")
                    shutil.copy(acr_pattern, out_acr)

                # Defense genes
                defense_pattern = f"{annot}/phold-pr/{samplenames}_phold/sub_db_tophits/defensefinder_cds_predictions.tsv"
                phold_lines_count = count_lines(defense_pattern)
                out_defense = f"{outdir}/{samplenames}_phold_defense.tsv"
                if phold_lines_count == 0:
                    summary.write("No Defense genes found\n")
                else:
                    summary.write("Defense genes found\n")
                    shutil.copy(defense_pattern, out_defense)
                summary.write("\n\n")

def generate_summary(input_files, output_summary, params):
    with open(output_summary, 'w') as summary:
        summary.write(f"Sample: {params['sample']}\n")
        if Path(input_files['table']).exists():
            line_count = sum(1 for line in open(input_files['table']))
            if line_count == 2:
                write_single_genome_summary(input_files, summary)
            elif line_count > 2:
                write_multiple_genome_summary(input_files, summary)
        else:
            summary.write("No contigs from the assembly were assigned viral, likely contigs too short in size\n")

def analyze_assembly(input_files, output_summary, params):
    file_content = Path(input_files['assembly']).read_text().splitlines()[-1]
    if 'Final assembly' in file_content or 'ALL DONE' in file_content:
        if Path(input_files['table']).exists():
            line_count = sum(1 for line in open(input_files['table']))
            if line_count == 2:
                copy_files(input_files, params)
                generate_summary(input_files, output_summary, params)
            elif line_count > 2:
                copy_multiple_files(params)
                generate_summary(input_files, output_summary, params)
            elif line_count == 1 :
                with open(output_summary, 'w') as summary:
                    summary.write(f"Sample: {params['sample']}\n")
                    filename = input_files['read']
                    with open(filename, 'r') as file:
                        contents = file.read()
                    summary.write(f"Total length of reads after QC and subsampling: {contents}\n")
                    summary.write("No contigs from the assembly were assigned viral, likely contigs too short in size\n")
        else:
            with open(output_summary, 'w') as summary:
                summary.write(f"Sample: {params['sample']}\n")
                filename = input_files['read']
                with open(filename, 'r') as file:
                    contents = file.read()
                summary.write(f"Total length of reads after QC and subsampling: {contents}\n")
                summary.write("No contigs from the assembly were assigned viral, likely contigs too short in size\n")
    else:
        with open(output_summary, 'w') as summary:
            summary.write(f"Sample: {params['sample']}\n")
            filename = input_files['read']
            with open(filename, 'r') as file:
                contents = file.read()
            summary.write(f"Total length of reads after QC and subsampling: {contents}\n")
            summary.write("Failed during assembly\n")            

# Replace input_files and output_params with the actual paths to your input/output files and parameters
input_files = {
        'read': snakemake.input.r,
        'assembly': snakemake.input.assembly,
        'table': snakemake.input.table,
        'genome': snakemake.input.genome,
        'gbk': snakemake.input.gbk,
        'plot': snakemake.input.plot,
        'taxa': snakemake.input.ph_taxa,
        'cdden': snakemake.input.cdden,
        'cds': snakemake.input.cds,
        'amr': snakemake.input.amr,
        'vfdb': snakemake.input.vfdb,
        'spacers': snakemake.input.spacers,
        'acr': snakemake.input.acr,
        'card': snakemake.input.card,
        'defense': snakemake.input.defense,
        'vfdb_phold': snakemake.input.vfdb_phold,
}

output_summary = snakemake.output.summary
annot= snakemake.params.annot
outdir=snakemake.params.outdir
params = {
    'sample' : snakemake.params.ID,
    'genomes': snakemake.params.genomes,
    'gbks' : snakemake.params.gbks,
    'plots': snakemake.params.plots,
    'annot': snakemake.params.annot
}

"""
input_files = {
    'assembly': '/home/nala0006/scratch/wine_achromobacter_sarah_output/sphae.out/PROCESSING/assembly/flye/SQK-RBK114-24_barcode19-sr/flye.log',
    'table': '/home/nala0006/scratch/wine_achromobacter_sarah_output/sphae.out/PROCESSING/genome/SQK-RBK114-24_barcode19-sr/SQK-RBK114-24_barcode19-genome-candidates.csv',
    'genome': '/home/nala0006/scratch/wine_achromobacter_sarah_output/sphae.out/PROCESSING/genome/SQK-RBK114-24_barcode19-sr/SQK-RBK114-24_barcode19_genome.fasta',
    'gbk': '/home/nala0006/scratch/wine_achromobacter_sarah_output/sphae.out/PROCESSING/pharokka/SQK-RBK114-24_barcode19-sr/phynteny/phynteny.gbk',
    'plot': '/home/nala0006/scratch/wine_achromobacter_sarah_output/sphae.out/PROCESSING/pharokka/SQK-RBK114-24_barcode19-sr/SQK-RBK114-24_barcode19_pharokka_plot.png',
    'amr': '/home/nala0006/scratch/wine_achromobacter_sarah_output/sphae.out/PROCESSING/pharokka/SQK-RBK114-24_barcode19-sr/top_hits_card.tsv',
    'vfdb': '/home/nala0006/scratch/wine_achromobacter_sarah_output/sphae.out/PROCESSING/pharokka/SQK-RBK114-24_barcode19-sr/top_hits_vfdb.tsv',
    'taxa': '/home/nala0006/scratch/wine_achromobacter_sarah_output/sphae.out/PROCESSING/pharokka/SQK-RBK114-24_barcode19-sr/SQK-RBK114-24_barcode19_top_hits_mash_inphared.tsv',
    'spacers': '/home/nala0006/scratch/wine_achromobacter_sarah_output/sphae.out/PROCESSING/pharokka/SQK-RBK114-24_barcode19-sr/SQK-RBK114-24_barcode19_minced_spacers.txt',
    'cdden': '/home/nala0006/scratch/wine_achromobacter_sarah_output/sphae.out/PROCESSING/pharokka/SQK-RBK114-24_barcode19-sr/SQK-RBK114-24_barcode19_length_gc_cds_density.tsv',
    'cds': '/home/nala0006/scratch/wine_achromobacter_sarah_output/sphae.out/PROCESSING/pharokka/SQK-RBK114-24_barcode19-sr/SQK-RBK114-24_barcode19_cds_functions.tsv'
}

output_summary = '/home/nala0006/scratch/wine_achromobacter_sarah_output/sphae.out/RESULTS/SQK-RBK114-24_barcode19_summary.txt'

params = {
    'sample': 'SQK-RBK114-24_barcode19',
    'genomes': '/home/nala0006/scratch/wine_achromobacter_sarah_output/sphae.out/RESULTS/SQK-RBK114-24_barcode19-sr/SQK-RBK114-24_barcode19_genome.fasta',
    'gbks': '/home/nala0006/scratch/wine_achromobacter_sarah_output/sphae.out/RESULTS/SQK-RBK114-24_barcode19-sr/SQK-RBK114-24_barcode19.gbk',
    'plots': '/home/nala0006/scratch/wine_achromobacter_sarah_output/sphae.out/RESULTS/SQK-RBK114-24_barcode19_pharokka_plot.png'
}
"""
analyze_assembly(input_files, output_summary, params)
