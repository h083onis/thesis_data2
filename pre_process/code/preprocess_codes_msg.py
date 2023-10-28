import nltk
from nltk import stem
from nltk.corpus import stopwords
from spiral import ronin
from pygments import lex
from pygments.lexers import PythonLexer
from pygments.lexers import JavaLexer
from pygments.lexers import CLexer
from pygments.lexers import CppLexer
from pygments.token import Token
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
        if token[0] in Token.String:
            code_list.append('<literal>')
        elif token[0] in Token.Name:
            code_list.extend(['<num>' if tmp.isnumeric() else tmp.strip().lower() for tmp in ronin.split(token[1])])
        elif token[0] in Token.Text:
            continue
        else:
            code_list.append(token[1].strip().lower())
    # return [tmp for tmp in code_list if tmp != '']
    return code_list


def process_codes(codes_list, codes_word_dict):
    codes_list2 = []
    for code_dict in codes_list:
        token_dict = {}
        ext = code_dict['filepath'].split('.')[-1]
        token_filepath = tokenize_code(code_dict['filepath'], ext)
        codes_word_dict = update_dict(token_filepath, codes_word_dict, type='code')
        token_dict['filepath'] = token_filepath
        
        for kind in ['added_code', 'deleted_code']:
            token_dict[kind] = []
            for line in code_dict[kind]:
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


def main(in_json_file, commit_inf_json, msg_dict_json, codes_dict_json):
    with open(in_json_file, 'r') as f_in:
        json_load = json.load(f_in)
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
        
    with open(commit_inf_json, 'w') as f_commit, open(msg_dict_json, 'w') as f_msg, open(codes_dict_json, 'w') as f_codes:
        json.dump(commit_list, f_commit, indent=2)
        json.dump(msg_word_dict, f_msg, indent=2)
        json.dump(codes_word_dict, f_codes, indent=2)
    
if __name__ == '__main__':
    in_json_file = sys.argv[1]
    commit_inf_json = sys.argv[2]
    msg_dict_json = sys.argv[3]
    codes_dict_json = sys.argv[4]
    main(in_json_file, commit_inf_json, msg_dict_json, codes_dict_json)

    