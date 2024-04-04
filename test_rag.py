from sys import argv
import openai
import psycopg

DB_HOST = "localhost"
DB_USER = "postgres"
DB_PASSWORD = "postgres"

def get_key() -> str:
    with open("openai_key.txt", "r") as f:
        return f.readline()

# get embeddings for the user prompt
def get_prompt_embeddings(user_prompt: str, model="text-embedding-3-small") -> list[float]:
    key = get_key()
    client = openai.OpenAI(api_key=key)
    return client.embeddings.create(input=user_prompt, model=model).data[0].embedding

# query db using cosine similarity
def get_closest_elements(num: int, emb: str) -> list:
    with psycopg.connect(dbname="adonis_emb", user=DB_USER, password=DB_PASSWORD, host=DB_HOST) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT (id, href, content, breadcrumb) FROM embeddings ORDER BY embedding <-> %(emb)s LIMIT %(num)s",
                        {"emb": emb, "num": num})
            return cur.fetchall()

# for debug, prints found elements
def present_elements(elements: list):
    for element in elements:
        element = element[0]
        print(f"""
Location: {element[1]}
{element[3]}

{element[2]}
""")

def query_gpt(user_prompt: str, elements: list, model="gpt-3.5-turbo") -> tuple[str, str]:
    context = ""
    for i, element in enumerate(elements):
        element = element[0]
        context += f"""
        (Index: {i+1})
        {element[2]}
        """

    key = get_key()
    client = openai.OpenAI(api_key=key)

    # initial messages
    messages = [
        {"role":"system", "content":f"""You are a senior developer with great knowledge. A junior asks you a question, formulate a new, comprehensible answer to the given prompt or instruction using only provided context.
         If the context doesn't permit to formulate an answer, say that you don't know.
         When asked to return a list of indices, execute the task with no further text
         Context:
         {context}"""},
        {"role": "user", "content": user_prompt}
    ]

    # get the model answer
    response = client.chat.completions.create(model=model, messages=messages)

    # ask for the source of the informations
    initial_response = response.choices[0].message.content
    messages.append({"role": "assistant", "content": initial_response})
    messages.append({"role": "user", "content": "Return a list in python format of the indices used from the context to formulate your previous answer"})
    response = client.chat.completions.create(model=model, messages=messages)

    return (initial_response, response.choices[0].message.content)

def get_sources_url(elements, sources) -> list[str]:
    sources = sources.strip('][').split(', ')
    links = []
    for source in sources:
        links.append(elements[int(source)-1][0][1]) #indices are 1 based, hence the -1

    return links

if __name__ == "__main__":
    user_prompt = argv[1]
    embeddings = get_prompt_embeddings(user_prompt)
    elements = get_closest_elements(3, str(embeddings))
    response, sources = query_gpt(user_prompt, elements)
    sources = get_sources_url(elements, sources)

    print(response)
    print("Sources: ")
    [print(x) for x in sources]