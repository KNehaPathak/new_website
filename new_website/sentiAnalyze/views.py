from django.shortcuts import render
from .models import Apipasswords
import tweepy
from tweepy import Stream, OAuthHandler
from tweepy.streaming import StreamListener
import sys
import json
import nltk
import string
from nltk.corpus import state_union , stopwords
from nltk.tokenize import PunktSentenceTokenizer
import aylien_news_api
from aylien_news_api.rest import ApiException
from pprint import pprint
import json
import re
from textblob import TextBlob
from django.http import HttpResponse


punctuation = list(string.punctuation)
stop = stopwords.words('english') + punctuation + ['rt', 'via']


tweets_filename = 'tweets_demo_100.txt'
final_entity_names = []
consumerKey = 'eaekfWDMm4U7izuXx75lKwx7x'
consumerSecret = 'rbcYHVtfxGpgEYOLJ3gkS3a5oeocJuTAMaQwuIMxQsKrC7XxQc'
accessToken =  '294593103-3Hhb1dEGDNKkKhKnv9zV4w5iuQpopRsBw9G106oA'
accessSecret =  'NGdFz93OfrmEd1NYV6bTrxpcDP4qdUhzQ7vM43z9IFIS5'
aylien_news_api.configuration.api_key['X-AYLIEN-NewsAPI-Application-ID'] = 'd5728285'
aylien_news_api.configuration.api_key['X-AYLIEN-NewsAPI-Application-Key'] = '85eacf2e44d6d789cbf48422819cec70'
max_tweets = 10

def extract_entity_names(t):
    entity_names = []

    if hasattr(t, 'label') and t.label:
        if t.label() == 'NE':

            final_entity_names.append(' '.join([child[0] for child in t]))

        else:
            for child in t:
                entity_names.extend(extract_entity_names(child))
    return entity_names


class FetchTweets(StreamListener):

    def __init__(self, api=None):
        self.num_tweets = 0
'''
    def on_data(self, data):
        with open('tweets_demo_100.txt', 'a') as tweet_file:
            tweet_file.write("kjkj")
        return True
'''

class TwitterClient(object):
    def __init__(self):
        consumerKey = 'eaekfWDMm4U7izuXx75lKwx7x'
        consumerSecret = 'rbcYHVtfxGpgEYOLJ3gkS3a5oeocJuTAMaQwuIMxQsKrC7XxQc'
        accessToken = '294593103-3Hhb1dEGDNKkKhKnv9zV4w5iuQpopRsBw9G106oA'
        accessSecret = 'NGdFz93OfrmEd1NYV6bTrxpcDP4qdUhzQ7vM43z9IFIS5'
        try:
            self.auth = OAuthHandler(consumerKey, consumerSecret)
            self.auth.set_access_token(accessToken, accessSecret)
            self.api = tweepy.API(self.auth)
        except:
            print("Error: Authentication Failed")

    def clean_tweet(self, tweet):
        return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t]) | (\w +:\ / \ / \S +)", " ", tweet).split())

    def get_tweet_sentiment(self, tweet):
        analysis = TextBlob(self.clean_tweet(tweet))
        if analysis.sentiment.polarity > 0:
            return 'positive'
        elif analysis.sentiment.polarity == 0:
            return 'neutral'
        else:
            return 'negative'

    def get_tweets(self, query, count=10):
        tweets = []
        try:
            fetched_tweets = self.api.search(q=query, count=count)
            for tweet in fetched_tweets:
                parsed_tweet = {}
                parsed_tweet['text'] = tweet.text
                parsed_tweet['sentiment'] = self.get_tweet_sentiment(tweet.text)
                if tweet.retweet_count > 0:
                    if parsed_tweet not in tweets:
                        tweets.append(parsed_tweet)
                else:
                    tweets.append(parsed_tweet)
            return tweets

        except tweepy.TweepError as e:
            print("Error : " + str(e))




def index(request):
    all_keys = Apipasswords.objects.all()
    #auth = OAuthHandler(consumerKey, consumerSecret)
    #auth.set_access_token(accessToken, accessSecret)
    #twitterStream = Stream(auth, FetchTweets())
    tweets = []
    for line in open(tweets_filename):
        try:
            tweets.append(json.loads(line))
        except:
            pass
    texts = ""
    for tweet in tweets:
        try:
            texts += tweet['text']
        except:
            pass
    tokenizedSentences = nltk.sent_tokenize(texts)
    data = []
    for sent in tokenizedSentences:
        data = data + nltk.pos_tag(nltk.word_tokenize(sent))

    entity_names = []
    namedEnt = nltk.ne_chunk(data, binary=True)

    for tree in namedEnt:
        entity_names.extend(extract_entity_names(tree))

    lowerFinalEntity = []
    for eachEntity in final_entity_names:
        lowerFinalEntity.append(eachEntity.lower())

    all_words = nltk.FreqDist(lowerFinalEntity)
    finalResult = all_words.most_common(5)
    api_instance = aylien_news_api.DefaultApi()
    f = open("new_queryKeywords2.txt", "w+")
    data_dict = {}
    i = 0
    for query_data in finalResult:
        try:
            data = query_data
            text = data
            language = ['en']
            since = 'NOW-10DAYS'
            until = 'NOW'
            api_response = api_instance.list_stories(text=text, language=language, published_at_start=since,
                                                     published_at_end=until)
            story = api_response.stories
            pnews = [data for data in story if data.sentiment.body.polarity == 'positive']
            nnews = [data for data in story if data.sentiment.body.polarity == 'negative']
            neutralnews = [data for data in story if data.sentiment.body.polarity == 'neutral']

            positive_news_sentiment = format(100 * len(pnews) / len(story))
            negetive_news_sentiment = format(100 * len(nnews) / len(story))
            neutral_news_sentiment = format(100 * len(neutralnews) / len(story))

            api = TwitterClient()
            tweets = api.get_tweets(query=data, count=200)
            ptweets = [tweet for tweet in tweets if tweet['sentiment'] == 'positive']
            ntweets = [tweet for tweet in tweets if tweet['sentiment'] == 'negative']
            neutraltweets = [tweet for tweet in tweets if tweet['sentiment'] == 'neutral']

            positive_twitter_sentiment = format(100 * len(ptweets) / len(tweets))
            negetive_twitter_sentiment = format(100 * len(ntweets) / len(tweets))
            neutral_twitter_sentiment = format(100 * len(neutraltweets) / len(tweets))

            data_dict[i] = {'query_val': query_data[0], 'positive_news_sentiment': positive_news_sentiment,
                            'negetive_news_sentiment':negetive_news_sentiment, 'neutral_news_sentiment':neutral_news_sentiment,
                            'positive_twitter_sentiment':positive_twitter_sentiment, 'negetive_twitter_sentiment':negetive_twitter_sentiment,
                            'neutral_twitter_sentiment':neutral_twitter_sentiment}
            i = i+1
        except:
            pass
    f.close()
    context = {
        'max_tweets': max_tweets,
        'tweets': tweets,
        'finalResult': finalResult,
        'data_dict': data_dict,
    }
    return render(request, 'sentiAnalyze/index.html', context)