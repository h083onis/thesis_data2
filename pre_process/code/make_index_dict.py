import sys
import json

def des_sort(apper_dict):
    appear_list = sorted(apper_dict.items(), key= lambda word : word[1], reverse=True)
    return appear_list


def make_index_dict(in_json_name, out_json_name, min_freq):
    with open(in_json_name, 'r') as f:
        json_load = json.load(f)
    tmp_dict = {key:value for key, value in json_load.items() if value >= int(min_freq)}
    special_tokens = ['<unk>', '<pad>']
    dict = {token : i for i, token in enumerate(special_tokens)}
    for i, word in enumerate(des_sort(tmp_dict), len(special_tokens)):
        dict[word[0]] = i
    with open(out_json_name, 'w',encoding='utf-8') as f:
        json.dump(dict, f, indent=2)
    

if __name__ == '__main__':
    in_json_name = sys.argv[1]
    out_json_name = sys.argv[2]
    min_freq = sys.argv[3]
    make_index_dict(in_json_name, out_json_name, min_freq)