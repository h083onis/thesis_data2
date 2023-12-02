import pandas as pd
import numpy as np
import argparse
import json
import pickle

def padding(data, max_len, max_lines=None, type='msg'):
    pad_data = []
    if type == 'msg':
        for value in data:
            if len(value) < max_len:
                pad_data.append(value + ['<pad>' for i in range(max_len-len(value))])
            elif len(value) > max_len:
                pad_data.append(value[:-(len(value)-max_len)])
            else:
                pad_data.append(value)
    else:
        for values in data:
            codes_list = []
            for i, value in enumerate(values, 1):
                if i > max_lines:
                    break
                if len(value) < max_len:
                    codes_list.append(value + ['<pad>' for i in range(max_len-len(value))])
                elif len(value) > max_len:
                    codes_list.append(value[:-(len(value)-max_len)])
                else:
                    codes_list.append(value)
            if len(codes_list) < max_lines:
                codes_list += [['<pad>' for i in range(max_len)] for i in range(max_lines-len(codes_list))]
            pad_data.append(codes_list)
    return pad_data


# def expand_dict(vob_dict, params):
#     keys = list(vob_dict.keys())
#     keys[:0] = params.special_tokens
#     return {key:i for i, key in enumerate(keys)}


def assign_index(pad_data, vob_dict, type='msg'):
    word_list = []
    mask_list = []
    if type == 'msg':
        for value in pad_data:
            word_list2 = []
            mask_list2 = []
            # print(value)
            for word in value:
                if word == '<pad>':
                    mask_list2.append(1)
                else:
                    mask_list2.append(0)
                if word in vob_dict.keys():
                    word_list2.append(vob_dict[word])
                else:
                    word_list2.append(vob_dict['<unk>'])
            word_list.append(word_list2)
            mask_list.append(mask_list2)
        return word_list, mask_list
    else:
        for values in pad_data:
            codes_list = [[vob_dict[word] if word in vob_dict.keys() else vob_dict['<unk>'] for word in lines]  for lines in values]
            word_list.append(codes_list)                
    return word_list


def process_msg(params, data, vob_dict, label_dict):
    pad_data = padding(data[2], params.max_msg_len, type='msg')
    word_list, mask_list = assign_index(pad_data, vob_dict, type='msg')
    
    label_list = [int(label_dict[commit]) for commit in data[0]]
    pkl_list = []
    pkl_list += [data[0], word_list, mask_list, label_list]
    pickle.dump(pkl_list, open(params.output_pkl, 'wb'))
    

def process_code(params, data, vob_dict, label_dict):
    pad_data = padding(data, params.max_codes_len, params.max_codes_lines, type='code')
    word_list = assign_index(pad_data, vob_dict, type='code')
    
    label_list = [int(label_dict[commit]) for commit in data[0]]
    pkl_list = []
    pkl_list += [data[0], word_list, label_list]
    pickle.dump(pkl_list, open(params.output_pkl, 'wb'))
 

def make_dataset(params):
    with open(params.input_dict, 'r', encoding='utf-8') as f_dict, open(params.input_data, 'rb') as f_data:
        data = pickle.load(f_data)
        vob_dict = json.load(f_dict)
    df = pd.read_csv(params.input_csv, index_col=0, header=0)
    label_dict = df[['commit_id', 'buggy']].set_index('commit_id')['buggy'].to_dict()
      
    if params.setting == 'msg':
        process_msg(params, data, vob_dict, label_dict)
    else:
        data = {commit['commit_id']:commit['codes'] for commit in data}
        process_code(params, data, vob_dict, label_dict)


def read_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i_csv', '--input_csv', type=str, required=True)
    parser.add_argument('-i_dict','--input_dict', type=str, required=True)
    parser.add_argument('-i_data', '--input_data', type=str, required=True)
    parser.add_argument('-s', '--setting', choices=['codes','msg'], required=True)
    # parser.add_argument('-o_dict', '--output_dict', type=str, required=True)
    parser.add_argument('-o_pkl', '--output_pkl', type=str, required=True)
    parser.add_argument('-max_m_len', '--max_msg_len', type=int, default=512)
    parser.add_argument('-max_c_len', '--max_codes_len', type=int, default=32)
    parser.add_argument('-max_c_lines', '--max_codes_lines', type=int, default=128)
    parser.add_argument('--special_tokens', type=list, default=['<unk>', '<pad>'])
    return parser


if __name__ == '__main__':
    params = read_args().parse_args()
    make_dataset(params)