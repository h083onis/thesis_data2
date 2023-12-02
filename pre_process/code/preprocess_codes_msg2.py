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
import pickle
import pandas as pd
import re


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
            code_list.append('<string>')
        # elif token[0] in Token.Number:
        #     code_list.append('<num>')
        elif token[0] in Token.Name:
            code_list.extend([tmp.strip().lower() for tmp in ronin.split(token[1])])
        elif token[0] in Token.Comment:
            code_list.extend([tmp.strip().lower() for tmp in tokenize_msg(token[1]) for tmp in ronin.split(tmp)])
        elif token[0] in Token.Text:
            continue
        else:
            code_list.append(token[1].strip().lower())
    code_list = [tmp.strip().lower() for tmp in code_list if tmp != '']
    
    return code_list


def process_codes(codes_list, codes_word_dict, type='train'):
    codes_list2 = []
    for code_dict in codes_list:
        ext = code_dict['filepath'].split('.')[-1]
        token_filepath = tokenize_code(code_dict['filepath'], ext)
        if type == 'train':
            codes_word_dict = update_dict(token_filepath, codes_word_dict)
        for kind in list(code_dict.keys())[1:]:
            for line in code_dict[kind]:
                token_list = ['<' + kind + '>']
                token_list += tokenize_code(line, ext)
                codes_list2.append(token_filepath + token_list)
                if type == 'train':
                    codes_word_dict = update_dict(token_list, codes_word_dict)
    return codes_list2, codes_word_dict


def process_msg(msg, msg_word_dict, type='train'):
    msg = msg.replace('\n'," ").replace('\r', " ")
    msg = re.sub(r'http?://[\w/:%#\$&\?\(\)~\.=\+\-]+', " ", msg)
    msg = re.sub(r'https?://[\w/:%#\$&\?\(\)~\.=\+\-]+', " ", msg)
    msg = re.sub(r'[!-/:-@[-`{-~¢-¿“-⟿⬀-⯐、-〶\u3099-ゞ・-ヾ㈠-㏿︐-﹪！-／：-＠［-｀｛-･ﾞﾟ￥]', " ", msg)
    msg = re.sub(r'\d+', '0', msg)
    
    msg_list = delete_stopwords(tokenize_msg(msg))
    msg_list = ['<num>' if tmp.isnumeric() else tmp for tmp in msg_list if tmp != '']
    if type == 'train':
        msg_word_dict = update_dict(msg_list, msg_word_dict)
    return msg_list, msg_word_dict


def update_dict(word_list, word_dict):
    for word in word_list:
        if word not in word_dict.keys():
            word_dict[word] = 1
        else:
            word_dict[word] += 1
    return word_dict


def main(in_json, in_csv, train_json, test_json, msg_dict_json, codes_dict_json):
    df = pd.read_csv(in_csv, index_col=0, header=0)
    df.set_index('commit_id', inplace=True)
    metrics_df = df.drop(['author_date', 'bugcount', 'fixcount', 'bugdens', 'buggy','strata'], axis=1)
    with open(in_json, 'r') as f_json:
        json_load = json.load(f_json)
    msg_word_dict = {}
    codes_word_dict = {}
    train_list = [[] for _ in range(6)]
    test_list = [[] for _ in range(6)]
    
    for i, commit in enumerate(json_load):
        print(i, commit['commit_id'])
        if commit['codes'] == []:
            continue
        if df.at[commit['commit_id'], 'strata'] != df['strata'].max():
            type = 'train'
            train_list[0].append(commit['commit_id'])
            train_list[1].append(df.at[commit['commit_id'], 'strata'])
            msg_list, msg_word_dict = process_msg(commit['msg'], msg_word_dict, type)
            train_list[2].append(msg_list)
            codes_list, codes_word_dict = process_codes(commit['codes'], codes_word_dict, type)
            train_list[3].append(codes_list)
            train_list[4].append(metrics_df.loc[commit['commit_id']])
            train_list[5].append(int(df.at[commit['commit_id'], 'buggy']))
        else:
            type = 'test'
            test_list[0].append(commit['commit_id'])
            test_list[1].append(df.at[commit['commit_id'], 'strata'])
            msg_list, msg_word_dict = process_msg(commit['msg'], msg_word_dict, type)
            test_list[2].append(msg_list)
            codes_list, codes_word_dict = process_codes(commit['codes'], codes_word_dict, type)
            test_list[3].append(codes_list)
            test_list[4].append(metrics_df.loc[commit['commit_id']])
            test_list[5].append(int(df.at[commit['commit_id'], 'buggy']))

    with open(train_json, 'wb') as f_train, open(test_json, 'wb') as f_test, open(msg_dict_json, 'w') as f_msg, open(codes_dict_json, 'w') as f_codes:
        pickle.dump(train_list, f_train)
        pickle.dump(test_list, f_test)
        json.dump(msg_word_dict, f_msg, indent=2)
        json.dump(codes_word_dict, f_codes, indent=2)
    
if __name__ == '__main__':
    in_json = sys.argv[1]
    in_csv = sys.argv[2]
    train_json = sys.argv[3]
    test_json = sys.argv[4] 
    msg_dict_json = sys.argv[5]
    codes_dict_json = sys.argv[6]
    main(in_json, in_csv, train_json, test_json, msg_dict_json, codes_dict_json)

    