import sys
import json

def des_sort(apper_dict):
    appear_list = sorted(apper_dict.items(), key= lambda word : word[1], reverse=True)
    return appear_list


def main(in_json_name, out_json_name, min_freq):
    json_open = open(in_json_name, 'r')
    json_load = json.load(json_open)
    
    json_load = des_sort(json_load)
    print(json_load)
    

if __name__ == '__main__':
    in_json_name = sys.argv[1]
    out_json_name = sys.argv[2]
    min_freq = sys.argv[3]
    main(in_json_name, out_json_name, min_freq) 