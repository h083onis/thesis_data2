import nltk
from nltk import stem
from nltk.corpus import stopwords
import torchdata.datapipes as dp
import torchtext.transforms as T
from torchtext.vocab import build_vocab_from_iterator

def delete_stopwords(list):
    stopset = set(stopwords.words('english'))
    tmp_list = [w for w in list if w not in stopset]
    return tmp_list

def stem_word(list):
    stemmer  = stem.PorterStemmer()
    tmp_list = [stemmer.stem(w) for w in list]
    return tmp_list

def tokenize_msg(text):
    tmp_list = nltk.word_tokenize(text)
    return tmp_list

# def make_dic(text):
#     dic = {}
#     tmp_list = stem_word(delete_stopwords(tokenize_msg(text)))
#     for w in tmp_list:
#         if w not in dic.keys():
#             dic[w] = 1
#         else:
#             cnt = dic[w]
#             dic[w] = cnt + 1

def getTokens(data_iter):
    for msg in data_iter:
        yield stem_word(delete_stopwords(tokenize_msg(msg)))
    
FILE_PATH = '../../resource/'
data_pipe = dp.iter.IterableWrapper([FILE_PATH])
data_pipe = dp.iter.FileOpener(data_pipe, mode='rb')
data_pipe = data_pipe.parse_csv(skip_lines=0, delimiter=',', as_tuple=True)

source_vocab = build_vocab_from_iterator(
    getTokens(data_pipe),
    min_freq = 4,
    specials = ['<pad>','<unk>'],
    special_first= True
)

source_vocab.set_default_index(source_vocab['<unk>'])

def getTransform(vocab):
    text_transform = T.Sequential(
        T.VocabTransform(vocab=vocab)
    )
    return text_transform

temp_list = list(data_pipe)
some_sentence = temp_list[0]
print("Some sentence=", end="")
print(some_sentence)
transformed_sentence = getTransform(source_vocab)(tokenize_msg(some_sentence))
print("Transformed sentence=", end="")
print(transformed_sentence)
index_to_string = source_vocab.get_itos()
for index in transformed_sentence:
    print(index_to_string[index], end=" ")

    