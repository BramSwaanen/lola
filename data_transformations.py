import numpy as np
import pandas as pd

def prepare_for_translation(dataset: pd.DataFrame, columns: list):
  '''
  Prepares a pandas_dataset for translation with simple_generate by 
  appending all dataset entries from the different columns
  and returning as one numpy-array with unique entries.
  '''
  res = []
  for column in columns:
    res = res + list(dataset[column])
  return np.unique(res)

def generate_translation_dict(nl_dataset, FOL_generator):
  '''
  Generates translation dictionary of the form {"nl_sentence":"fol_translation"} from nl_dataset using FOL_generator.
  Params:
  	- nl_dataset: list of nl sentences
  	- FOL_generator: logicllama translator from nl to fol
  '''
  translation_dict = {}
  for i,sent in enumerate(nl_dataset):
    translation_dict[sent] = FOL_generator(input_str={"NL":sent})[1][1]
  return translation_dict

def generate_samples_dict(dataset, n, generator):
  '''
  Generates a dictionary with as keys n samples selected from
  the dataset with as value their translation using generator.
  '''
  first_15_indexes = np.random.shuffle(dataset["id"])
  for i in first_15_indexes:
    data = data + [data['sentence_A'][i]] + [data['sentence_B'][i]]
  return generate_translation_dict(data,generator)

def prepare_for_sample(dataset, columns: list):
  '''
  Prepares dataset for translation with simple_generate by 
  appending all dataset entries from the different columns
  and returning as one numpy-array.
  '''
  res = []
  for column in columns:
    res = res + dataset[column]
  return np.array(res)
