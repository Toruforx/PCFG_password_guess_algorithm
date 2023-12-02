# -*- coding: UTF-8 -*-
import re
import sys
import copy
from queue import PriorityQueue as pq
import itertools

#Four character regular expressions
Lpattern = re.compile('L')
Upattern = re.compile('U')
Dpattern = re.compile('D')
Spattern = re.compile('S')

#Read in the test set data
def load_testdata(path):
    testdata = {}
    with open(path, encoding='utf-8') as f:
        for line in f:
            pwd = line.strip()
            if pwd in testdata:
                testdata[pwd] += 1
            else:
                testdata.setdefault(pwd, 1)
    return testdata

#Divide the template into fragments
def split_base(base):
    pattern = re.compile(r'[LUDS]\d+',re.ASCII)
    pieces = re.findall(pattern, base)
    return pieces

#Get the number of characters before each fragment and the number of characters in the fragment
def piece_length(pieces, pivor, altype):
    len = [0] * 3
    prefix = ''.join(pieces[0:pivor])
    pattern = re.compile(r'\d+')
    len[0] = sum(map(int, re.findall(pattern, prefix)))
    len[1] = str(re.search(pattern, pieces[pivor]).group())
    len[2] = altype
    return len

#Determine if a fragment contains letters
def match_alpha(pieces):
    alpha = []
    for i, p in enumerate(pieces):
        if Upattern.match(p):
            len = piece_length(pieces, i, 'U')
            alpha.append(len)
        if Lpattern.match(p):
            len = piece_length(pieces, i, 'L')
            alpha.append(len)        
    return alpha


class Guess:
    #Initialize data
    def __init__(self, model, testdata, pwlower, pwupper, threshold):
        self.model = model
        self.total_guess = 0
        self.true_guess = 0
        self.queue = pq()
        self.testdata = testdata
        self.pwlower = pwlower
        self.pwupper = pwupper
        self.flag = 1
        self.threshold = threshold

    #Initialize the priority queue
    #For each queue element, 0-base 1-preterminal 2- probability 3-pivor 4-intermediate variables 5-times
    def init_queue(self):
        for base in self.model.bases:
            node = [None] * 6
            node[0] = split_base(base)
            node[3] = 0
            node[4] = split_base(base)
            node[5] = [0] * len(node[0])
            probability = self.model.bases[base]
            preterminal = ""

            for i, s in enumerate(node[0]):
                if Lpattern.match(s) or Upattern.match(s):
                    preterminal += s
                    continue
                else:
                    if Dpattern.match(s):
                        preterminal += self.model.digits[s][0][0]
                        node[4][i] = self.model.digits[s][0][0]
                        probability *= self.model.digits[s][0][1]
                    else:
                        preterminal += self.model.symbols[s][0][0]
                        node[4][i] = self.model.symbols[s][0][0]
                        probability *= self.model.symbols[s][0][1]
            if probability < self.threshold:
                continue
            node[1] = preterminal
            node[2] = probability
            self.queue.put(node)

    #Expand the queue element
    def insert_queue(self):
        if self.queue.empty():
            self.flag = 0
            return
        
        node = self.queue.get()
        pivor = node[3]
        base = node[0]
        alphalen = match_alpha(base)
        
        for i, s in enumerate(base):
            if i < pivor or Lpattern.match(s) or Upattern.match(s):
                continue
            if Dpattern.match(s) and node[5][i] == self.model.digittime[s]:
                continue
            if Spattern.match(s) and node[5][i] == self.model.symboltime[s]:
                continue
            newnode = copy.deepcopy(node)
            newnode[3] = i
            newnode[5][i] += 1
            if Dpattern.match(s):
                old = self.model.digits[s][node[5][i]]
                new = self.model.digits[s][newnode[5][i]]
            else:
                old = self.model.symbols[s][node[5][i]]
                new = self.model.symbols[s][newnode[5][i]]
            newnode[4][i] = new[0]
            newnode[2] = node[2] / old[1] * new[1]
            newnode[1] = ''.join(newnode[4])
            if newnode[2] < self.threshold:
                continue
            self.queue.put(newnode)
        return (alphalen, node[1], node[2])

    #Password guessing based on training data
    def guess_pwd(self, node):
        alphalen = node[0]
        pwd = node[1]
        prob = node[2]
        num = 0

        if not alphalen:
            self.total_guess += num
        else:
            alpha_replace = []
            
            for i in alphalen:
                if i[2] == 'L':
                    s = 'L' + i[1]
                    alpha_replace.append(self.model.lowers[s])
                else:
                    s = 'U' + i[1]
                    alpha_replace.append(self.model.uppers[s])
                
            alpha_replace = list(itertools.product(*alpha_replace))
            fpath = './template/' + list(self.model.bases.keys())[0] + '.txt'
            with open(fpath, "a+") as f:
                for rep in alpha_replace:
                    newpwd = pwd
                    newprob = prob
                    #PCFG padding
                    for i, s in enumerate(rep):
                        if alphalen[i][2] == 'L':
                            tmp = alphalen[i][0]
                            res = 'L' + alphalen[i][1]
                            newpwd = newpwd.replace(res, s, 1)
                            newprob *= self.pwlower[res][s]
                        else:
                            tmp = alphalen[i][0]
                            res = 'U' + alphalen[i][1]
                            newpwd = newpwd.replace(res, s, 1)
                            newprob *= self.pwupper[res][s]
                    
                    if newprob < self.threshold:
                        continue
                    num += 1
                    f.write(newpwd + '\t' + str(newprob) + '\n')
                    if newpwd in self.testdata:
                        self.true_guess += self.testdata[newpwd]
                        del self.testdata[newpwd]
            self.total_guess += num
