import sys
import json
import subprocess
from git import Repo
from gitdb.exc import BadName
import argparse
import pandas as pd
from utils import out_code_dict, out_txt
from exclude_comment import exclude_comment

def is_auth_ext(file_path, auth_ext):
    splited_file = file_path.split('.')
    if len(splited_file) >= 2 and splited_file[-1] in auth_ext:
        return True
    else:
        return False


def diff_texts(filepath, hexsha, commit_dict):
    command = 'diff -B -w -u -0 ../resource/pre_process_data/before.txt ../pre_process_data/resource/after.txt'
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]
    code_dict = out_code_dict(output.decode('utf-8','ignore'))
    commit_dict[hexsha]['codes'][filepath]['added_code'].append(code_dict['added_code'])
    commit_dict[hexsha]['codes'][filepath]['deleted_code'].append(code_dict['deleted_code'])
    return commit_dict
        
        
def print_code(repo, hexsha, filepath, ext, type):
    if type == 'before':
        output = repo.git.show(hexsha+"~1"+':'+filepath)
    else:
        output = repo.git.show(hexsha+':'+filepath)
    output = exclude_comment(output, ext)
    out_txt('../resource/pre_process_data/'+type+'.txt', output)


def pipe_process(repo, commit, hexsha, params, commit_dict, type):
    auth_ext = params.auth_ext.split(',')
    if type == 'first':
        for filepath in commit.stats.files:
            if is_auth_ext(filepath, auth_ext) == False:
                continue
            ext = filepath.split('.')[1]
            commit_dict[hexsha]['codes'][filepath] = {}
            commit_dict[hexsha]['codes'][filepath]['added_code'] = []
            commit_dict[hexsha]['codes'][filepath]['deleted_code'] = []
            with open('../resource/pre_process_data/before.txt','w', encoding='utf-8') as f:
                f.truncate(0)
            print_code(repo, hexsha, filepath, ext, type='after')
            
            commit_dict = diff_texts(filepath, hexsha, commit_dict)
    
    else:
        diff = commit.diff(hexsha)
        for item in diff:
            if is_auth_ext(item.b_path, auth_ext) == False:
                continue
            ext = item.b_path.split('.')[1]
            commit_dict[hexsha]['codes'][item.b_path] = {}
            commit_dict[hexsha]['codes'][item.b_path]['added_code'] = []
            commit_dict[hexsha]['codes'][item.b_path]['deleted_code'] = []
            
            ch_type = item.change_type
            if ch_type == 'M' or ch_type == 'R':
                print_code(repo, hexsha, item.a_path, ext, type='before')
                print_code(repo, hexsha, item.b_path, ext, type='after')
            elif ch_type == 'A' or ch_type == 'C':
                with open('../resource/pre_process_data/before.txt','w', encoding='utf-8') as f:
                    f.truncate(0)
            
                print_code(repo, hexsha, item.b_path, ext, type='after')
            else:
                continue
            
            commit_dict = diff_texts(item.b_path, hexsha, commit_dict)

    return commit_dict


def excute(params):
    commit_dict = {}
    df = pd.read_csv(params.csv_filename, index_col=0)
    repo_list = list(df['repo_name'].unique())
    
    for repo_name in repo_list:
        print(repo_name)    
        repo = Repo('../resource/repo/'+params.project+'/'+repo_name)
        id_list = df.loc[df['repo_name'] == repo_name, 'commit_id']
        for hexsha in id_list:
            commit_dict[hexsha] = {}
            commit = repo.commit(hexsha)
            commit_dict[hexsha]['msg'] = commit.message
            commit_dict[hexsha]['codes'] = {}
 
            try:
                commit = repo.commit(hexsha+'~1')
                commit_dict = pipe_process(repo, commit, hexsha, params, commit_dict, type='normal')
            except (IndexError, BadName):   
                commit_dict = pipe_process(repo, commit, hexsha, params, commit_dict, type='first')
        break
    
    with open(params.json_name, 'w') as f:
        json.dump(commit_dict, f, indent=2)
    
    # hexsha = '0026b80cd2a484ad9d685ff5a4f89e6c9815f913'
    # repo_name ='qtbase'
    # repo = Repo('../resource/repo/'+params.project+'/'+repo_name)
    # commit_dict[hexsha] = {}
    # commit = repo.commit(hexsha)
    # commit_dict[hexsha]['msg'] = commit.message
    # commit_dict[hexsha]['codes'] = {}

    # try:
    #     commit = repo.commit(hexsha+'~1')
    #     commit_dict = pipe_process(repo, commit, hexsha, params, commit_dict, type='normal')
    # except (IndexError, BadName):   
    #     commit_dict = pipe_process(repo, commit, hexsha, params, commit_dict, type='first')
    # with open('test.json', 'w') as f:
    #     json.dump(commit_dict, f, indent=2)
    


def read_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-csv_filename', type=str)
    parser.add_argument('-project', type=str, default='qt')
    parser.add_argument('-json_name', type=str, default='qt2.json')
    parser.add_argument('-auth_ext', type=str, default='java,c,h,cpp,hpp,ts,js,py')
    return parser


if __name__ == '__main__':
    params = read_args().parse_args()
    excute(params)
    sys.exit(0)