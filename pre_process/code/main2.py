import sys
import subprocess
from git import Repo
from gitdb.exc import BadName
import argparse
import pandas as pd
from take_data import out_piece_snippet, out_snippet_to_txt, out_txt

def is_auth_ext(file_path, auth_ext):
    splited_file = file_path.split('.')
    if len(splited_file) == 2 and splited_file[1] in auth_ext:
        return True
    else:
        return False


def diff_texts(diff_range, cnt, snippet_filename):
    range_list = diff_range.split('-')
    for i in range(range_list[0], range_list[1]+1):
        command = 'diff -u -'+ str(i) +' ../resource/before.txt ../resource/after.txt'
        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
        output = process.communicate()[0]
        snippet_list = out_piece_snippet(output.decode('utf-8'))
        out_snippet_to_txt('../resource/' + snippet_filename + '_' + str(i) + '.txt', str(cnt), snippet_list)


def tokenize(command, repo, hexsha, filepath, type):
    process = subprocess.Popen(command.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    if type == 'before':
        output = repo.git.show(hexsha+"~1"+':'+filepath)
    else:
        output = repo.git.show(hexsha+':'+filepath)
    output = repo.git.show(hexsha+':'+filepath)
    process.stdin.write(output.encode(errors='ignore'))
    process.stdin.close()
    output = process.communicate()[0]
    out_txt('../resource/+'+type+'.txt', output.decode('utf-8'))
    return process



def pipe_process_first(cnt, repo,commit, hexsha, f_each_commit_file_inf ,f_error, params):
    error_ctx = ''
    command = 'java -jar ../package/tokenizer.jar'

    ch_type = 'A'
    for filepath in commit.stats.files:
        if is_auth_ext(filepath, params.auth_ext) == False:
            continue

        with open('../resource/before.txt','w', encoding='utf-8') as f:
            f.truncate(0)
        process1 = tokenize(command,  repo, hexsha, filepath, type='after')
        process1.wait()
        if process1.returncode != 0:
            error_ctx = hexsha+','+ch_type+','+filepath
            print(error_ctx, file=f_error)
            continue
        cnt += 1

        diff_texts(params.diff_range, cnt, params.snippet_filename)

        print(str(cnt)+','+hexsha+','+filepath+','+filepath +','+ch_type, file=f_each_commit_file_inf)
        
    return cnt   
    
    
def pipe_process(cnt, repo, commit, hexsha, f_each_commit_file_inf, f_error, params):
    error_ctx = ''
    command = 'java -jar ../package/tokenizer.jar'

    diff = commit.diff(hexsha)
    for item in diff:
        if is_auth_ext(item.b_path, params.auth_ext) == False:
            continue
        ch_type = item.change_type
        
        if ch_type == 'M' or ch_type == 'R':
            process1 = tokenize(command, repo, hexsha, item.a_path, type='before')
            process2 = tokenize(command, repo, hexsha, item.b_path, type='after')
            process1.wait()
            process2.wait()
            if process1.returncode != 0 or process2.returncode != 0:
                error_ctx = hexsha+','+ch_type+','+item.b_path
                print(error_ctx, file=f_error)
                continue
      
        elif ch_type == 'A':
            with open('../resource/before.txt','w', encoding='utf-8') as f:
                f.truncate(0)
            
            process3 = tokenize(command, repo, hexsha, item.b_path, type='after') 
            process3.wait()
            if process3.returncode != 0:
                error_ctx = hexsha+','+ch_type+','+item.b_path
                print(error_ctx, file=f_error)
                continue
        
        else:
            continue
        
        cnt += 1
        diff_texts(params.diff_range, cnt, params.snippet_filename)
        print(str(cnt)+','+hexsha+','+item.a_path+','+item.b_path +','+ch_type, file=f_each_commit_file_inf)
        
    return cnt


def excute(params):
    cnt = 0
    
    df = pd.read_csv(params.csv_filename, index_col=0)
    repo_list = list(df['repo_name'].unique())
    
    with open('../resource/'+params.hexsha_filename, 'a', encoding='utf-8') as f_each_commit_file_inf, \
            open('../resource/'+params.error_log_filename, 'a', encoding='utf-8') as f_error:
        for repo_name in enumerate(repo_list):
            print(repo_name)
            repo = Repo('../resource/repo/openstack'+repo_name)
            id_list = df.loc(df['repo_name'] == repo_name, 'commit_id')
            for commit_id in id_list:
                print(commit_id)
                target_hexsha = commit_id
                try:
                    commit = repo.commit(target_hexsha)
                    cnt = pipe_process_first(cnt, repo, commit, target_hexsha, f_each_commit_file_inf, f_error, params)
                except (IndexError, BadName):
                    commit = repo.commit(target_hexsha+'~1')
                    cnt = pipe_process(cnt, repo, commit, target_hexsha, f_each_commit_file_inf, f_error, params)


def read_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-csv_filename', type=str)
    parser.add_argument('-hexsha_filename', type=str, defalut='hexsha.txt')
    parser.add_argument('-snippet_filename', type=str, default='snippet.txt')
    parser.add_argument('-error_log_filename', type=str, defalut='error_log.txt')
    parser.add_argument('-auth_ext', type=str, default='java')
    parser.add_argument('-diff_range', type=str, default='1-10')


if __name__ == '__main__':
    params = read_args().parse_args()
    excute(params)
    sys.exit(0)