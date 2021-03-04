from starlette.applications import Starlette
from starlette.responses import UJSONResponse
from dotenv import load_dotenv
from newsapi import NewsApiClient
import json
import pprint
import uvicorn
import os
import gc
load_dotenv()
import requests
app = Starlette(debug=False)

import openai
openai.organization = os.getenv("OPNAI_ORG")
openai.api_key = os.getenv("KEY")

spacy_url = 'https://imoft-spacy-idvgffrwca-ez.a.run.app'

# Init
newsapi = NewsApiClient(api_key=os.getenv("NEWS"))
pprint.pprint("Hello pretty printer")

non_entities = ['EVENT', 'LAW', 'DATE', 'TIME', 'PERCENT', 'MONEY', 'QUANTITY', 'ORDINAL', 'CARDINAL']


# /v2/top-headlines
top_headlines = newsapi.get_top_headlines(language='en', sources="bbc-news,new-york-magazine,new-scientist, national-geographic" )
# pprint.pprint( newsapi.get_sources())
newsTexts = []
for article in top_headlines['articles']:
    newsTexts.append(article['title'] + "." + article['description'])


def generatePrompt(words):
    i=1
    output = "Words\n"

    for word in words:
        output += (str(i) + ". " + "\"" + word + "\"\n")
        i+=1
        if i==5:
            output += "\n Speculative Questions \n 1."
            return output
    
    return output

def parseOutput(output):
    print(output.split(str="\n", num=5))
    

# Needed to avoid cross-domain issues
response_header = {
    'Access-Control-Allow-Origin': '*'
}

generate_count = 0


@app.route('/', methods=['GET', 'POST', 'HEAD'])
async def homepage(request):
    words = []

    query = {'sections': newsTexts, 'sense2vec':False}
    jsonData = json.dumps(query)
    r = requests.post(spacy_url+'/ner', json=query)

    data = r.json()['data']

    namedEntities = []
    for obj in data:
        for ent in obj['entities']:
            
            if ent['label'] not in non_entities:
                
                if ent['text'] not in namedEntities and not any(map(str.isdigit, ent['text'])):
                    if len(ent['text'])< 30 and len(ent['text'])> 4:
                        namedEntities.append(ent['text'])


    output_qs = ''
    for i in range(0,3):

        prompt = generatePrompt(namedEntities[i*5: (i+1)*5])

        output = openai.Completion.create(
        engine="davinci",
        prompt="This is a speculative question generator.\nQuestion: \"What if taxes could be a prosperous choice ?\"\nWord: taxes\n###\nQuestion: \"What if Baghdad could be a cyberpunk utopia?\"\nWord: Baghdad\n###\nQuestion: \"What if Apple transformed the way we drive?\"\nWord: Apple\n###\nQuestion: \"What if UFOs could be a new form of meditation?\"\nWord: UFO\n###\nQuestion: \"What if Google could be a key player in world peace?\"\nWord: Google\n###\n\nWords:\n1. Taxes\n2. Baghdad\n3. Apple\n4. UFO\n5. Google\n\nSpeculative Questions\n1. \"What if Taxes could be a prosperous choice?\"\n2. \"What if Baghdad could be a cyberpunk utopia?\"\n3. \"What if Apple transformed the way we drive?\"\n4. \"What if UFOs could be a new form of meditation?\"\n5. \"What if Google could be a key player in world peace?\"\n\n###\n\n" + prompt,
        temperature=0.5,
        max_tokens=300,
        top_p=1,
        frequency_penalty=1,
        presence_penalty=0.75,
        stop=["\n\n"]
        )
        # pprint.pprint(output['choices'][0]['text'])
        output_qs += output['choices'][0]['text']
        
    query = {'text': output_qs}
    r = requests.post(spacy_url+'/sentencizer', json=query)


    output_sentences = []
    for sentence in r.json()['sentences']:
        if "What if" in sentence:
            pprint.pprint(sentence)
            output_sentences.append(sentence)

    gc.collect()
    return UJSONResponse({'sentences': output_sentences},
                         headers=response_header)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
