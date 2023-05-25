# ERA RINF chatbot

This simple chatbot answers natural languages data questions about the [ERA RINF](https://rinf.era.europa.eu/rinf/) public data. It uses the [OpenAI](https://openai.com/) GPT-3 davinci model together with the [ERA vocabulary](https://data-interop.era.europa.eu/era-vocabulary/) to generate a [SPARQL](https://www.w3.org/TR/rdf-sparql-query/). Then the bot launches the query on the [EU open SPARQL endpoint](https://linked.ec-dataplatform.eu/sparql) and returns the results.

Because the complete ontology is to big to send as prompt to GPT, the ontology is first reduced to the classes and properties that are actually in use by the public data.

## Demo environment

Due to billing restriction on the GPT API, there is no official publicly available demo environment. Please contact the author for more information if you are unable to setup your own environment.

## Deployment

### Local deployment

1. Install the required dependencies for your project (e.g. via `pip install -r requirements.txt`).
2. Rename .env-empty to .env and give a value to the empty variables
3. Run the Streamlit application with the command `streamlit run streamlit_app.py`.
4. Access the URL displayed in the console to use the Streamlit application.
5. Enter text into the application to generate and run SPARQL queries.

### Docker

1. Rename .env-empty to .env and give a value to the empty variables
2. Build the image `docker build -t era-rinf-chatbot .`
3. Run the image `docker run -it --env-file ./env -p 8501:8501 era-rinf-chatbot`
4. Access the URL displayed in the console to use the Streamlit application.
5. Enter text into the application to generate and run SPARQL queries.

## Usage tips

GPT doesn't always return the same answer. If at first (or second) the query doesn't succeed, try again.

## Possible improvements

Several actions are possible to improve this application:

In this code:

- Check the SPARQL query returned by GPT for syntax errors and retry if errors occur
- Improve the default prompt (prompt engineering)
- Check the SPARQL query for obvious errors (non existing classes or properties)
- Usability: allow editing of sparql query
- Speed up the initial loading by pregenerating the reduced ontology and cache it

In the ERA vocabulary and ontology handling:

- Add synonyms to classes and properties
- Add the concept schemes to the reduced ontology

In the AI model used to translate text to query:

- [Finetune the model](https://platform.openai.com/docs/guides/fine-tuning)
- Use GPT-4 models when they are available as API
