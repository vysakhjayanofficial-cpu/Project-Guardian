from server import search_articles, download_article, download_articles_batch, get_article_summaries
from llm import llm




articles = search_articles("Alzheimer's Disease")
print(articles)
# print(search_articles("COVID-19"))
content = download_article(articles['pmids'][0],format_type='abstract',return_mode='text')
# print(content)
# print(get_article_summaries(articles['pmids']))
# print(download_article(articles['pmids'][1]))


result = llm.invoke(f"Summarize the following: {content}")

print(result.content)