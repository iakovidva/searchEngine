import string
import unicodedata
import sys
import numpy as np
from bs4 import BeautifulSoup
import requests
import re
import multiprocessing
import time

def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])

def add_article_to_dict(article_name, the_article):
    global stopwords
    pl_word = 0
    max_tf = 1
    global max_nx
    for word in the_article.split():
        word = word.translate(str.maketrans('', '', string.punctuation))
        word = word.lower()
        word = remove_accents(word)
        if word not in stopwords:
            pl_word += 1
            if word in Indexer:  # word already in the dictionary
                found_word = Indexer[word]
                # increase overall impressions
                updated = Indexer[word]
                updated[1] += 1
                Indexer[word] = updated
                if article_name in found_word:  #word already in url
                    position = found_word.index(article_name)  # location of url
                    # increase impressions in url
                    updated = Indexer[word]
                    updated[position+1] += 1
                    Indexer[word] = updated
                    if found_word[position + 1] > max_tf:
                        max_tf = found_word[position + 1]
                else:  # add url in word's list
                    # increase the number of url's found
                    updated = Indexer[word]
                    updated[0] += 1
                    Indexer[word] = updated

                    # To find max_nx
                    if len(max_nx) > 0:
                        if (updated[0] >  max(max_nx)):
                            ei = max_nx
                            ei.append(updated[0])
                            max_nx = ei

                    shared_list = Indexer[word]
                    shared_list.append(article_name)
                    shared_list.append(1)
                    Indexer[word] = shared_list
            else:  # word not in dictionary
                alist = [1, 1, article_name, 1]
                Indexer.update({word: alist})
    articleInfo = [max_tf, pl_word]
    articlesDict.update({article_name: articleInfo})

def query_Indexer_build(query):
    global stopwords
    pl_word = 0
    global max_query_f
    for word in query.split():
        word = word.translate(str.maketrans('', '', string.punctuation))
        word = word.lower()
        word = remove_accents(word)
        if word not in stopwords:
            pl_word += 1
            if word in IndexerQ:
                IndexerQ[word] += 1
                if (IndexerQ[word]) > max_query_f: max_query_f = IndexerQ[word]
            else:
                IndexerQ.update({word: 1})

def idf_calculation(the_max_nx):
    for word in Indexer:
        updated = Indexer[word]
        updated[0] = np.log(1+the_max_nx / updated[0])
        Indexer[word] = updated

def similarityCalc():
    #words = lexi sto lexiko tou indexer
    #Indexer[words] = lista emfanisis tis lexis
    #Indexer[words][0] == IDF lexis
    #Indexer[words][i] == onoma apo kathe eggrafo
    #Indexer[words][i+1] == TF sto kathe eggrafo
    #IndexerQ[word] == TF sto Query
    #np.log(2) = IDF query
    #articlesDict[Indexer[words][i]][0]  Max_Tf keimenou
    #articlesDict[Indexer[words][i]][1] Megethos kathe eggrafou
    for word in IndexerQ:
        for words in Indexer:
            if word == words:
                for i in range(2, len(Indexer[words]), 2):
                    update_score = (Indexer[words][0]*Indexer[words][i+1]*IndexerQ[word]*np.log(2)) / (max_query_f * articlesDict[Indexer[words][i]][0])
                    if Indexer[words][i] in accumulators:
                        accumulators[Indexer[words][i]] += update_score
                    else:
                        accumulators.update({Indexer[words][i] : update_score})
    for x in accumulators:
        accumulators[x] = accumulators[x] / articlesDict[x][1]

def article(url):
    headers = requests.utils.default_headers()
    titlos = ""
    try:
        req = requests.get(url, headers)
        soup = BeautifulSoup(req.content, 'html.parser')
        body = soup.find('body')
        head = soup.find('head')
        if head is not None:
            title = str(head.find('title'))
            title = title.replace('<title>', '')
            title = title.replace('</title>', '')
            titlos = title
        all_par = body.findAll('p')
        art = ''
    except:
        return
    for par in all_par:
        par = str(par)
        clean = re.compile('<.*?>')
        par = re.sub(clean, '', par)
        art += par
    art = art + " " + 5 * titlos  # Title has more weight
    add_article_to_dict(url, art)

def linkFinder(url):
    headers = requests.utils.default_headers()
    try:
        req = requests.get(url, headers)
    except:
        return
    soup = BeautifulSoup(req.content, 'html.parser')
    all_links = soup.findAll('a', href=True)
    for link in all_links:
        link = link['href']
        if link.startswith('https://') | link.startswith('http://'):
            if len(sites_to_crawl) < (sites_to_exam):
                if link not in sites_to_crawl:
                    sites_to_crawl[link] = None
            else:
                break

#command line arguments
list = sys.argv
if (len(list)!=5):
    print ('You didnt give the right arguments (Ex. https://mypage.gr 200 1 8)')
    sys.exit()

#initializations
manager = multiprocessing.Manager()
manager2 = multiprocessing.Manager()
manager3 = multiprocessing.Manager()
manager4 = multiprocessing.Manager()
Indexer = manager.dict()
sites_to_crawl = manager2.dict()
max_nx = manager3.list()
max_nx.append(1)
articlesDict = manager4.dict()
IndexerQ = dict()
accumulators = dict()
stopwords = ['το', 'απο', 'στο', 'των', 'του', 'και', 'της', 'ειναι', 'Η','εκεινος','εκεινη','εκεινο','εκεινους','εκεινοι','αυτο','αυτον','αυτου','αυτη','αυτοι', 'o',
             'τα', 'οταν', 'στον', 'να', 'εχει', 'τους', 'μια', 'ότι', 'δυο', 'μεχρι', 'αλλα', 'θα', 'ενα', 'δεν', 'πως', 'που', 'τον', 'στην', 'την',
             'για', 'η', 'με', 'σε', 'τη', 'στη', 'οι', 'ότι', 'τις', 'ως', 'ηταν', 'στις', 'οποια', 'οπως', 'μετα', 'στα', 'πριν', 'γιατι', 'μας',
             '', 'οτι', 'στους', 'ειχε', 'καθε', 'μην', 'πιο', 'πολυ', 'μιας', 'αν', 'αυτος', 'ομως', 'καθως', 'ακομα', 'πρεπει', 'μονο', 'o',
             'μπορει', 'μας','εχουν', 'ενω', 'αφου', 'κι', 'υπαρχει', 'μπορει']
max_query_f = 1

starturl = list[1]
sites_to_crawl[starturl] = None
sites_to_exam = int(list[2])
start_time = time.time()
pool = multiprocessing.Pool(processes=int(list[4]))

#gathering_web_pages
while True:
    pool.map(linkFinder, sites_to_crawl)
    if len(sites_to_crawl) >= sites_to_exam: break

pool.map(article, sites_to_crawl)
idf_calculation(max(max_nx))

elapsed_time = time.time() - start_time
print("Execution time for crawling and indexing: ", elapsed_time)

query = input("Enter query: ")
top = int(input('Enter the number of the top documents: '))
query_Indexer_build(query)

similarityCalc()
accumulators = sorted(accumulators.items(), key=lambda kv: kv[1], reverse=True)
if (top > len(accumulators)):
    print("Can't find {} relative articles".format(top))
    top = len(accumulators)
count = 0
for x in accumulators:
    print("{}) {}, score: {}".format(count+1, x[0], x[1]))
    count += 1
    if count == top:
        break
