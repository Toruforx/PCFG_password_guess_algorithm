# -*- coding: UTF-8 -*-
# 实现了在09年论文的基础上进行两点优化的PCFG。
# 两点优化分别为：
# 1、将字母划分为大写字母和小写字母两种片段。
# 2、对于口令结构（模板）的概率计算方式使用n阶markov模型。而不是单纯使用频数相除计算。
from train import *
from guess import *
import argparse
from collections import OrderedDict

def main():
    #Use an interpreter to run programs easily
    parser = argparse.ArgumentParser(description="The modified PCFG")
    parser.add_argument('--path', type=str, default='myspace.txt')
    parser.add_argument('--rate', type=float, default=0.5)
    parser.add_argument('--threshold', type=float, default=0.000000001)
    parser.add_argument('--order', type=int, default=3)
    args = parser.parse_args()

    #Preprocessed dataset
    #preprocess(args.path, args.rate)

    #Use the training set for training to generate data
    traindata = load_traindata('traindata.txt')
    trainbase, trainlower, trainupper, traindigit, trainspecial, trainmarkov = statistic(traindata, args.order)
    generate_dict(trainlower, 'lowerdic.txt')
    generate_dict(trainupper, 'upperdic.txt')
    base_probability(trainbase, trainmarkov, args.order)
    trainbase = sorted(trainbase.items(), key=lambda t:t[1], reverse=True)
    
    #Password guessing based on training data
    testdata = load_testdata('testdata.txt')
    true_guess = 0
    total_guess = 0
    
    with open('result.txt', "a+") as f:
            f.write("true_guess / total_guess" + '\n')
            
    #Password guessing based on template probability from large to small
    for i in trainbase:
        #Initialize data
        base = OrderedDict([i])
        lower = copy.deepcopy(trainlower)
        upper = copy.deepcopy(trainupper)
        digit = copy.deepcopy(traindigit)
        special = copy.deepcopy(trainspecial)

        model = Train(base, digit, special)
        model.sort_dec()

        #Use a dictionary of letters generated from the training set
        #Reduce duplicate dictionaries
        model.load_dict('lowerdic.txt', 'upperdic.txt')
        part_probability(lower)
        part_probability(upper)

        #Start password guessing
        guesser = Guess(model, testdata, lower, upper, args.threshold)
        guesser.init_queue()
        
        #If flag is 0, it means an empty queue
        while True:
            temp = guesser.insert_queue()
            if guesser.flag:
                guesser.guess_pwd(temp)
            else:
                break
        
        #Calculate the number of guesses and correct times under the template
        true_guess += guesser.true_guess
        total_guess += guesser.total_guess

        #Write the number of guesses and the number of corrects to the result file
        with open('result.txt', "a+") as f:
            f.write(str(true_guess) + ' / ' + str(total_guess) + '\n')

if __name__ == "__main__":
    main()        