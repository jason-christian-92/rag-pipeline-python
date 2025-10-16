Demonstrating simple RAG Pipeline using Python.

* Parses all PDF documents inside a given folder folder and save it as embeddings
* Find relevant documents based on the given query
* Use local LLM to ask the AI about something based on the queried relevant documents

## Prerequisites

* Python 3.13 or higher
* Account in [supabase.com](https://supabase.com) to store vector data. Free tier is enough
* [Ollama](https://ollama.com) installed in your machine and is accessible

## Prep

Assuming you have cloned the project

1. Copy `.env.example` and rename it to `.env`
2. Create a table in your Supabase account with columns
  - document name (VARCHAR). This will store the document path. Set as primary key
  - page (INT). This will store the page number. Set as primary key
  - embedding (VECTOR). This will store the embedded data.
    - You might need to add the `pgvector` to your schema to enable vector data type
3. In order to be able to query by vector data, it's best to create a postgre function that can be called through the API
  - In your table view inside Supabase, select `SQL Editor`
  - Run this SQL
```lang=sql
DROP FUNCTION query_documents(vector);

CREATE OR REPLACE FUNCTION query_documents(query_embedding vector(1536))
returns TABLE (doc_name TEXT, page INT, similarity FLOAT)
language sql
as $$  
    select 
    d.doc_name AS doc_name,
    d.page AS page,
    1- (d.embedding <=> query_embedding) AS similarity
    from doc_embeddings d
    order by similarity desc
$$;
```
  - the column names have to match the columns in your table
  - You can now call `query_documents(vectordata)` through the supabase API
4. Replace the variables in .env with your own credentials
5. Create a folder and fill it with PDF documents you want to convert to vector data
6. Inside `prompts` folder, remove the `.example`-prefix so the script can load relevant prompts
  - you can also customize your own prompts
7. Install prerequisite libraries (`pip install -r requirements.txt`)

## How to use

```lang=bash
py rag-manager.py --action store --foldername <foldername>
```
Find all PDF files from the given foldername (inside project folder), extract the text, convert it to embeddings, and store it in the database.

```lang=bash
py rag-manager.py --action query --query <query-string>
```
Retrieve all documents that are related to the given query, sorted by relevancy

```lang=bash
py rag-manager.py --action ask --query <query-string>
```
Ask the LLM and get the answer.

## TODO

- [x] Refactor into classes
- [x] Completing the pipeline with LLM
- [ ] More file types to be converted
- [ ] More command line options (e.g. model choice, more actions)
- [ ] Refining search (similarity value, limiting the number of docs, better prompt)
- [ ] Testing other models
- [ ] Local postgresql database instead of online service