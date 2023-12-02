import json
import re
import sys

def main(in_json_name, out_json_name, repo_name):
    json_open = open(in_json_name,'r')
    json_load = json.load(json_open)
    
    its_list = []
    if repo_name == 'qt':
        pattern = r'QTBUG-\d+'
    elif repo_name == 'openstack':
        pattern = r'bug[|.*\b](\d{6,})'
    else:
        return False
            
    repatter = re.compile(pattern, re.IGNORECASE)
    for commit in json_load:
        commit_dict = {}
        commit_dict['commit_id'] = commit['commit_id']
        result = repatter.findall(commit['msg'])
        print(result)
        if result == []:
            continue
        else:
            commit_dict['issue_id'] = list(set(value for tup in result for value in tup if value != ''))
        its_list.append(commit_dict)

    with open(out_json_name, 'w') as f:
        json.dump(its_list, f, indent=2)

if __name__ == '__main__':
    in_json_name = sys.argv[1]
    out_json_name = sys.argv[2]
    repo_name = sys.argv[3]
    flag  = main(in_json_name, out_json_name, repo_name)
    if flag == False:
        print("Isn't pattern for input of repo_name")