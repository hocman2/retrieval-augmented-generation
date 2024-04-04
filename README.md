# Simple RAG
This is a small RAG procedure that uses the [AdonisJS](https://adonisjs.com/) documentation as it's knowledge base.
It uses OpenAI's embedding-3-small and gpt-3.5-turbo but it could easily be swapped with other online models or local models if needed

The main goal is to have a LLM capable of using a knowledge base to answer questions and <u>always</u> provide a source in case the answer is insufficient or if the user needs double confirmation.

## Examples
```
"How do I read environment variables in adonisjs ?"

To read environment variables in AdonisJS, you can utilize the process.env object without any setup on the AdonisJS side. Additionally, you may use the AdonisJS env module for various benefits such as storing and parsing environment variables from multiple .env files, validating them upon application start, and ensuring static-type safety for the variables. The env module is initialized in the start/env.ts file and can be accessed throughout your AdonisJS application.
Sources:
https://docs.adonisjs.com/guides/environment-variables#using-the-adonisjs-env-module
https://docs.adonisjs.com/guides/environment-variables#environment-variables
```

```
"Can I use adonisjs with python ?"

No, AdonisJS is a JavaScript framework for Node.js and is not compatible with Python.
Sources:
https://docs.adonisjs.com/guides/introduction#what-is-adonisjs
```

```
"What are container services ?"

Container services are JavaScript modules that wrap container.make calls to allow for fetching objects using import statements instead. They act as a layer of indirection, enabling the use of a more unified syntax for importing and using modules, compared to a mix of import statements and container.make calls. Container services are utilized to resolve pre-configured objects within an application, commonly shipped with packages that interact with the container. They serve as an alternative to dependency injection, offering a way to request instances of classes from services within the container in a concise manner.
```

## Important disclaimer
The code in this repo is not meant to be used in production at all. 
There are probably a lot of security vulnerabilities and there is a lot of dirtiness (like exposing DB username and passwords directly in python files). 
Be aware that it is that way for simplicity or by incompetence and you should be concious of that when forking, reusing or cloning this repository 

## Querying the model
Before querying the model, you need to setup a PostgreSQL database either on localhost or online with the [pgvector](https://github.com/pgvector/pgvector) extension. If need be, change the constants at the top of *test_rag.py* to connect to your DB.
This repo comes with a SQL dump of the documentation as of April 2024 (version 6.something)

Once the DB is setup, simply run 
`python test_rag.py "{your query}"`

## Parsing the doc
This repo comes with all the tools needed to parse the documentation and populate the database from scratch.
To parse the whole doc simply run
`python parse_adonis_doc.py`
This will generate a *parsed_doc.csv* file which contains each section broken down into rows with the URL source and a breadcrumb pointer.
Tables are formated as lists of list to make it more comprehensible to the LLM that will ultimately have to read it.
**Disclaimer**: This script doesn't parse code blocks because I didn't implement it 🛌
**Disclaimer (2)**: This works as of April 2024 but changes to the website might break this script

### Generating embeddings from the doc
Once you've got your *parsed_doc.csv* file, you can simply follow the *generate_embeddings.ipynb* notebook to generate embeddings for each text content (I should've made it a python script for consistency).
The result is a `parsed_doc_embedded.csv` file

### Populating the database
Simply run
`python populate_db.py`

Again, you may change constants at the top of the file to suit your needs. It assumes there is a *adonis_emb* database with the following columns:
- id BIGSERIAL PRIMARY KEY
- href TEXT
- breadcrumb TEXT
- content TEXT
- embedding vector(1536) (you need the [pgvector](https://github.com/pgvector/pgvector) extension)

## Weaknesses and hallucinations
- The dataset generation itself assumes no paragraph will go over the 8191 token limit of text-embedding-3-small
- This model is not immune to hallucinations, it may sometimes say "I don't know." and still return valid sources
- The retrieval is a bit weak and will sometime fail to retrieve rows of interest. For example if you ask "What alternatives to lucid orm can I use ?" it will fail to return the row with URL "https://docs.adonisjs.com/guides/sql#other-popular-options". This might be fixed by using a more powerful embedding model or using algorithmic trickery to expand the retrieved context
- Since the dataset lacks any coding context, the LLM is ultimately limited in it's code generation.