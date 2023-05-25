import os
import openai
import pandas as pd 
from SPARQLWrapper import SPARQLWrapper, JSON
import rdflib
from rdflib import Graph, ConjunctiveGraph, URIRef
from rdflib.namespace import RDF, RDFS
import streamlit as st

openai.api_key = os.getenv('OPENAI_API_KEY')
openai.api_type = os.getenv('OPENAI_API_TYPE')
openai.api_version = os.getenv('OPENAI_API_VERSION')
openai.api_base = os.getenv('OPENAI_API_BASE')

print(f"openai.api_base={openai.api_base}")

EndPoint_Models={
    "/v1/completions":["text-davinci-003", "text-davinci-002", "text-curie-001",
                        "text-babbage-001", "text-ada-001"],
    "/v1/chat/completions":["gpt-4", "gpt-4-0314", "gpt-4-32k", "gpt-4-32k-0314", "gpt-3.5-turbo", "gpt-3.5-turbo-0301"],
}
def API_SelectModel(model):
    for endPoint in EndPoint_Models:
        if model in EndPoint_Models[endPoint]:
            return endPoint
    return None

# openai.error.APIConnectionError: Error communicating with OpenAI: Invalid URL '/chat/completions': No scheme supplied. Perhaps you meant https:///chat/completions?
# https://api.openai.com/v1/models ?
# See: https://platform.openai.com/docs/models/model-endpoint-compatibility

def DG_simple_AI_test1():
    # https://medium.com/geekculture/a-simple-guide-to-chatgpt-api-with-python-c147985ae28
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": "Tell the world about the ChatGPT API in the style of a pirate."}
        ]
    )
    print(completion.choices[0].message.content)

def DG_simple_AI_test2():
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Who won the world series in 2020?"},
                {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
                {"role": "user", "content": "Where was it played?"}
            ]
        )
    print(completion['choices'][0]['message'])
    print(completion.choices[0].message.content)

# DG_simple_AI_test2()

st.cache(ttl=None)
def create_reduced_ontology():
    sparql_query_classes = "select distinct ?class FROM <http://data.europa.eu/949/graph/rinf> where { ?subj a ?class . }"
    sparql_query_properties = "select distinct ?pred FROM <http://data.europa.eu/949/graph/rinf> where { ?subj ?pred ?obj . }"
    
    res1 = execute_sparql_query(os.getenv('SPARQL_ENDPOINT'), sparql_query_classes)
    res2 = execute_sparql_query(os.getenv('SPARQL_ENDPOINT'), sparql_query_properties)
    
    relevant_classes = []
    for item in res1["results"]["bindings"]:
        v = item.get("class", {}).get("value", "")
        relevant_classes.append(v)
    
    relevant_properties = []
    for item in res2["results"]["bindings"]:
        v = item.get("pred", {}).get("value", "")
        relevant_properties.append(v)

    # Load the original ontology
    g = Graph()
    g.parse(os.getenv('ONTOLOGY_TTL'))

    # Create a new graph for the reduced ontology
    g_reduced = Graph()

    # Copy over the relevant classes and properties
    for cls in relevant_classes:
        g_reduced += g.triples((URIRef(cls), None, None))
    for prop in relevant_properties:
        g_reduced += g.triples((None, prop, None))

    # Copy over any additional triples that involve the relevant items
    for s, p, o in g:
        if s in relevant_classes or p in relevant_properties or o in relevant_classes:
            g_reduced.add((s, p, o))

    # Save the reduced ontology
    #print("Save the reduced ontology")
    #g_reduced.serialize('reduced_ontology.owl', format='turtle')
    return g_reduced

st.cache(ttl=None)
def load_ontologies():
    cg = ConjunctiveGraph()
    
    cg.parse("reduced_ontology.owl")

    return cg

st.cache(ttl=None)
def extract_ontology_information(graph):
    classes = set()
    properties = set()
    instances = set()

    for s, p, o in graph:
        if p == rdflib.RDF.type and o != rdflib.RDFS.Class:
            classes.add(str(o))
            instances.add(str(s))
        else:
            properties.add(str(p))

    return {
        "classes": list(classes),
        "properties": list(properties),
        "instances": list(instances),
    }

def generate_sparql_query(user_text, ontology_information):
    ontology_info_text = "\n".join(
        f"{key}: {', '.join(values)}"
        for key, values in ontology_information.items()
    )

    data_properties_text = ", ".join(ontology_information["properties"])

    prompt = (
        f"Ontology information:\n{ontology_info_text}\n\n"
        f"Data properties: {data_properties_text}\n\n"
        f"Generate a SPARQL query, not using prefixes, based on the following text: '{user_text}'"
    )

    prefixes = {
        "owl":"http://www.w3.org/2002/07/owl#", 
        "dc":"http://purl.org/dc/terms/",
        "dcelts":"http://purl.org/dc/elements/1.1/",
        "rdfs":"http://www.w3.org/2000/01/rdf-schema#", 
        "eu":"http://data.europa.eu/949/",
        "geo":"http://www.w3.org/2003/01/geo/wgs84_pos#", 
        "skos":"http://www.w3.org/2004/02/skos/core#", 
    }
    if "USE NAMESPACE PREFIX" in user_text:
        prompt=prompt.replace("not using prefixes","using prefixes")
        prompt=prompt.replace("USE NAMESPACE PREFIX"," ")
        for pref,url in prefixes.items():
            prompt = prompt.replace(url,pref+":")
        prefStr = "\n".join([f"PREFIX {pref}: <{url}>" for pref,url in prefixes.items()])
        prompt = prompt.replace("Ontology information:",f"Ontology information:\n{prefStr}\n\n")

    print(prompt)

    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=200,
        n=1,
        stop=None,
        temperature=0.5,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        best_of=1
    )

    
    generated_query = response.choices[0].text.strip()
    # generated_query = prefStr+ "\n\n" + generated_query
    print(generated_query)

    return generated_query, prompt

def execute_sparql_query(endpoint_url, query):
    sparql = SPARQLWrapper(endpoint_url)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    result = sparql.query().convert()

    return result

def json_result_to_dataframe(json_result):
    cols = json_result["head"]["vars"]
    data = [
        {key: value["value"] for key, value in row.items()}
        for row in json_result["results"]["bindings"]
    ]
    df = pd.DataFrame(data, columns=cols)
    return df