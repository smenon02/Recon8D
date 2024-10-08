# -*- coding: utf-8 -*-
"""ML function.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1GeLDE8egbID6JrHv8BnYnNIHxEqB2mT7

# ML function for metabolome predictions using Random Forests
"""

import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install('dill')
install('shap==0.37.0')
install('scikit-learn-intelex')
install('pandas')

import pandas as pd
import time
import sklearn
import numpy as np
from sklearn.model_selection import StratifiedKFold
from collections import Counter
import scipy
install('missingno')
import missingno
install('adjustText')
from adjustText import adjust_text
np.random.seed(123)
import dill
import math

# machine learning
# from sklearnex import patch_sklearn, unpatch_sklearn

from sklearn.model_selection import train_test_split
from sklearn.multioutput import MultiOutputRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import KFold
from sklearn.feature_selection import SelectKBest
from multiprocessing import Pool

# Commented out IPython magic to ensure Python compatibility.
#If running code on Google Colab, mount drive to access data files
import os
from google.colab import drive
drive.mount('/content/drive')
#Name of folder that holds datasets
file_folder = 'your_file_folder'
file_path = '/content/drive/My\ Drive/' + file_folder
# %cd {file_path}

# Read in data (rows = cell lines, columns = features)
input_features = pd.read_csv('./your_file_here.csv',index_col=0)
metabolomics = pd.read_csv('./your_metabolomics_here.csv',index_col=0)

"""# Random Forests"""

scaler = StandardScaler()
def train_multiRegressCV(classifier, data, x_cols, y_cols, n_splits=5, pval_cutoff=0.05, scale_y=True):

  # split into train and test data: all metabolites, median data
  X =  data.loc[:, x_cols]
  y =  data.loc[:, y_cols]

  # create multi-output ridge regression model
  if classifier=="RF":
    model=RandomForestRegressor(random_state=0, n_estimators=100, n_jobs=-1, max_depth=10)
    print("Training model with random forest!")

  else:
    print("Enter model type!")
    sys.exit()

  clf = MultiOutputRegressor(model)

  cv = KFold(n_splits=n_splits,
                shuffle=True,
                random_state=123)

  # create empty lists to store CV scores, confusion mat, etc.
  df_y_test_all = pd.DataFrame(columns=y_cols)
  df_y_pred_all = pd.DataFrame(columns=y_cols)

  count = 1

  # loop through cross-val folds
  all_means = pd.DataFrame(index=x_cols)

  for train_index, test_index in cv.split(X, y):
      start_time = time.perf_counter()
      print(count,flush=True)
      X_trainCV, X_testCV = X.iloc[train_index], X.iloc[test_index]
      y_trainCV, y_testCV = y.iloc[train_index], y.iloc[test_index]

      X_trainCV =  scaler.fit_transform(X_trainCV)
      X_testCV =  scaler.transform(X_testCV)

      if scale_y:
        y_trainCV =  scaler.fit_transform(y_trainCV)
        y_testCV =  scaler.transform(y_testCV)

      tmp_mdl = clf.fit(X_trainCV, y_trainCV)
      y_predCV = tmp_mdl.predict(X_testCV)

      df_pred_temp  = pd.DataFrame(y_predCV, columns=y_cols)
      df_test_temp = pd.DataFrame(y_testCV, columns=y_cols)

      df_y_test_all = pd.concat([df_y_test_all, df_test_temp])
      df_y_pred_all = pd.concat([df_y_pred_all, df_pred_temp])

      count = count+1

      finish_time = time.perf_counter()
      print("CV fold finished in {} seconds".format(finish_time-start_time),flush=True)

  #print("Shape of y_test:")
  #print(df_y_test_all.shape)
  #print("Calculating Pearson's R for each metabolite...")
  r = []
  for i, col in enumerate(y_cols):
    r.append(scipy.stats.pearsonr(df_y_test_all.iloc[:,i], df_y_pred_all.iloc[:,i]))

  df_results = pd.DataFrame(r, columns=['R','pval'], index=y_cols)  # index=y_cols,

  #print("Shape of results:")
  #print(df_results.shape)


  df_results['Significant']  = (df_results.pval < pval_cutoff) & (df_results.R > 0)
  df_results['R2']  = df_results.R**2

  X_final = scaler.fit_transform(X)
  X_final = pd.DataFrame(X_final,columns=X.columns,index=X.index)
  if scale_y:
    y_final = scaler.fit_transform(y)
    y_final = pd.DataFrame(y_final,columns=y.columns,index=y.index)

  print("Training final model on dataset of {} samples and {} features".format(X_final.shape[0], X_final.shape[1]))

  final_mdl = clf.fit(X_final, y_final)

  return df_results, final_mdl

"""# Ridge and Lasso Regression"""

scaler = StandardScaler()
def train_tune_CV(classifier,data, x_cols, y_cols,
                  n_splits=5, pval_cutoff=0.05, alphas=[1e-2, 0.1, 1, 10, 100, 1000], scale_y=True):

  # split into train and test data: all metabolites, median data
  X =  data.loc[:, x_cols]
  y =  data.loc[:, y_cols]

  if classifier=="Ridge":
    # create multi-output ridge regression model
    model=Ridge(alpha=1.0, max_iter=None, tol=0.001, solver='auto', random_state=0)
  elif classifier=="Lasso":
    model=Lasso(alpha=1.0, max_iter=500, tol=0.001, random_state=0)

  multi_ridge = MultiOutputRegressor(model)
  hyperParameters = {'estimator__alpha':alphas}
  gridSearch = GridSearchCV(multi_ridge, hyperParameters, scoring='r2', cv=5)

  cv = KFold(n_splits=n_splits,
                shuffle=True,
                random_state=123)

  # create empty lists to store CV scores, confusion mat, etc.
  df_y_test_all = pd.DataFrame(columns=y_cols)
  df_y_pred_all = pd.DataFrame(columns=y_cols)

  count = 1

  # loop through cross-val folds
  all_means = pd.DataFrame(index=x_cols)

  df_alpha_cv = pd.DataFrame()
  df_r_cv = pd.DataFrame()

  for count, (train_index, test_index) in enumerate(cv.split(X, y)):
      print(count)
      X_trainCV, X_testCV = X.iloc[train_index], X.iloc[test_index]
      y_trainCV, y_testCV = y.iloc[train_index], y.iloc[test_index]

      X_trainCV =  scaler.fit_transform(X_trainCV)
      X_testCV =  scaler.transform(X_testCV)

      if scale_y:
        y_trainCV = scaler.fit_transform(y_trainCV)
        y_testCV = scaler.transform(y_testCV)

      #
      tmp_mdl = gridSearch.fit(X_trainCV, y_trainCV)

      # predict on CV-test set
      y_predCV = tmp_mdl.predict(X_testCV)

      # store tuned alpha values
      my_alphas = []
      r_cv = []

      for i in range(len(tmp_mdl.best_estimator_.estimators_)):
        my_alphas.append(tmp_mdl.best_estimator_.estimators_[i].get_params()['alpha'])
        r_cv.append(scipy.stats.pearsonr(y_predCV[:,i], y_testCV[:,i])[0])

      df_alpha_cv.loc[:,count] = my_alphas
      df_r_cv.loc[:,count] = r_cv


      # # calculate r2 for true vs predicted values of CV-test set
      # tmp_scores = r2_score(y_testCV, y_predCV, multioutput='raw_values')

      df_pred_temp  = pd.DataFrame(y_predCV, columns=y_cols)
      df_test_temp = pd.DataFrame(y_testCV, columns=y_cols)

      df_y_test_all = pd.concat([df_y_test_all, df_test_temp])
      df_y_pred_all = pd.concat([df_y_pred_all, df_pred_temp])

  print("Calculating Pearson's R for each metabolite...")
  r = []
  for i, col in enumerate(y_cols):
    r.append(scipy.stats.pearsonr(df_y_test_all.iloc[:,i], df_y_pred_all.iloc[:,i]))

  df_results = pd.DataFrame(r, columns=['R','pval'], index=y_cols)  # index=y_cols,

  df_results['Significant']  = (df_results.pval < pval_cutoff) & (df_results.R > 0)
  df_results['R2']  = df_results.R**2

  print("For each metabolite, find CV fold with best R and get alpha...")
  ix_best_fold = df_r_cv.idxmax(axis=1)
  best_alphas = df_alpha_cv.values[np.arange(len(ix_best_fold)),ix_best_fold]
  Counter(best_alphas)
  #savetxt('best_alphas_phos.csv', best_alphas)

  print("Training final models with best alphas...")
  X_final = scaler.fit_transform(X)
  X_final = pd.DataFrame(X_final,columns=X.columns,index=X.index)
  if scale_y:
    y_final = scaler.fit_transform(y)
    y_final = pd.DataFrame(y_final,columns=y.columns,index=y.index)

  final_mdls = list()
  for i in range(len(best_alphas)):
    if classifier=="Ridge":
        model=Ridge(alpha=best_alphas[i], max_iter=None, tol=0.001, solver='auto', random_state=0)
    else:
        model=Lasso(alpha=best_alphas[i], max_iter=500, tol=0.001, random_state=0)
    model.fit(X_final.iloc[:,:], y_final.iloc[:,i])
    final_mdls.append(model)
  return df_results, final_mdls, best_alphas

# Get feature names

feature_names = input_features.columns

my_metabs = metabolomics.columns

feature_cell_lines = input_features.index

my_metabs_cls = metabolomics.index

# merge features+metabs by cell lines
merged_data = pd.merge(input_features, metabolomics, left_index=True, right_index=True)
print(merged_data.shape,flush=True)

#%%
print("METAB:",flush=True)
print(metabolomics.shape,flush=True)

print("\nFeats:",flush=True)
print(input_features.shape,flush=True)
merged_feats_mets =  pd.merge(input_features, metabolomics, left_index=True, right_index=True)
print(merged_feats_mets.shape,flush=True)

# Assign significance value (Bonferroni correction)
pval_cutoff_ccle = 0.05 / len(my_metabs)

results_df, model = train_multiRegressCV("RF",
                                            data = merged_feats_mets,
                                            x_cols = feature_names,
                                            y_cols = my_metabs,
                                            pval_cutoff = pval_cutoff_ccle,
                                            n_splits = 5)

print("Metabolites below Bonferroni pval cutoff: {}".format(np.sum(results_df.Significant)),flush=True)


#%%
df = pd.DataFrame({"pearsons_r":results_df.R,
                                "model_pval":results_df.pval,
                                "metabolite_significant":results_df.Significant})
df.to_csv("./your_results.csv")

# save models
print("Saving models!",flush=True)
with open('./your_final_rf_model.pkl', 'wb') as f:
   dill.dump(model, f)
print("Done!",flush=True)

"""# Example

Using CCLE Histone PTM Data and CCLE Metabolomics
"""

scaler = StandardScaler()
def train_multiRegressCV(classifier, data, x_cols, y_cols, n_splits=5, pval_cutoff=0.05, scale_y=True):

  # split into train and test data: all metabolites, median data
  X =  data.loc[:, x_cols]
  y =  data.loc[:, y_cols]

  # create multi-output ridge regression model
  if classifier=="RF":
    model=RandomForestRegressor(random_state=0, n_estimators=100, n_jobs=-1, max_depth=10)
    print("Training model with random forest!")

  else:
    print("Enter model type!")
    sys.exit()

  clf = MultiOutputRegressor(model)

  cv = KFold(n_splits=n_splits,
                shuffle=True,
                random_state=123)

  # create empty lists to store CV scores, confusion mat, etc.
  df_y_test_all = pd.DataFrame(columns=y_cols)
  df_y_pred_all = pd.DataFrame(columns=y_cols)

  count = 1

  # loop through cross-val folds
  all_means = pd.DataFrame(index=x_cols)

  for train_index, test_index in cv.split(X, y):
      start_time = time.perf_counter()
      print(count,flush=True)
      X_trainCV, X_testCV = X.iloc[train_index], X.iloc[test_index]
      y_trainCV, y_testCV = y.iloc[train_index], y.iloc[test_index]

      X_trainCV =  scaler.fit_transform(X_trainCV)
      X_testCV =  scaler.transform(X_testCV)

      if scale_y:
        y_trainCV =  scaler.fit_transform(y_trainCV)
        y_testCV =  scaler.transform(y_testCV)

      tmp_mdl = clf.fit(X_trainCV, y_trainCV)
      y_predCV = tmp_mdl.predict(X_testCV)

      df_pred_temp  = pd.DataFrame(y_predCV, columns=y_cols)
      df_test_temp = pd.DataFrame(y_testCV, columns=y_cols)

      df_y_test_all = pd.concat([df_y_test_all, df_test_temp])
      df_y_pred_all = pd.concat([df_y_pred_all, df_pred_temp])

      count = count+1

      finish_time = time.perf_counter()
      print("CV fold finished in {} seconds".format(finish_time-start_time),flush=True)

  #print("Shape of y_test:")
  #print(df_y_test_all.shape)
  #print("Calculating Pearson's R for each metabolite...")
  r = []
  for i, col in enumerate(y_cols):
    r.append(scipy.stats.pearsonr(df_y_test_all.iloc[:,i], df_y_pred_all.iloc[:,i]))

  df_results = pd.DataFrame(r, columns=['R','pval'], index=y_cols)  # index=y_cols,

  #print("Shape of results:")
  #print(df_results.shape)


  df_results['Significant']  = (df_results.pval < pval_cutoff) & (df_results.R > 0)
  df_results['R2']  = df_results.R**2

  X_final = scaler.fit_transform(X)
  X_final = pd.DataFrame(X_final,columns=X.columns,index=X.index)
  if scale_y:
    y_final = scaler.fit_transform(y)
    y_final = pd.DataFrame(y_final,columns=y.columns,index=y.index)

  print("Training final model on dataset of {} samples and {} features".format(X_final.shape[0], X_final.shape[1]))

  final_mdl = clf.fit(X_final, y_final)

  return df_results, final_mdl

features_file_path = "./CCLE_hist.csv"
metabolomics_file_path = "./CCLE_metabolomics_averages.csv"
input_features = pd.read_csv(features_file_path, index_col=0)
metabolomics = pd.read_csv(metabolomics_file_path, index_col=0)

# Get feature names

feature_names = input_features.columns

my_metabs = metabolomics.columns

feature_cell_lines = input_features.index

my_metabs_cls = metabolomics.index

# merge features+metabs by cell lines
merged_data = pd.merge(input_features, metabolomics, left_index=True, right_index=True)
print(merged_data.shape,flush=True)

#%%
print("METAB:",flush=True)
print(metabolomics.shape,flush=True)

print("\nFeats:",flush=True)
print(input_features.shape,flush=True)
merged_feats_mets =  pd.merge(input_features, metabolomics, left_index=True, right_index=True)
print(merged_feats_mets.shape,flush=True)

# Assign significance value (Bonferroni correction)
pval_cutoff_ccle = 0.05 / len(my_metabs)

results_df, model = train_multiRegressCV("RF",
                                            data = merged_feats_mets,
                                            x_cols = feature_names,
                                            y_cols = my_metabs,
                                            pval_cutoff = pval_cutoff_ccle,
                                            n_splits = 5)

print("Metabolites below Bonferroni pval cutoff: {}".format(np.sum(results_df.Significant)),flush=True)


#%%
df = pd.DataFrame({"pearsons_r":results_df.R,
                                "model_pval":results_df.pval,
                                "metabolite_significant":results_df.Significant})
df.to_csv("./CCLE_histone_results.csv")

# save models
print("Saving models!",flush=True)
with open('./CCLE_histone_model.pkl', 'wb') as f:
   dill.dump(model, f)
print("Done!",flush=True)
