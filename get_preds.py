import assigntools.LoLa.tp
from assigntools.LoLa.tp import prover9_prove
from prepocessing import preprocessing
from lexical_knowledge import get_hypo_syn_lk
import json
import nltk
import pandas as pd
import re
import os
import numpy as np
from data_transformations import prepare_for_translation
import argparse

def negated(fol_string):
    return "not " + fol_string

def get_preds(translation_dict,dataset,columns,judgment_dict,csv_name: str, modification_id :str, use_lk : bool):
    '''
    columns should have format [[premise-1-column-name,premise-2-column-name,etc.],
    hypothesis-column-name, label-column-name]
    judgment_dict should have format {[value]:"e", [value]:"n",
    [value]:"c"}.
    modification_id indicates the modification used
    Returns a pandas dataframe with premises, hypothesis, e_pred and c_pred
    '''
    #TODO: change premises indeling back to one column with lists
    # Set everything up:
    # Exception dataframe
    start_d = {}
    start_d.update({'nl_ps':[],'fol_ps':[],'nl_h':[],'fol_h':[],'label':[]})
    start_d['exception'] = []
    e_df = pd.DataFrame(start_d)

    # Evaluation dataframe
    del start_d['exception']
    start_d.update({'e_pred':[],'c_pred':[]})
    df = pd.DataFrame(start_d)

    # Fill out nl and fol p's and h's
    for i_dat in range(len(dataset)):
        print("progress: " + str(int(i_dat/len(dataset)*100)) + "%", end='\r')
        
        #Get nl_premise, hypothesis and not(hypothesis) fol string representation
        nl_h = dataset[columns[1]][i_dat]        
        fol_h = translation_dict[nl_h]
        fol_h = preprocessing.fol2nltk(fol_h)
        fol_not_h = negated(fol_h)

        nl_ps_list = []
        fol_ps_list = []
        # Get premises and hypothesis natural string representation
        for prem_col in columns[0]:
            nl_p = dataset[prem_col][i_dat]
            nl_ps_list.append(nl_p)
            fol_p = translation_dict[nl_p]
            fol_p = preprocessing.fol2nltk(fol_p)
            fol_ps_list.append(fol_p)

        # Get label
        label = judgment_dict[dataset[columns[2]][i_dat]]

        if use_lk: 
            lk = get_hypo_syn_lk(fol_ps_list[0], fol_h) #in sick there's only 1 premise 
        else:
            lk = [] #no lexical knowledge 

        try:
            e_pred = prover9_prove(PROVER9_BIN, fol_h, fol_ps_list + lk)
            c_pred = prover9_prove(PROVER9_BIN, fol_not_h, fol_ps_list + lk)
            
            nl_ps = nl_ps_list[0]
            fol_ps = fol_ps_list[0]
            for i in range(len(nl_ps_list))[1:]:
                nl_ps = nl_ps + " ## " + nl_ps_list[i]  
                fol_ps = fol_ps + " ## "  + fol_ps_list[i] 
            df.loc[len(df)] = {'nl_ps':nl_ps,'fol_ps':fol_ps,'nl_h':nl_h,'fol_h':fol_h,'label':label,
            'e_pred':e_pred,'c_pred':c_pred}
        except Exception as a: 
            print(a)       
            e_df.loc[len(e_df)] = {'nl_ps':nl_ps,'fol_ps':fol_ps,'nl_h':nl_h,'fol_h':fol_h,'label':label,
            'exception':str(a)}
    if modification_id == "none" and not use_lk: #if there was no modification 
        if not os.path.isdir("evaluations"):        
            os.mkdir("evaluations")
        df.to_csv(f"evaluations/{csv_name}_evaluation.csv",sep='\t')
        e_df.to_csv(f"evaluations/{csv_name}_exceptions.csv",sep='\t')
    else:
        if not os.path.isdir("mod_evaluations"):        
            os.mkdir("mod_evaluations")
        df.to_csv(f"mod_evaluations/[{modification_id}][{use_lk}]{csv_name}_evaluation.csv",sep='\t')    #just save the evaluations

#get dataset information
parser = argparse.ArgumentParser()
parser.add_argument('dataset_name',choices=['sick_trial','sick_train','sick_test','syllogisms'],help='dataset_name')
parser.add_argument('modification_id',choices=['a2e', 'i2c_a2e', 'none'],help='modification_id')   #possible to have no modification
parser.add_argument('lexical_knowledge',choices=['True', 'False'],help='use lexical knowledge')  
args = parser.parse_args()
dataset_name = args.dataset_name  
modification_id = args.modification_id
lexical_knowledge = args.lexical_knowledge

if re.search(r'sick',dataset_name):
    # set modification type
    if modification_id == "none": 
        dictionary_path = "dictionaries/sick/full_sick_dictionary.json"
    else:
        dictionary_path = f"mod_dictionaries/[{modification_id}]full_sick_dictionary.json"
    #set lexical knowledge 
    if lexical_knowledge == "True":
        use_lk = True
    else:
        use_lk = False
    #set basic info
    relevant_column_list = [['sentence_A'],'sentence_B','entailment_judgment']
    judgment_dict = {"ENTAILMENT":"e","NEUTRAL":"n","CONTRADICTION":"c"}
    if dataset_name == "sick_trial":
        dataset_path = "datasets/sick/SICK_trial.csv"
    elif dataset_name == "sick_train":
        dataset_path = "datasets/sick/SICK_train.csv"
    elif dataset_name == "sick_test":
        dataset_path = "datasets/sick/SICK_test_annotated.csv"

elif dataset_name == "syllogisms":
    dataset_path = "datasets/syllogisms/syllogisms.csv"
    # set modification type
    if modification_id == "none": 
        dictionary_path = "dictionaries/syllogisms/syllogism_dict.json"
    else:
        raise Exception(f"There are no modified dictionaries for the {dataset_name} data set")
    #set lexical knowledge 
    if lexical_knowledge == "True":
        raise Exception(f"There is no lexical knowledge for the {dataset_name} data set")
    else:
        use_lk = False
    #set basic info
    relevant_column_list = [['prem_1','prem_2'],'hypothesis','label']
    judgment_dict = {"entailment":"e","neutral":"n","contradiction":"c"}

# elif dataset_name == "fracas":
#     dataset_path = 
#TODO: extend for other datasets    

#locate prover9
PROVER9_BIN = "./prover9/bin"
print("cur dir: ", os.getcwd())
#load dataset
dataset = pd.read_csv(dataset_path,header=0,sep="\t")

#get the dictionary
with open(dictionary_path,"r") as file:
    dictionary = json.load(file)

#get the predictions using the dictionary
get_preds(dictionary,dataset,relevant_column_list,judgment_dict,dataset_name,modification_id, use_lk)
