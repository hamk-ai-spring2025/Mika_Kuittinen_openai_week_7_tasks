import os
import streamlit as st
import requests
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
from langchain_core.runnables import RunnableSequence

# Load environment variables
load_dotenv()
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
#OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# OpenAI model
llm = ChatOpenAI(model="gpt-4", temperature=0.3, openai_api_key=OPENAI_API_KEY)

# Prompt template
prompt = PromptTemplate(
    input_variables=["articles"],
    template="""
Below is a list of news headlines with short summaries. Summarize the overall trends and main topics in a clear and concise English paragraph.

News List:
{articles}

Summary:
"""
)

# LangChain chain
chain = prompt | llm

# Streamlit UI
st.set_page_config(page_title="News Search (Serper)", page_icon="📰")
st.title("📰 News Search and Summary (via Serper.dev)")

# User inputs
query = st.text_input("🔍 Enter a news topic (e.g., AI, Ukraine):")
time_period = st.selectbox("🕒 Time period (for context only):", ["today", "past week", "past month"])

# Function to call Serper.dev API
def search_serper_news(query):
    url = "https://google.serper.dev/news"
    headers = {"X-API-KEY": SERPER_API_KEY}
    data = {"q": query}
    response = requests.post(url, headers=headers, json=data)
    return response.json()

if st.button("Search and summarize"):
    if not query:
        st.warning("Please enter a topic to search.")
    else:
        try:
            st.info("🔎 Searching news with Serper API...")
            result = search_serper_news(query)

            articles = ""
            for item in result.get("news", []):
                title = item.get("title", "")
                snippet = item.get("snippet", "")
                link = item.get("link", "")
                articles += f"- {title}: {snippet} (More: {link})\n"

            if not articles.strip():
                st.warning("No news found.")
            else:
                st.markdown("### 📰 Articles used:")
                st.text(articles.strip())

                st.success("✅ News fetched! Summarizing now...")
                summary = chain.invoke({"articles": articles})
                st.markdown("### 📝 Summary:")
                st.write(str(summary.content))

        except Exception as e:
            st.error(f"❌ Error: {e}")