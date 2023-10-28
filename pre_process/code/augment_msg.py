import json
import sys
import re

def augment_msg(msg, issue_inf_list, repo_name):
    desc = ''
    for issue_inf in issue_inf_list:
        if repo_name == 'qt':
            pattern = r'({})'.format(issue_inf['issue_id'])
        elif repo_name == 'openstack':
            pattern = r'(bug.*\b{})'.format(issue_inf['issue_id'])
        repattern = re.compile(pattern, re.IGNORECASE)
        text = '('+repr(issue_inf['title'])+')'
        msg = re.sub(repattern, r'\1'+text, msg)
        if 'description' in issue_inf.keys():
            desc += '<desc>' + issue_inf['description']
    msg += desc
    return msg
    

def main(repo_json, issue_id_json, issue_inf_json, out_json, repo_name):
    with open(repo_json, 'r') as f_repo, open(issue_id_json, 'r') as f_id, open(issue_inf_json, 'r') as f_inf:
        repo_load = json.load(f_repo)
        issue_id_load = json.load(f_id)
        issue_inf_load = json.load(f_inf)
    
    commit_list = []
    commit_id_list = [commit['commit_id'] for commit in issue_id_load]
    for commit in repo_load:
        if commit['commit_id'] not in commit_id_list:
            commit_list.append(commit)
            continue
        commit_dict = {}
        commit_dict['commit_id'] = commit['commit_id']
        commit_dict['timestamp'] = commit['timestamp']
        issue_id_list = [commit3 for commit2 in issue_id_load if commit2['commit_id'] == commit['commit_id'] for commit3 in commit2['issue_id']]
        issue_inf_list = [issue_inf for issue_inf in issue_inf_load if issue_inf['issue_id'] in issue_id_list]
        augmented_msg = augment_msg(commit['msg'], issue_inf_list, repo_name)
        commit_dict['msg'] = augmented_msg
        commit_dict['codes'] = commit['codes']
        commit_list.append(commit_dict)
        
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(commit_list, f, indent=2)
    
if __name__ == '__main__':
    repo_json = sys.argv[1]
    issue_id_json = sys.argv[2]
    issue_inf_json = sys.argv[3]
    out_json = sys.argv[4]
    repo_name = sys.argv[5]
    main(repo_json, issue_id_json, issue_inf_json ,out_json, repo_name)