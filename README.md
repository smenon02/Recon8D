# Recon8D: A metabolic regulome network from oct-omics and machine learning
Recon8D utilizes oct-omics (genomics, histone PTMs, DNA methylation, transcriptomics, RNA splicing, miRNA, proteomics, and phosphoproteomics) to predict metabolomic variation across cancer lines from the Cancer Cell Line Encyclopedia, thereby inferring a multiomic prediction network of the metabolome. 

File descriptions

RF_restuls: Pearson's correlations and p-values for all metabolite models from each of 8 omics classes. 

example_datasets: metabolomics and histone PTM data that can be used to test the machine lerning code present in this repository. 

omics_top_features: top 10 features for all metabolite models from each of 8 omics classes. 

recon_mapping: MATLAB and Python scripts for extracting genes from reactions involving metabolites of interest and matching them with top feature lists. 

ML_function.ipynb: ML script for random forests, ridge regression, and lasso regression, along with example code for using histone PTM data as input. 
