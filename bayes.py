import csv
from twitter_specials import *
import re
import math
import json

POS = 0
NEG = 1
NEU = 2
IRRE = 3
emotions = ["positive", "negative", "neutral", "irrelevant"]
category_total = [0,0,0,0]
word_prior_prob = {}
global total_rows


def parse_words():
    global total_rows
    with open("data/labeled_corpus.tsv", encoding="utf-8") as csvfile:
        readCSV = csv.reader(csvfile, delimiter='\t')
        count = 0
        for row in readCSV:
            #skip words with @ and strip punctuations from word
            count += 1
            line_arr = list(row)
            tweet = line_arr[0]
            category = line_arr[1]
            try:
                category_total[emotions.index(category)] += 1
            except:
                continue
            tweet = clean_tweet(tweet, emo_repl_order, emo_repl, re_repl)
            words = tweet.split()
            word_set = set()
            for w in words:
                if '@' not in w:
                    w = re.sub(r'[^\w\s]','',w)
                    word_set.add(w)

            #create prior probability dict
            for w in word_set:
                if w not in word_prior_prob:
                    word_prior_prob[w] = [0,0,0,0]
                if category == 'positive':
                    word_prior_prob[w][POS] += 1
                elif category == 'negative':
                    word_prior_prob[w][NEG] += 1
                elif category == 'neutral':
                    word_prior_prob[w][NEU] += 1
                elif category == 'irrelevant':
                    word_prior_prob[w][IRRE] += 1
        for w,value in word_prior_prob.items():
            for i in range(len(value)):
                word_prior_prob[w][i] = word_prior_prob[w][i]/float(category_total[i])
        total_rows = count

#classify each tweets into category with highest probability
def classify():
    global total_rows
    with open("data/geo_twits_squares.tsv", encoding="utf-8") as csvfile:
        readCSV = csv.reader((line.replace('\0','') for line in csvfile), delimiter='\t')
        result = []
        for row in readCSV:
            temp_result = []
            line_arr = list(row)
            temp_result.append(line_arr[0])
            temp_result.append(line_arr[1])
            tweet = clean_tweet(line_arr[2], emo_repl_order, emo_repl, re_repl)
            words = tweet.split()
            word_set = set()
            prob = [0,0,0,0]
            changed = False
            for w in words:
                if '@' not in w:
                    w = re.sub(r'[^\w\s]','',w)
                    if w in word_prior_prob:
                        for i in range(4):
                            try:
                                prob[i] += math.log(word_prior_prob[w][i])
                            except:
                                pass
                        changed = True
            for i in range(4):
                prob[i] += math.log(category_total[i]/float(total_rows))
            if changed:
                decision = prob.index(max(prob))
                if decision == 0:
                    temp_result.append("positive")
                elif decision == 1:
                    temp_result.append("negative")
                elif decision == 2:
                    temp_result.append("neutral")
                elif decision == 3:
                    temp_result.append("irrelevant")
            else:
                temp_result.append("irrelevant")
            result.append(temp_result)
        with open("locations_classified.tsv", "w") as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerows(result)

#calculate positivity score of each area
def positivity_score():
    positivity_dict = {}
    prev_key = None
    with open("locations_classified.tsv", encoding="utf-8") as csvfile:
        readCSV = csv.reader(csvfile, delimiter='\t')
        for row in readCSV:
            line_arr = list(row)
            if (line_arr[0], line_arr[1]) not in positivity_dict:
                if prev_key != None:
                    positivity_dict[prev_key] = (tracking[0]/tracking[-1] - tracking[1]/tracking[-1] + 1)/2
                prev_key = (line_arr[0], line_arr[1])
                tracking = [0.0, 0.0, 0.0, 0.0, 1.0]
                positivity_dict[(line_arr[0], line_arr[1])] = 0
                tracking[emotions.index(line_arr[2])] += 1
            else:
                tracking[emotions.index(line_arr[2])] += 1
                tracking[-1] += 1
        positivity_dict[prev_key] = (tracking[0]/tracking[-1] - tracking[1]/tracking[-1] + 1)/2
        convert_json(positivity_dict)


def convert_json(dict):
    data = []
    for key, value in dict.items():
        temp_dict = {}
        temp_dict["score"] = value
        temp_dict["g"] = float(key[1]) + 0.05/2
        temp_dict["t"] = float(key[0]) + 0.05/2
        data.append(temp_dict)
    with open("data.js", 'w') as outfile:
        outfile.write("var data = ")
        json.dump(data, outfile)


if __name__ == '__main__':
    parse_words()
    classify()
    positivity_score()
