import os

from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma

os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY")

vectorstore_read = Chroma(embedding_function=OpenAIEmbeddings(),
                          persist_directory="./chroma_db")
retriever = vectorstore_read.as_retriever()


def get_answer(query: str):
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
    qa_chain = RetrievalQA.from_chain_type(llm, retriever=retriever, chain_type="stuff", verbose=True)
    x = qa_chain({"query": query})
    return x['result']
