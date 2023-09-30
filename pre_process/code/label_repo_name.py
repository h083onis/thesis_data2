from git import Repo, GitCommandError
import pandas as pd
import sys

def label_repo_name(repo_path, label_csv):
    repo = Repo(repo_path)
    repo_name = repo_path.split('/')[-1]
    df = pd.read_csv(label_csv, index_col=0)
    id_list = df.loc[df['repo_name'] == '*','commit_id']
    print(len(id_list))
    for i, id in enumerate(id_list):
        try:
            if repo.git.log(id):
                df.loc[df['commit_id'] == id,'repo_name'] = repo_name
                print(i)
        except GitCommandError:
            continue

    df.to_csv('qt_reponame.csv')

def main():
    repo_path = sys.argv[1]
    label_csv = sys.argv[2]
    label_repo_name(repo_path, label_csv)
    
    
    
if __name__ == '__main__':
    main()