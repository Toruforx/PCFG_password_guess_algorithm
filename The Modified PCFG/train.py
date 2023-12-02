# -*- coding: UTF-8 -*-
import re
import sys
import random

#Preprocess the dataset and divide it into training set and test set
def preprocess(path, rate):
    data = []
    pattern = re.compile(r'[^\x20-\x7e]')
    with open(path, encoding='utf-8') as f:
        for line in f:
            l = line.strip().split(' ', 1)
            num = int(l[0])
            pwd = l[1]
            if pattern.search(pwd) or ' ' in pwd:
                continue
            else:
                data.extend([pwd] * num)
    
    random.seed(1)
    sample = random.sample(range(0, len(data)), int(rate * len(data)))
    traindata = [data[i] for i in sample]
    testdata = [data[i] for i in range(len(data)) if i not in sample]

    with open("traindata.txt", "w") as f:
        for line in traindata:
            f.write(line + '\n')
    with open("testdata.txt", "w") as f:
        for line in testdata:
            f.write(line + '\n')

#Read in the training set data
def load_traindata(path):
    data = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            data.append(line.strip())
    return data

#Count occurrences of fragment in template
def count_times(part, mode, time):
    if mode in time:
        if part in time[mode]:
            time[mode][part] += 1
        else:
            time[mode].setdefault(part, 1)
    else:
        time.setdefault(mode, {})
        time[mode].setdefault(part, 1)

#Count the number of occurrences of each character under the specified preamble
def count_markov(mfrom, mto, markov):
    strfrom = ''.join(mfrom)
    if strfrom in markov:
        if mto in markov[strfrom]:
            markov[strfrom][mto] += 1
        else:
            markov[strfrom].setdefault(mto, 1)
    else:
        markov.setdefault(strfrom, {})
        markov[strfrom].setdefault(mto, 1)

#Calculate fragment probabilities
def part_probability(prob):
    for k1 in prob.keys():
        num = sum(prob[k1].values())
        for k2 in prob[k1].keys():
            prob[k1][k2] = prob[k1][k2] / num

#Calculate template probability using markov model
#Second point optimization
#Add end character
def base_probability(prob, markov, order):
    Bpattern = re.compile(r'[LUDS]\d+')
    for k1 in markov.keys():
        num = sum(markov[k1].values())
        for k2 in markov[k1].keys():
            markov[k1][k2] = markov[k1][k2] / num
    for k in prob.keys():
        tmp = [' '] * order
        pieces = re.findall(Bpattern, k)
        tmp.extend(pieces)
        tmp.extend(' ')
        prob[k] = 1
        for i in range(order, len(tmp)):
            p = ''.join(tmp[i-order:i])
            q = tmp[i]
            prob[k] = prob[k] * markov[p][q]
    num = sum(prob.values())
    for k in prob.keys():
        prob[k] = prob[k] / num

#Process the training data to get the required data
def statistic(data, order):
    mode = {}
    lower = {}
    upper = {}
    digit = {}
    special = {}
    markov = {}

    #Add end character
    #Generate structured password
    pattern = re.compile(r'[a-z]*|[A-Z]*|[0-9]*|[^a-zA-Z0-9]*')
    for pwd in data:
        res = ''
        tmp = [' '] * order
        parts = re.findall(pattern, pwd)
        for p in parts:
            if p == '':
                continue
            else:
                #First point optimization
                if p.islower():
                    m = "L" + str(len(p))
                    count_times(p, m, lower)
                elif p.isupper():
                    m = "U" + str(len(p))
                    count_times(p, m, upper)
                elif p.isdigit():
                    m = "D" + str(len(p))
                    count_times(p, m, digit)
                else:
                    m = "S" + str(len(p))
                    count_times(p, m, special)
            res += m
            tmp.append(m)
        if res in mode:
            mode[res] += 1
        else:
            mode.setdefault(res, 1)
        tmp.append(' ')
        for i in range(order, len(tmp)):
            count_markov(tmp[i-order:i], tmp[i], markov)
    return mode, lower, upper, digit, special, markov

#Generate dictionary
def generate_dict(alpha, fname):
    with open(fname, "w") as f:
        for key in alpha.keys():
            for value in list(alpha[key].keys()):
                f.write(value + '\n')

class Train:
    #Initialize data
    def __init__(self, bases, digits, symbols):
        self.bases = bases
        self.digits = digits
        self.symbols = symbols
        self.lowers = {}
        self.uppers = {}
        self.digittime = {}
        self.symboltime = {}
        self.lowertime = {}
        self.uppertime = {}
        self.lsize = 0
        self.usize = 0
    
    #Sort numbers and special symbols in descending order
    def sort_dec(self):
        part_probability(self.digits)
        part_probability(self.symbols)
        
        for key, value in self.digits.items():
            self.digits[key] = sorted(value.items(), key=lambda t:t[1], reverse=True)
            self.digittime[key] = len(self.digits[key]) - 1        
        for key, value in self.symbols.items():
            self.symbols[key] = sorted(value.items(), key=lambda t:t[1], reverse=True)
            self.symboltime[key] = len(self.symbols[key]) - 1

    #Import both uppercase and lowercase dictionaries
    def load_dict(self, pathl, pathu):
        with open(pathl, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                self.lsize += 1
                m = 'L' + str(len(line))
                if m not in self.lowers:
                    self.lowers[m] = []
                self.lowers[m].append(line)
        for i in self.lowers:
            self.lowertime[i] = len(self.lowers[i])

        with open(pathu, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                self.usize += 1
                m = 'U' + str(len(line))
                if m not in self.uppers:
                    self.uppers[m] = []
                self.uppers[m].append(line)
        for i in self.uppers:
            self.uppertime[i] = len(self.uppers[i])
        