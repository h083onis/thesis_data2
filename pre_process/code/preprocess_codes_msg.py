import nltk
from nltk import stem
from nltk.corpus import stopwords
from spiral import ronin
from pygments import lex
from pygments.lexers import PythonLexer
from pygments.lexers import JavaLexer
from pygments.lexers import CLexer
from pygments.lexers import CppLexer
import sys
import json


def delete_stopwords(list):
    stopset = set(stopwords.words('english'))
    return [w for w in list if w not in stopset]


def stem_word(list):
    stemmer  = stem.PorterStemmer()
    return [stemmer.stem(w) for w in list]


def tokenize_msg(text):
    return stem_word(nltk.word_tokenize(text))


def tokenize_code(code, ext):
    if ext == 'py': 
        tokens = list(lex(code, PythonLexer()))
    elif ext == 'cpp' or ext == 'hpp':
        tokens = list(lex(code, CppLexer()))
    elif ext == 'c' or ext == 'h':
        tokens = list(lex(code, CLexer()))
    elif  ext == 'java':
        tokens = list(lex(code, JavaLexer()))
        
    code_list = []
    for token in tokens:
        if token[1].isidentifier():
            tmp_list = ronin.split(token[1])
            for tmp in tmp_list:
                code_list.append(tmp.strip().lower())
        else:
            code_list.append(token[1].strip().lower())
    return [token for token in code_list if token != '']


def process_codes(codes_list, codes_word_dict):
    codes_list2 = []
    for code_dict in codes_list:
        token_dict = {}
        token_filepath = [token.lower() for token in ronin.split(code_dict['filepath'])]
        codes_word_dict = update_dict(token_filepath, codes_word_dict, type='code')
        token_dict['filepath'] = token_filepath
        
        for kind in ['added_code', 'deleted_code']:
            token_dict[kind] = []
            for line in code_dict[kind]:
                ext = code_dict['filepath'].split('.')[-1]
                token_list = tokenize_code(line,ext)
                token_dict[kind].append(token_list)
                codes_word_dict = update_dict(token_list, codes_word_dict, type='code')
        codes_list2.append(token_dict)
    return codes_list2, codes_word_dict


def process_msg(msg, msg_word_dict):
    msg_list = tokenize_msg(msg)
    msg_word_dict = update_dict(msg_list, msg_word_dict, type='msg')
    return msg_list, msg_word_dict


def update_dict(word_list, word_dict, type):
    if type == 'msg':
        word_list = delete_stopwords(word_list)
    for word in word_list:
        if word not in word_dict.keys():
            word_dict[word] = 1
        else:
            cnt =  word_dict[word]
            word_dict[word] = cnt + 1
    return word_dict


def main(in_json_file, commit_inf_json, msg_vcb_json, codes_vcb_json):
    json_open = open(in_json_file, 'r')
    json_load = json.load(json_open)
    msg_word_dict = {}
    codes_word_dict = {}
    commit_list = []
    for commit in json_load:
        commit_dict = {}
        if commit['codes'] == []:
            continue
        commit_dict['commit_id'] = commit['commit_id']
        commit_dict['timestamp'] = commit['timestamp']
        msg_list, msg_word_dict = process_msg(commit['msg'], msg_word_dict)
        commit_dict['msg'] = msg_list
        codes_list, codes_word_dict = process_codes(commit['codes'], codes_word_dict)
        commit_dict['codes'] = codes_list
        commit_list.append(commit_dict)    
        
    with open(commit_inf_json, 'w') as f:
        json.dump(commit_list, f, indent=2)
    
    with open(msg_vcb_json, 'w') as f:
        json.dump(msg_word_dict, f, indent=2)
        
    with open(codes_vcb_json, 'w') as f:
        json.dump(codes_word_dict, f, indent=2)
    
    
if __name__ == '__main__':
    in_json_file = sys.argv[1]
    commit_inf_json = sys.argv[2]
    msg_vcb_json = sys.argv[3]
    codes_vcb_json = sys.argv[4]
    main(in_json_file, commit_inf_json, msg_vcb_json, codes_vcb_json)

    