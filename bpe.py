# -*- coding: utf-8 -*-
"""
Created on Tue Oct 29 15:50:37 2019

@author: 63184
"""

import re, collections, json, copy

def get_vocab(filenames):
    vocab = collections.defaultdict(int)
    for filename in filenames:
        with open(filename, 'r', encoding='utf-8') as fhand:
            for line in fhand:
                line_dict = json.loads(line.strip())
                words = line_dict['context'].lower().split() + line_dict['response'].lower().split()
                for word in words:
                    vocab[' '.join(list(word)) + ' </w>'] += 1
    return vocab

def get_vocab2(filename):
    vocab = collections.defaultdict(int)
    myDict = dict()
    with open(filename) as f:
        myDict = json.load(f)
    for k, v in myDict.items():
        words = v['message_body'].lower().strip().split() + v['course'].lower().split()
        for word in words:
            vocab[' '.join(list(word)) + ' </w>'] += 1
    return vocab

def get_stats(vocab):
    pairs = collections.defaultdict(int)
    pair2word = collections.defaultdict(set)
    tokens = collections.defaultdict(int)
    for word, freq in vocab.items():
        symbols = word.split()
        for i in range(len(symbols)-1):
            key = (symbols[i],symbols[i+1])
            pairs[key] += freq
            pair2word[key].add(word)
            tokens[symbols[i]] += freq
        tokens[symbols[-1]] += freq
    return pairs, pair2word, tokens

def merge_vocab(pair, v_in, update_set, pairs, pair2word, tokens):
    bigram = re.escape(' '.join(pair))
    pair_combine = ''.join(pair)
    p = re.compile(r'(?<!\S)' + bigram + r'(?!\S)')
    
    for word in update_set:
        w_out = p.sub(pair_combine, word)
        v_in[w_out] = v_in[word]
        del v_in[word]
        symbols = word.split()
        for i in range(len(symbols)-1):
            key = (symbols[i], symbols[i+1])
            pairs[key] -= v_in[w_out]
            tokens[symbols[i]] -= v_in[w_out]
            if tokens[symbols[i]] == 0:
                del tokens[symbols[i]]
            if word in pair2word[key]:
                pair2word[key].remove(word)
            if pairs[key] == 0:
                del pairs[key]
                del pair2word[key]
        tokens[symbols[-1]] -= v_in[w_out]
        if tokens[symbols[-1]] == 0:
            del tokens[symbols[-1]]
        
        symbols = w_out.split()
        for i in range(len(symbols)-1):
            key = (symbols[i], symbols[i+1])
            pairs[key] += v_in[w_out]
            pair2word[key].add(w_out)
            tokens[symbols[i]] += v_in[w_out]
        tokens[symbols[-1]] += v_in[w_out]
    
    return v_in, pairs, pair2word, tokens

def save_obj_dict(path, myDict):
    jsObj = json.dumps(myDict)
    fileObj = open(path, 'w')
    fileObj.write(jsObj)
    fileObj.close()
    print('data have been saved to', path)
    
def bpe(srcname, dstname, dstname_vo, target_num):
    vocab = get_vocab(srcname)
    print('finish generate the vocab, there are', len(vocab), 'vocab.')
    #vocab = get_vocab2(srcname)
    pairs, pair2word, sub_words = get_stats(vocab)
    cnt = 0
    while len(sub_words) < target_num:
        if not pairs:
            break
        best = max(pairs, key=pairs.get)
        store_best = pairs[best]
        vocab, pairs, pair2word, sub_words = merge_vocab(best, vocab, copy.deepcopy(pair2word[best]), pairs, pair2word, sub_words)
        cnt += 1
        if cnt % 1 == 0:
            print(cnt, 'iteration finish, the size of sub words is:', len(sub_words), ', best freq is:', store_best)
    print('there are', len(sub_words), 'sub words.')
    save_obj_dict(dstname, sub_words)
    save_obj_dict(dstname_vo, vocab)
    
if __name__ == '__main__':
    bpe(['useful_dataset/test.json', 'useful_dataset/val.json', 'useful_dataset/train.json'], 'sub_words.json', 'vocab.json', 64000)