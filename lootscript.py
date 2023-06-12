#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: fscript
"""

### Some Players were deleted from the Forum.
### This list contains their IDs, so they can be filtered out of mentions and quotes.
### Feel free to add some.
### Could also be used to remove a Player that wishes not to be subject of the statistics.
playerID_mask=[0,7,367,826,2876,2350,5659]

import requests
import os
import string
import re
from bs4 import BeautifulSoup
import numpy as np
import datetime as dt
import gzip
import os.path
import lootplotlib as lpl
from tabulate import tabulate


def my_profiling(funk,dump_the_stats=False):
    import cProfile
    import pstats
    with cProfile.Profile() as pr:
        output=funk()
    stats = pstats.Stats(pr)
    stats.sort_stats(pstats.SortKey.TIME)
    stats.print_stats()
    if dump_the_stats:
        stats.dump_stats(filename=f"{funk.__name__}_stats.prof")
    return(output)

def binput(prompt,yes_defaulf=False):
    yes_no=" ".join([prompt,"Please enter [yes]/no: "]) if yes_defaulf else " ".join([prompt,"Please enter yes/[no]: "])
    while True: 
        user_input=input(yes_no)
        if user_input == "":
            return(yes_defaulf)
        if user_input[0].lower() == 'y':
            return(True)
        if user_input[0].lower() == 'n':
            return(False)
        else:
            print("Invalid, try again...")        

def player_from_id(id_,players):
    if id_==0:
        return("player not found (0)")
    try:
        return(players["player_name"][players["player_id"]==id_])
    except(ValueError):
        return("player not found ({})".format(id_))
    
def date2code(Y,M=1,D=1,h=0,m=0,s=0):
    return(int(dt.datetime.timestamp(dt.datetime(Y,M,D,h,m,s))))

def code2date(code):
    return(dt.datetime.fromtimestamp(code))

day_sec=60*60*24


    # Mindestens 5 Wörter.
    # Keine 100% sinnlosen Posts (Warscheinlich die schwerste Aufgabe :p)
    # Der erste Buchstabe bei dem ersten Wort muss immer groß sein und am Ende des Satzes muss ein Satzzeichen oder Smiley stehen (Wir sind hier doch eine gesittete Community... Oder? :D)

def rule_check(text,len_text): # Werden die Regeln befolgt? True/False
    try: 
        return((len_text>=5) and (re.sub(f"[{string.punctuation}{string.whitespace}{string.digits}]","",text)[0].isupper()) and (text[-1] in string.punctuation))
    except(IndexError):
        return(False)

def postlikes(likes):
    if likes is None: # Check for likes
        return(0)
    Nl=len(likes.find_all('bdi')) # count directly mentioned likes 
    if Nl<3:
        return(Nl)
    for bdi in likes("bdi"):
        bdi.decompose() # Remove player names
    # Return counted likes plus the 3 being counted
    try:
        return int(re.findall(r"\d+", likes.get_text(strip=True))[0]) + Nl
    except IndexError:
        return Nl # No additional likes
            
def post_text_cleanup(testext,postid,junkclass=["js-extraPhrases"]):
    """
    Cleanupfunction for post text, with extraction of mentions and quotes
    
    Parameters:
        testtext  -> the text of a post as a BeatifulSoup
        postid    -> the id belonging to the post
        junkclass -> classes inside text to get rid of
    
    Returns: text, [[postid,quote],...], [[postid,mention],...]
        text      -> the cleaned text
        postid    -> the id belonging to the post (see Parameters)
        quote     -> raw quote text as BeautifulSoup
        mention   -> player id of the mentioned player
        
    """
    rawquotes=[]
    rawmentions=[]
    for _ in range(len(testext.find_all(class_="bbCodeBlock bbCodeBlock--expandable bbCodeBlock--quote js-expandWatch"))):
        try: # filter out all quotes
            rawquotes.append(testext.find(class_="bbCodeBlock bbCodeBlock--expandable bbCodeBlock--quote js-expandWatch").extract())
        except(AttributeError):
            break
    for _ in range(len(testext.find_all(class_=junkclass))):
        try: # delete some classes
            testext.find(class_=junkclass).decompose()
        except:
            pass
    for mention_x in testext.find_all("a",class_="username"):
        try: # find mentions
            rawmentions.append(int(mention_x["data-user"][:mention_x["data-user"].index(",")]))
        except(KeyError):
            rawmentions.append(int(mention_x["data-user-id"]))
    try: # Replace last Smily with "." to keep it conform to the rules.
        testext.find_all(class_="smilie")[-1].insert_before(".")
    except(IndexError):
        pass
    outext=testext.get_text().replace("\u200b","").replace("\t"," ").replace("\r"," ").replace("\n"," ")
    outext=re.sub(r"\s\s+"," ",outext)
    try: 
        if outext[-1]==" ":
            outext=outext[:-1]
        if outext[0]==" ":
            outext=outext[1:]
    except(IndexError):
        pass
    return(outext,
          [[postid,str(rawquote)] for rawquote in rawquotes],
          [[postid,rawmention] for rawmention in rawmentions]) # save cleaned post text

def _get_from_user():
    the_thread=input("Which thread shall be analyzed? i.E.: wer-als-letztes-antwortet-kriegt-viel-mehr-als-nur-128-dias.8439\n: ")
    while(True):
        try: 
            first_page=int(input("What is the first page? (usually 1)\n: "))
            if first_page>0:
                break
        except(ValueError):
            pass
        print('Must be an integer number bigger than 0!\n')
    while(True):
        try:
            last_page=int(input("What is the last page? (bigger or equal to the first page)\n: "))
            if last_page>=first_page:
                break
        except(ValueError):
            pass
        print('Must be an integer number bigger than the one before!\n') 
    thread_url=f"https://unlimitedworld.de/threads/{the_thread}/"
    the_title=input("Please enter a title for these statistics.\n: ")
    return(thread_url,first_page,last_page,the_title)

def load_pages(thread_url,first_page,last_page,title=""):
    print(f"Start loading {last_page-first_page+1} page(s) from {thread_url}\nThis might take a while!")
    pages=[]
    for ii in range(first_page,last_page+2):
        pages.append(requests.get(f"{thread_url}page-{ii}").text) # load all pages
        if ii in range(first_page,last_page+1,int((last_page-first_page+10)/10)):
            print(f"    Now finished loading page {ii}.")
    print("Finished!\n")
    if title != "": title="".join([title,"-"])
    np.savetxt(
        f"./{title.replace(' ','_').replace('/','_')}offlinedata.txt.gz",
        [pages[ii].replace("\t"," ").replace("\n","line_delimiter_here_by_fscript ").replace("\r","line_delimiter_here_by_fscript ") for ii in range(len(pages))],
        delimiter="page_delimiter_here_by_fscript",fmt='%s')

def analyze_web_data(title="",deleted_player_ids=[0],append_posttypes=[]):
    if title != "": title="".join([title,"-"])
    posttypes=["message message--post js-post js-inlineModContainer", # normal post
           "message message-threadStarterPost message--post js-post js-inlineModContainer", # post from OP
           "message message-staffPost message--post js-post js-inlineModContainer" # post from Team
          ]
    for appendtype in append_posttypes:
        posttypes.append(appendtype)
    num_lines = sum(1 for _ in gzip.open(f"./{title.replace(' ','_').replace('/','_')}offlinedata.txt.gz", "rt"))
    print(f"Start analyzing {num_lines-1} pages of data. This may take a while!")
    future_post=0
    mentions=[]
    quotes=[]
    posts=[] # post_id, player_id, player_name, post_zeit, post_dauer, post_likes, post_quotes, post_quotings, post_text
    with gzip.open(f"./{title.replace(' ','_').replace('/','_')}offlinedata.txt.gz", "rt") as file:
        pages=1 #Load pages from save
        for line in file:
            soup=BeautifulSoup(line.replace("line_delimiter_here_by_fscript ","\n"), 'html.parser')
            if pages == num_lines:
                if binput("By default the script uses the first post on the last page (which is –if possible– one more than you entered), to calculate the lifetime of the last post in your range. Do you want to use the current time to calculate the lifetime of the last post instead?"):
                    future_post=dt.datetime.timestamp(dt.datetime.now())
                else:
                    future_post=int(soup.find_all(class_=posttypes)[0].find(class_="u-dt")['data-time'])
                    break
            for post in soup.find_all(class_=posttypes):
                out_post=[]
                out_post.append(int(str(post['data-content'])[5:])) # find id of post
                posttext,out_quotes,out_mentions=post_text_cleanup(post.find(class_="bbWrapper"),out_post[0]) # find post content
                out_post.append(int(post.find(class_="message-name").find(class_="username")['data-user-id'])) # find id of poster
                out_post.append(str(post.find(class_="message-name").find(class_="username").string)) # find name of poster
                out_post.append(int(post.find(class_="u-dt")['data-time'])) # find post time
                out_post.append(0) # post dauer later tbd
                out_post.append(postlikes(post.find(class_="reactionsBar-link"))) # find reactions
                out_post.append(0) # quotes soon
                out_post.append(0) # quotings later
                out_post.append(len(posttext.split())) # word_count
                out_post.append(rule_check(posttext, out_post[-1])) # post_valid
                #out_post.append(posttext)
                for ii in out_quotes:
                    quotes.append(ii)
                    out_post[7]+=1
                for ii in out_mentions:
                    mentions.append(ii)
                posts.append(tuple(out_post))
                #if out_post[0]==300205: print(f"uwmc.de/p{out_post[0]} Words: {out_post[-2]} Valid? {out_post[-1]} Text: {posttext}")
            if pages in range(1,num_lines+2,int((num_lines+10)/10)):
                print(f"    Now finished analyzing page {pages}.")
            pages+=1
            del soup,posttext,out_quotes,out_mentions,out_post
    print(f"Finished! Analyzed {len(posts)} posts.\n")
    column_datatypes=[
    ('post_id',"int32"),
    ('player_id', 'int32'), 
    ('player_name','U32'), 
    ('post_time','int32'), 
    ('post_lifetime','int32'), 
    ('post_likes','int8'), 
    ('post_quotes','int8'), 
    ('post_quotings','int8'),
    ('post_wordcount','int32'),
    ('post_valid',bool),
    #('post_text','U100000')
    ]
    posts=np.array(posts,dtype=column_datatypes)
    for id_ in deleted_player_ids:
        posts["player_id"][posts["player_id"]==id_]=0
    return(posts,quotes,mentions,future_post)

def setup_player_array(posts,deleted_player_ids):
    column_datatypes=[
        ('player_id', 'int32'), 
        ('player_name','U32'), 
        ('count_posts','int32'),  
        ('count_likes','int32'), 
        ('count_quotes','int32'), 
        ('count_quotings','int32'),
        ('count_mentions','int32'), 
        ('count_mentionings','int32'),
        ('count_words','int64'),
        ('count_valid','int32')]
    players=[]
    ### create players array with all player names and entry-slots
    for ii in range(len(posts)):
        tmp=[posts["player_id"][ii],posts["player_name"][ii]]
        for _ in range(len(column_datatypes)-2):
            tmp.append(0)
        players.append(tuple(tmp))
    players=np.array(players,dtype=column_datatypes)
    
    ### dealing with deleted players
    for id_ in deleted_player_ids:
        players["player_id"][players["player_id"]==id_]=0
    players["player_name"][players["player_id"]==0]='Gelöschte Mitglieder'
    
    ### counting posts
    players,cnt=np.unique(players,return_counts=True)
    players["count_posts"]=cnt
    print(f"Found {len(players)} different Players.\n")
    return(players)

def count_mentions(mentions,players,posts,deleted_player_ids):
    print(f"Start evaluating {len(mentions)} mentions. There might be mentioned players, that never contributed to this tread:")
    for ii in mentions:
        if ii[1] in deleted_player_ids:
            ii[1]=0
        players["count_mentions"][players["player_id"]==ii[1]]+=1
        # try:
        #     posts["player_id"][posts["post_id"]==ii[0]][0]
        # except:
        #     print(posts["player_id"][posts["post_id"]==ii[0]],ii)
        players["count_mentionings"][players["player_id"]==posts["player_id"][posts["post_id"]==ii[0]][0]]+=1
        if len(np.where(players["player_id"]==ii[1])[0])==0:
            print(f"    Unknown metioned player id {ii[1]} in post uwmc.de/p{str(ii[0])}")
    print(f"There were {sum(players['count_mentions'])} mentioned players identified.\nTotal mentions are: {sum(players['count_mentionings'])}\n")

def count_quotes(quotes,players,posts,deleted_player_ids):
    print(f"Start evaluating {len(quotes)} quotes. There might be quoted players, that never contributed to this tread:")
    for rawquotes in quotes:
        soup=BeautifulSoup(rawquotes[-1], 'html.parser').find(class_="bbCodeBlock bbCodeBlock--expandable bbCodeBlock--quote js-expandWatch")
        ### First the mentioning player
        players["count_quotings"][players["player_id"]==posts["player_id"][posts["post_id"]==rawquotes[0]][0]]+=1
        ### Now the mentioned player
        try: # find id of quoted post
            poid=int(str(soup['data-source'])[5:])
        except(ValueError):
            poid=0 # if no id is found
        try: #find the quoted player
            pid=int(str(soup['data-attributes'])[8:])
        except(ValueError):
            try: #try again but different
                pid=posts["player_id"][posts["post_id"]==poid][0]
            except:
                try: # try again with the name
                    pid=players["player_id"][players["player_name"]==soup['data-quote']][0]
                except: # give up
                    pid=0
        if pid in deleted_player_ids:
            pid=0
        players["count_quotes"][players["player_id"]==pid]+=1
        if len(np.where(players["player_id"]==pid)[0])==0:
            print(f"    Unknown Quoted player id {pid} in post uwmc.de/p{str(rawquotes[0])}")
        del soup
    print(f"There were {sum(players['count_quotes'])} quoted player posts identified.\nTotal quotes are: {sum(players['count_quotings'])}\n")

def count_likes(players,posts):
    for id_ in players["player_id"]:
        players["count_likes"][players["player_id"]==id_]=np.sum(posts["post_likes"][posts["player_id"]==id_])

def count_valids(players,posts):
    for id_ in players["player_id"]:
        players["count_valid"][players["player_id"]==id_]=np.sum(posts["post_valid"][posts["player_id"]==id_])
        
def count_words(players,posts):
    for id_ in players["player_id"]:
        players["count_words"][players["player_id"]==id_]=np.sum(posts["post_wordcount"][posts["player_id"]==id_])

def calc_post_lifetime(posts,next_time):
    posts["post_lifetime"]=np.append(np.subtract(posts["post_time"][1:],posts["post_time"][:-1]),next_time-posts["post_time"][-1])
    print(f"The average lifetime of a post is {dt.timedelta(np.mean(posts['post_lifetime'])/day_sec)}.")

def quantiles_answertime(lifetimes,quantiles=[0.5,0.75,0.8,0.9,0.95,0.99]):
    print("Quantiles: Time until X% posts was answered:")
    for qtile in quantiles:
        print(f"    {int(qtile*100)}% after {dt.timedelta(np.quantile(lifetimes,qtile)/day_sec)}")
    print("\n")
    
def fast_numbers(players,posts):
    print(f"Total posts:         {len(posts['post_id'])}")
    print(f"Total valid posts:   {np.sum(posts['post_valid'])} ({100*np.sum(posts['post_valid'])/len(posts['post_id'])}%)")
    print(f"Total time:          {dt.timedelta(days=0,seconds=int(np.sum(posts['post_lifetime'])))} ({len(posts['post_id'])/dt.timedelta(days=0,seconds=int(np.sum(posts['post_lifetime']))).days} time/post)")
    print(f"Total players:       {len(players['player_id'])} ({len(posts['post_id'])/len(players['player_id'])} posts/player)")
    print(f"Total likes:         {np.sum(posts['post_likes'])}")
    print(f"Total quotes:        {np.sum(posts['post_quotes'])} ({np.sum(posts['post_quotes'])/np.sum(posts['post_likes'])} quotes/like)")
    print(f"Total mentions:      {np.sum(players['count_mentions'])}")
    print(f"Total words:         {np.sum(posts['post_wordcount'])} ({np.sum(posts['post_wordcount'])/len(posts['post_id'])} words/post)")



def main():
    project_info=_get_from_user()
    old_PATH=os.getcwd()
    PATH=f"{os.getcwd()}/{project_info[3].replace(' ','_').replace('/','_')}"
    if not os.path.exists(PATH):
        os.makedirs(PATH)
    os.chdir(PATH)
    if os.path.isfile(f"./{project_info[3].replace(' ','_').replace('/','_')}-offlinedata.txt.gz" if project_info[3] != "" else "offlinedata.txt.gz"):
        if binput("\nThis folder already contains web data with that project name, which will be lost if you load new data. If you don't load new data, the statistics will run with the old data. Do you want to load new data?"):
            the_start_time=dt.datetime.now()
            load_pages(*project_info)
        else:
            print("Proceeding with old data.")
    else:
        the_start_time=dt.datetime.now()
        load_pages(*project_info)
    try: 
        print(f"+++ TIME since initializing: {dt.datetime.now()-the_start_time}\n")
    except(UnboundLocalError):
        the_start_time=dt.datetime.now()

    posts_array,quotes,mentions,future_post_time=analyze_web_data(project_info[-1],playerID_mask)
    print(f"+++ TIME since initializing: {dt.datetime.now()-the_start_time}\n")
    calc_post_lifetime(posts_array, future_post_time)
    quantiles_answertime(posts_array["post_lifetime"])
    try:
        print(f"Quantiles for 2023 with average lifetime {dt.timedelta(np.mean(posts_array['post_lifetime'][posts_array['post_time']>=date2code(2023)])/day_sec)}")
        quantiles_answertime(posts_array["post_lifetime"][posts_array["post_time"]>=date2code(2023)])
    except(ValueError):
        pass
    player_array=setup_player_array(posts_array, playerID_mask)
    count_mentions(mentions, player_array, posts_array, playerID_mask)
    count_quotes(quotes, player_array, posts_array, playerID_mask)
    del mentions,quotes
    count_likes(player_array, posts_array)
    count_valids(player_array, posts_array)
    count_words(player_array, posts_array)
    print(f"+++ TIME since initializing: {dt.datetime.now()-the_start_time}\n")
    
    
    player_array.sort(order="count_posts")
    lpl.top10_pie(player_array["player_name"], player_array["count_posts"], "Top 10 Spieler:")
    lpl.histograms(posts_array["post_time"])
    lpl.top10_histogram(player_array["player_name"][-1:-11:-1], posts_array["player_name"], posts_array["post_time"])
    
    player_array.sort(order="count_words")
    lpl.top10_pie(player_array["player_name"], player_array["count_words"], "Top 10 Vielscheiber (Anzahl Wörter):")
    lpl.histograms(posts_array["post_time"],posts_array["post_wordcount"],"Wörter")
    lpl.histograms(posts_array["post_time"],posts_array["post_wordcount"],var_name="Wörter pro Post",norm_values=np.ones(len(posts_array)))
    lpl.histograms(posts_array["post_time"],posts_array["post_likes"],var_name="Likes pro Post",norm_values=np.ones(len(posts_array)))
    lpl.histograms(posts_array["post_time"],np.where(posts_array["post_valid"],1,0),var_name="Anteil Gültiger Posts",norm_values=np.ones(len(posts_array)))
    
    lpl.time_decay_plots(posts_array["post_time"], posts_array["post_lifetime"])
    lpl.top10_by_year(posts_array["player_name"], posts_array["post_time"])
    lpl.top10_by_year(posts_array["player_name"], posts_array["post_time"],values=posts_array["post_wordcount"],var_name="Wörter")
    lpl.top10_by_year(posts_array["player_name"], posts_array["post_time"],values=posts_array["post_wordcount"],var_name="Wörter pro Post",norm_values=np.ones(len(posts_array)))
    lpl.top10_by_year(posts_array["player_name"], posts_array["post_time"],values=np.where(posts_array["post_valid"],1,0),var_name="Anteil gültiger Posts",norm_values=np.ones(len(posts_array)),min_posts_filter=6)
    lpl.top10_by_year(posts_array["player_name"], posts_array["post_time"],values=posts_array["post_quotings"],var_name="Zitate pro Like",norm_values=posts_array["post_likes"])
    lpl.top10_by_year(posts_array["player_name"], posts_array["post_time"],values=np.where(posts_array["post_valid"],0,1),var_name="Ungültige Posts")
    
    player_array.sort(order="count_posts")
    lpl.top10_histogram(player_array["player_name"][-1:-11:-1], posts_array["player_name"], posts_array["post_time"],values=posts_array["post_wordcount"],var_name="Wörter")
    lpl.top10_histogram(player_array["player_name"][-1:-11:-1], posts_array["player_name"], posts_array["post_time"],values=np.where(posts_array["post_valid"],0,1),var_name="Ungültige Posts")
    
    fast_numbers(player_array, posts_array)
    player_array.sort(order="count_posts")
    with open("top_table.txt", "w") as file:
        print(tabulate(player_array[::-1],["ID","Name","Posts","Likes","q","Q","m","M","Wörter","Val"]),file=file)
    print(f"+++ TIME since initializing: {dt.datetime.now()-the_start_time}\n")
    os.chdir(old_PATH)

    

if __name__=="__main__":
    # po,pl=main()
    # for pp in pl[-1:-11:-1]:
    #     print(f"{pp['player_name']} has {100*pp['count_valid']/pp['count_posts']:.2f}% valid posts")
    main()
