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
from typing import List

def is_hexadecimal(value):
    try:
        int(value, 16)
        return True
    except ValueError:
        return False

def is_float(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

def is_integer(value):
    try:
        int(value)
        return True
    except ValueError:
        return False
    
def update_dict(word_list:List[str], word_dict:dict) -> None:
    for word in word_list:
        if word not in word_dict.keys():
            word_dict[word] = 1
        else:
            word_dict[word] += 1
            
def tokenize_msg(text:str) -> List[str]:
    # text = text.replace('\n'," ").replace('\r', " ")
    # text = re.sub(r'http?://[\w/:%#\$&\?\(\)~\.=\+\-]+', " ", text)
    # text = re.sub(r'https?://[\w/:%#\$&\?\(\)~\.=\+\-]+', " ", text)
    # text = re.sub(r'[!-/:-@[-`{-~¢-¿“-⟿⬀-⯐、-〶\u3099-ゞ・-ヾ㈠-㏿︐-﹪！-／：-＠［-｀｛-･ﾞﾟ￥]', " ", text)
    text = nltk.word_tokenize(text)
    stemmer = stem.PorterStemmer()
    stopset = set(stopwords.words('english'))
    text = [stemmer.stem(w) for w in text if w not in stopset]
    # text = ['<num>' if is_float(w) else '<num>' if is_integer(w) else '<num>' if is_hexadecimal(w) else w for w in text]
    # text = ['<num>' if w.isnumeric() else stemmer.stem(w) for w in text if w not in stopset]
    return text 

def tokenize_code(code:str, ext:str) ->List[str]:
    if ext == 'py': 
        tokens = list(lex(code, PythonLexer()))
    elif ext == 'cpp' or ext == 'hpp' or ext == 'cxx' or ext == 'hxx':
        tokens = list(lex(code, CppLexer()))
    elif ext == 'c' or ext == 'h':
        tokens = list(lex(code, CLexer()))
    elif ext == 'java':
        tokens = list(lex(code, JavaLexer()))
    
    code_list = []
    for token in tokens:
        if token[0] in Token.Literal:
            code_list.append('<literal>')
        elif token[0] in Token.Name:
            code_list.extend(['<num>'if tmp.isnumeric() else tmp.strip().lower() for tmp in ronin.split(token[1])])
        elif token[0] in Token.Comment:
            code_list.extend(['<num>'if tmp.isnumeric() else tmp.strip().lower() for tmp in nltk.word_tokenize(token[1]) for tmp in ronin.split(tmp)])
        elif token[0] in Token.Text:
            continue
        else:
            code_list.append(token[1].strip().lower())
        code_list = ['<num>' if is_float(w) else '<num>' if is_integer(w) else '<num>' if is_hexadecimal(w) else w for w in code_list]
    return code_list

def make_index_dict(word_dict:dict, min_freq=3) -> None:
    tmp_dict = {key:value for key, value in word_dict.items() if value >= int(min_freq)}
    special_tokens = ['<unk>', '<pad>']
    dict = {token : i for i, token in enumerate(special_tokens)}
    appear_list = sorted(tmp_dict.items(), key= lambda word : word[1], reverse=True)
    for i, word in enumerate(appear_list, len(special_tokens)):
        dict[word[0]] = i
    return dict

class MakeDataset():
    def __init__(self, in_json:json, in_csv:pd, project:str, its_json:json=None, its_id:json=None) -> None:
        with open(in_json, 'r') as f_json:
            self.data = json.load(f_json)
        self.its_inf = None
        self.commit_its_id = None
        if its_json != None and its_id != None:
            with open(its_json, 'r') as f_its, open(its_id, 'r') as f_id:
                self.its_inf = json.load(f_its)
                self.commit_its_id = {its['commit_id']:its['issue_id'] for its in json.load(f_id)}
        self.df = pd.read_csv(in_csv, index_col=0, header=0)
        self.df.set_index('commit_id', inplace=True)
        self.project = project
        self.train_list = [[] for _ in range(6)]
        self.test_list = [[] for _ in range(6)]
        self.msg_word_dict = {}
        self.codes_word_dict = {}
        
    def process(self) -> None:
        metrics_df = self.df.drop(['author_date', 'bugcount', 'fixcount', 'bugdens', 'buggy', 'strata'], axis=1)
        for i, commit in enumerate(self.data, 1):
            print(str(i) + '/'+ str(len(self.data)), commit['commit_id'])
            if commit['codes'] == []:
                continue
            if self.df.at[commit['commit_id'], 'strata'] != self.df['strata'].max():
                type = 'train'
                self.train_list[0].append(commit['commit_id'])
                self.train_list[1].append(self.df.at[commit['commit_id'], 'strata'])
                self.process_msg(commit['commit_id'], commit['msg'], type)
                self.process_codes(commit['codes'], type)
                self.train_list[4].append(metrics_df.loc[commit['commit_id']])
                self.train_list[5].append(int(self.df.at[commit['commit_id'], 'buggy']))
            else:
                type = 'test'
                self.test_list[0].append(commit['commit_id'])
                self.test_list[1].append(self.df.at[commit['commit_id'], 'strata'])
                self.process_msg(commit['commit_id'], commit['msg'], type)
                self.process_codes(commit['codes'], type)
                self.test_list[4].append(metrics_df.loc[commit['commit_id']])
                self.test_list[5].append(int(self.df.at[commit['commit_id'], 'buggy']))
        self.msg_word_dict = make_index_dict(self.msg_word_dict)
        self.codes_word_dict = make_index_dict(self.codes_word_dict)
        with open(self.project+'_train.pkl', 'wb') as f_train, open(self.project+'_test.pkl', 'wb') as f_test, \
            open(self.project+'_msg_dict.json', 'w') as f_msg, open(self.project+'_codes_dict.json', 'w') as f_codes:
            pickle.dump(self.train_list, f_train)
            pickle.dump(self.test_list, f_test)
            json.dump(self.msg_word_dict, f_msg, indent=2)
            json.dump(self.codes_word_dict, f_codes, indent=2)
        print('Finish Process')
        
    def augment_msg(self, msg:str, its_list:List) -> List[str]:
        desc = []
        for issue_inf in its_list:
            if self.project == 'qt':
                pattern = r'({})'.format(issue_inf['issue_id'])
            elif self.project == 'openstack':
                pattern = r'(bug[|.*\b]{})'.format(issue_inf['issue_id'])
            repattern = re.compile(pattern, re.IGNORECASE)
            text = '('+repr(issue_inf['title'])+')'
            msg = re.sub(repattern, r'\1'+text, msg)
            if 'description' in issue_inf.keys():
                desc += ['<desc>'] + tokenize_msg(issue_inf['description'])
        return tokenize_msg(msg) + desc
        
    def process_msg(self, commit_id:str, msg:str, type='train') -> None:
        if self.commit_its_id != None and commit_id in self.commit_its_id.keys():
            its_list = [its for its in self.its_inf if its['issue_id'] in self.commit_its_id[commit_id]]
            msg_list = self.augment_msg(msg, its_list)
        else:
            msg_list = tokenize_msg(msg)
        if type == 'train':
            update_dict(msg_list, self.msg_word_dict)
            self.train_list[2].append(msg_list)
        else:
            self.test_list[2].append(msg_list)
        
    def process_codes(self, codes_list:List[List[str]], type='train') -> None:
        codes_list2 = []
        for code_dict in codes_list:
            ext = code_dict['filepath'].split('.')[-1]
            token_filepath = tokenize_code(code_dict['filepath'], ext)
            if type == 'train':
                update_dict(token_filepath, self.codes_word_dict)
            for kind in list(code_dict.keys())[1:]:
                for line in code_dict[kind]:
                    token_list = ['<' + kind + '>']
                    token_list += tokenize_code(line, ext)
                    codes_list2.append(token_filepath + token_list)
                    if type == 'train':
                       update_dict(token_list, self.codes_word_dict)
        if type=='train':
            self.train_list[3].append(codes_list2)
        else:
            self.test_list[3].append(codes_list2)
        
if __name__ == '__main__':
    in_json = sys.argv[1]
    in_csv = sys.argv[2]
    project = sys.argv[3]
    if len(sys.argv) == 6:
        in_its = sys.argv[4]
        in_its_id = sys.argv[5]
        tmp = MakeDataset(in_json, in_csv, project, in_its, in_its_id)
    else:
        tmp = MakeDataset(in_json, in_csv, project)
    tmp.process()