import os

from langchain import PromptTemplate, OpenAI
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma

os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY")
os.environ["HUGGINGFACEHUB_API_TOKEN"] = os.environ.get("HUGGINGFACEHUB_API_TOKEN")

vectorstore_read = Chroma(embedding_function=HuggingFaceEmbeddings(),
                          persist_directory=os.environ.get("CHROMA_DB"))
retriever = vectorstore_read.as_retriever()


def get_answer(question: str):
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)

    # qa_chain = ConversationalRetrievalChain.from_llm(llm=llm, retriever=retriever, chain_type="stuff", verbose=True)
    # answer = qa_chain({"question": question, "chat_history": chat_history})["answer"]
    # chat_history.append((question, answer))

    """
    Retrieval produces different results with subtle changes in query wording using LLMs.
    """
    template = """Use the following pieces of context to answer the question at the end. 
        If you don't know the answer, just say that you don't know, don't try to make up an answer. 
        Use three sentences maximum and keep the answer as concise as possible. 
        Do not try to be polite, or say thank you or apologise. 
        {context}
        Question: {question}
        Helpful Answer:"""
    QA_CHAIN_PROMPT = PromptTemplate.from_template(template)

    qa = RetrievalQA.from_chain_type(
        llm=OpenAI(temperature=0),
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={"prompt": QA_CHAIN_PROMPT}
    )

    return qa.run(question)
