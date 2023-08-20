import os

from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma

os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY")
vectorstore_read = Chroma(embedding_function=OpenAIEmbeddings(), persist_directory="./chroma_db")
retriever = vectorstore_read.as_retriever()


def get_answer(question: str, chat_history: list[str]):
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
    qa_chain = ConversationalRetrievalChain.from_llm(llm=llm, retriever=retriever, chain_type="stuff", verbose=True)
    answer = qa_chain({"question": question, "chat_history": chat_history})["answer"]
    chat_history.append((question, answer))
    return answer
