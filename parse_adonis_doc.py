import bs4
import requests
import re
import pandas as pd

def get_section_name(heading: bs4.Tag | bs4.NavigableString) -> str:
    last_content = heading.contents[len(heading.contents)-1]

    return last_content.text if last_content.text else last_content

def update_header_stack(stack: list[(str, str)], node: bs4.Tag) -> str:
    while(len(stack) > 0 and stack[len(stack)-1][0] >= node.name):
        stack.pop()

    stack.append((node.name, get_section_name(node)))

    a = node.find("a")
    return a.get("href") if a else ""

def headings_as_breadcrumb(stack: list[(str, str)]) -> str:
    return " > ".join([x[1] for x in stack])

def format_p(p: bs4.Tag) -> tuple[str, bs4.Tag]:
    text_content = ""
    node = p
    while True:
        text_content += node.text + "\r\n"

        next = node.find_next_sibling()

        if next == None or next.name != "p":
            return (text_content, next)
        else: node = next

def format_ul(ul: bs4.Tag) -> tuple[str, bs4.Tag]:
    text_content = ""
    lis = ul.find_all("li")
    for li in lis:
        text_content += f"- {li.text.strip().replace("Copy code to clipboard", "")}\r\n"

    return (text_content, ul.find_next_sibling())

def format_table(div: bs4.Tag) -> tuple[str, bs4.Tag]:
    text_content = ""
    table = div.find("table")

    table_rows = [elem for elem in table.find_all("tr") if elem.name != None]

    has_header = table.find("thead")
    # thats ugly af but there is a table that has no thead element yet still has a header
    if has_header or len([x for x in table_rows[0].children if x.name != None]) > 2:
        headers = []
        header_cols = table_rows[0]
        for col in header_cols:
            # somehow some children are empty
            if (col.name == None): continue
            text = col.text.strip()
            headers.append(text)

        for i, row in enumerate(table_rows[1:]):
            text_content += f"{i+1}.\r\n"
            # filter out empty children here too
            for i, col in enumerate([elem for elem in row.children if elem.name != None]):
                text = col.text.strip()
                text = text.replace("Copy code to clipboard", "")
                text_content += f"\t· {headers[i]}: {text}\r\n"

    #a edge case when the table has no header and only two cols
    else:
        table_rows = table.find("tbody").find_all("tr")
        for row in table_rows:
            children = [elem for elem in row.children if elem.name != None]
            assert(len(children) == 2)
            text = children[1].text.strip()
            text = text.replace("Copy code to clipboard", "")
            text_content += f"- {children[0].text.strip()}: {text}\r\n"

    return (text_content, div.find_next_sibling())

def add_to_content(page_content: list[ tuple[ tuple[str, str], str ] ], header_stack: list[str], link: str, content: str):
    page_content.append( ( (headings_as_breadcrumb(header_stack), link),  content ) )

def retrieve_text(first_node: bs4.Tag, url: str) -> list[ tuple[ tuple[str, str], str ] ]:
    page_content = []

    header_stack = []
    current_location = ""
    text_content = ""

    node = first_node
    while True:
        #is heading
        if (re.match("h[0-9]", node.name)):
            if len(text_content):
                add_to_content(page_content, header_stack, f"{url}{current_location}", text_content)
                text_content = ""
            current_location = update_header_stack(header_stack, node)
            node = node.find_next_sibling()
        elif (node.name == "p"):
            new_text, next = format_p(node)
            text_content += new_text
            node = next
        elif (node.name == "ul"):
            new_text, next = format_ul(node)
            text_content += new_text
            node = next
        elif (node.name == "div" and node.find("table")):
            new_text, next = format_table(node)
            text_content += new_text
            node = next
        else:
            node = node.find_next_sibling()

        if (node == None):
            return page_content
        
def get_all_links(html: bs4.BeautifulSoup) -> list[str]:
    nav = html.find("div", {"class": "docs_sidebar_container"}).find("nav")
    links = nav.find("ul").find_all("a")
    return [link.get("href") for link in links]

def get_content(html: bs4.BeautifulSoup) -> bs4.Tag | bs4.NavigableString:
    return html.find("article", {"class":"markdown"}).contents[1]

def make_df(texts: list[ tuple[ tuple[str, str], str ] ]):
    data = {"breadcrumb": [], "href": [], "text": []}

    for text in texts:
        data["breadcrumb"].append(text[0][0])
        data["href"].append(text[0][1])
        data["text"].append(text[1])

    return pd.DataFrame.from_dict(data)

root_url = "https://docs.adonisjs.com"
start_url = f"{root_url}/guides/introduction"

if __name__ == "__main__":
    result = requests.get(start_url)
    soup = bs4.BeautifulSoup(result.content, "html.parser")
    links = get_all_links(soup)

    texts = []
    try:
        for i, link in enumerate(links):
            parse_url = f"{root_url}{link}"
            print(f"{i+1}/{len(links)} Parsing {parse_url}")
            result = requests.get(parse_url)
            soup = bs4.BeautifulSoup(result.content, "html.parser")
            content = get_content(soup)

            if not isinstance(content, bs4.Tag):
                raise Exception(f"{content} is not a bs4.Tag!")
            
            text = retrieve_text(content, parse_url)
            texts.extend(text)
    except Exception as e:
        print(e)

    df = make_df(texts)
    df.to_csv("parsed_doc.csv", sep=";", index=False)
