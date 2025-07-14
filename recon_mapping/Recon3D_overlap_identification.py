# -*- coding: utf-8 -*-
"""
Created on Mon Jul 14 16:31:54 2025

@author: ryanseth
"""

import pandas as pd
import numpy as np

#%%
# Read in list of genes involved in associated reactions, top features, and matching BIGG IDs
recon_genes_from_metabolites = pd.read_csv('./genes_from_recon3d.csv') # enzymatically associated genes (or out to the first degree neighbor) generated using MATLAB (recon3d_mapping_script.mlx)
top_feature_inputs = pd.read_csv('./top_features_from_model.csv') # should be formatted with metabolites (rows) and top features (columns, descending order of importance)
name_translator_BiggIDs = pd.read_csv('./biggIDs_for_matching.csv') # file containing common gene names and BiggIDs for name conversion

#%%

def recon_mapping(recon_genes, top_features, name_translator, num_feats, num_metabs):
    # Rename common gene names to BiggIDs
    rename_dict = dict(zip(name_translator['Feats'], name_translator['BiggID']))
    top_features = top_features.replace(rename_dict)
    
    # Isolate the number of features you wish to investigate
    if num_feats == 1:
        top_features = top_features.iloc[:,0]
        top_features = pd.DataFrame(top_features)
    else:
        top_features = top_features.iloc[:,0:num_feats]
    
    # Find occurences of overlap
    present = []
    for i in range(0,num_metabs):
      if sum(np.isin(recon_genes.iloc[i,:], top_features.iloc[i,:]))>0:
        present.append("TRUE")
      else:
        present.append("FALSE")
    # Count total number of overlaps
    word_count = {}
    for word in present:
        word_count[word] = word_count.get(word,0) + 1
    print(word_count)
    
    # Identify central carbon metabolite locations
    central_carbon_metabolites = [1,4,7,9,10,15,16,17,19,29,31,32,36,37,39,53] # rows with central carbon metabolites - replace with unique locations in your data 
    
    central_overlaps = [present[i] for i in central_carbon_metabolites]
    
    # Count total number of overlaps in central carbon metabolites 
    word_count_central = {}
    for word in central_overlaps:
        word_count_central[word] = word_count_central.get(word,0) + 1
    print(word_count_central)
    
    return word_count, word_count_central

#%%
# Call function for counting overlaps
overlaps_transc_1, central_transc_1 = recon_mapping(recon_genes_from_metabolites, # genes associated with metabolite reactions in recon3D
                                                    top_feature_inputs, # dataframe of top features 
                                                    name_translator_BiggIDs, # conversion to BiggIDs
                                                    1, # number of features (columns) you wish to investigate
                                                    136 # number of metabolites in your panel
                                                    )

#%%









