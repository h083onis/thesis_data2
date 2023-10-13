import sys
import json
import subprocess
from git import Repo
from gitdb.exc import BadName
import argparse
import pandas as pd

def pipe_process(commit, hexsha, tmp_list, type):
    is_contain = False
    if type == 'first':
        for filepath in commit.stats.files:
            tmp = filepath.split('.')
            if len(tmp) >= 2 and tmp[-1] in tmp_list:
                return True
    else:
        diff = commit.diff(hexsha)
        for item in diff:
            tmp = item.b_path.split('.')
            if len(tmp) >= 2 and tmp[-1] in tmp_list:
                return True
                
    return is_contain


def excute(params):
    # tmp_list = ['java','cpp','hpp','c','h']
    tmp_list = ['py']
    df = pd.read_csv(params.csv_filename, index_col=0)
    repo_list = list(df['repo_name'].unique())
    
    with open('openstack_confirm_ext.txt','a', encoding='utf-8') as f:
        for repo_name in repo_list:
            print(repo_name)    
            repo = Repo('../resource/repo/'+params.project+'/'+repo_name)
            id_list = df.loc[df['repo_name'] == repo_name, 'commit_id']
            for hexsha in id_list:
                commit = repo.commit(hexsha)
                try:
                    commit = repo.commit(hexsha+'~1')
                    flag = pipe_process(commit, hexsha, tmp_list, type='normal')
                except (IndexError, BadName):   
                    flag = pipe_process(commit, hexsha, tmp_list, type='first')
            if flag == False:
                print(hexsha, file=f)      
        
    
    


def read_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-csv_filename', type=str)
    parser.add_argument('-project', type=str, default='openstack')
    parser.add_argument('-json_name', type=str, default='qt.json')
    parser.add_argument('-auth_ext', type=str, default='java,py,cpp,h')
    parser.add_argument('-diff_range', type=str, default='0-0')
    return parser


if __name__ == '__main__':
    params = read_args().parse_args()
    excute(params)
    sys.exit(0)