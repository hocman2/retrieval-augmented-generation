import psycopg
import pandas as pd

EMBEDDING_FILE = "parsed_doc_embedded.csv"

DB_HOST="localhost"
DB_USER="postgres"
DB_PASSWORD="postgres"

if __name__ == "__main__":
    df = pd.read_csv(EMBEDDING_FILE, sep=";", index_col=0)

    with psycopg.connect(dbname="adonis_emb", user=DB_USER, password=DB_PASSWORD, host=DB_HOST) as conn:
        with conn.cursor() as cur:

            print("Running query ...")
            try:
                for _, row in df.iterrows():
                    cur.execute("INSERT INTO embeddings (href, breadcrumb, content, embeddings) VALUES (%s, %s, %s, %s)", (row["href"], row["breadcrumb"], row["text"], row["embedding"]))
    
                print("All good!")
            except Exception as e:
                print(e)
    