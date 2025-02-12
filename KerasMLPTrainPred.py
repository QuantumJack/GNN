""" Train Multi Layer Perceptron and test.
   Arg1: base directory name for data files.
   Arg2: file name containing fold information (first row training indexes, second row test indexes)
"""

import os
import sys
import csv
import numpy as np
import pandas as pd
import itertools as it
import keras
from keras.models import Sequential
from keras.layers import Dense, Dropout
from keras.optimizers import RMSprop
from keras.regularizers import l2
import lib.data_rw as data_rw
import lib.keras_util as keras_util

def getModel(nDInput, nDOutput, layers_config, alpha):
    layers_config.append(nDOutput)
    isFirst = True
    model = Sequential()
    for nD in layers_config:
        if isFirst:
            model.add(Dense(nD, input_shape=(nDInput,), activation='sigmoid', kernel_regularizer=l2(alpha)))
            isFirst = False
        else:
            model.add(Dense(nD, activation='sigmoid'))
    return model

def run(data_filenames, fold_filename, alpha, layers_config, ge_range_all):
    fold_filepath = '{!s}/folds/{!s}'.format(dir_path, fold_filename)
    df_train_input, df_train_output, df_test_input, df_test_output = data_rw.loadData(data_filenames, fold_filepath)
    model = getModel(nDInput = df_train_input.shape[1],
                     nDOutput = df_train_output.shape[1],
                     layers_config = layers_config,
                     alpha = alpha)

    if ge_range_all:
        model = keras_util.apply_range(model, ge_range_all, df_train_output.columns)

    keras_util.fitModel(model, df_train_input.as_matrix(), df_train_output.as_matrix(), layers_config, alpha, "kmlp", dir_path, fold_filename)
    
    # Save test predictions:
    test_pred = model.predict(df_test_input.as_matrix())
    df_test_pred = pd.DataFrame(data = test_pred,
                                columns=df_test_output.columns,
                                index=None)
    data_rw.savePreds(df_test_pred, dir_path, fold_filename, layers_config, alpha, "kmlp")

    # Save training predictions:
    train_pred = model.predict(df_train_input.as_matrix())
    df_train_pred = pd.DataFrame(data = train_pred,
                                 columns=df_train_output.columns,
                                 index=None)
    data_rw.savePreds(df_train_pred, dir_path, fold_filename, layers_config, alpha, "train_kmlp")

dir_path = sys.argv[1] if len(sys.argv) > 1 else "/Users/ameen/mygithub/grnnPipeline/data/dream5/modules_gnw_a/size-20/top_edges-1_gnw_data/d_1/"
fold_filename = sys.argv[2] if len(sys.argv) > 2 else "n10_f1.txt"


data_filenames = {"NonTFs": '{!s}/processed_NonTFs.tsv'.format(dir_path),
                  "TFs" : '{!s}/processed_TFs.tsv'.format(dir_path),
                  "KOs" : '{!s}/processed_KO.tsv'.format(dir_path)}

ge_range_dic = data_rw.get_ge_range('{!s}/../ge_range.csv'.format(dir_path))

if len(sys.argv) <= 3:
    h_params = keras_util.loadMLPHyperParameters(dir_path)
    for row in h_params:
        alpha = row[0]
        mlp_layers_config = row[1]
        run(data_filenames, fold_filename, alpha, mlp_layers_config, ge_range_all=ge_range_dic)
else: # ToDo: should load config from a file instead
    alpha=0.8
    mlp_layers_config = []
    run(data_filenames, fold_filename, alpha, mlp_layers_config, ge_range_all=ge_range_dic)

keras.backend.clear_session()
