# coding: UTF-8
from __future__ import print_function

import boto3,os
import json,logging,re
import http.client, urllib.parse


# Replace the subscriptionKey string value with your valid subscription key.
subscriptionKey = os.environ.get('AZURE_KEY')

host = "api.cognitive.microsoft.com"
path = "/bing/v7.0/news/search"

logger = logging.getLogger()
logger.setLevel(logging.INFO)

#Region指定しないと、デフォルトのUSリージョンが使われる
clientLambda = boto3.client('lambda', region_name='ap-northeast-1')

logger.info('Loading function')

def lambda_handler(event, context):
    
    # このサービスが動作するか決定する。動作条件は、「ニュース」という単語が含まれているかどうか。
    lineText = event["lineMessage"]["events"][0]["message"]["text"]
    logger.info(lineText)
    if "ニュース" not in lineText :
        return None

    # どの単語でニュース検索をかけに行くか。パターンは2つ。「○○のニュース」の場合、〇〇を取得
    if "のニュース" in lineText :
        searchText = lineText.split("のニュース")[0]
        #↑のロジックは、「のニュース」で単語をSplitして0番目=最初に出てきた単語を使う
    else :  # 「○○ニュースのパターンを想定
        searchText = lineText.split("ニュース")[0]
    
    
    logger.info(searchText)
    
    # BingNewsを取得する
    headers, result = BingNewsSearch(searchText)
    logger.info(json.dumps(json.loads(result), indent=4, ensure_ascii=False))
    
    latestNews = json.loads(result)["value"]
    resNewsText = ""
    for i in range(len(latestNews)) :
        resNewsText += latestNews[i]["description"] + "\n"
        resNewsText += latestNews[i]["url"] + "\n"
        # 最大出力件数は3件まで
        if i >= 2 :
            break

    logger.info(resNewsText)
    
    #取得したNewsを返す
    return { "message" : resNewsText }
    

# BingNewsSearchからNewsを検索して取得する この部分はリファレンスほぼそのまま
def BingNewsSearch(search):
    "Performs a Bing News search and returns the results."

    headers = {'Ocp-Apim-Subscription-Key': subscriptionKey}
    conn = http.client.HTTPSConnection(host)
    query = urllib.parse.quote(search)
    conn.request("GET", path + "?q=" + query + "&mkt=ja-JP", headers=headers)
    response = conn.getresponse()
    headers = [k + ": " + v for (k, v) in response.getheaders()
                   if k.startswith("BingAPIs-") or k.startswith("X-MSEdge-")]
    return headers, response.read().decode("utf8")
