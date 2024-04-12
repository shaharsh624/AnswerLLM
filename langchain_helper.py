from langchain_google_genai import GoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

llm = GoogleGenerativeAI(model="gemini-pro", temperature=0.9)


def initialise():
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    return embeddings


# TODO: SAVE the csv file taken from Streamlit


def create_vector_db(project, file_name):

    file_path = os.path.join("data", project, file_name)

    file_name = file_name.replace(".csv", "") + "-faiss_index"
    vectordb_file_path = os.path.join("data", project, file_name)

    loader = CSVLoader(file_path=file_path)
    data = loader.load()

    embeddings = initialise()
    vectordb = FAISS.from_documents(documents=data, embedding=embeddings)
    vectordb.save_local(vectordb_file_path)


def get_qa_chain(project, file_name):
    file_name = file_name.replace(".csv", "") + "-faiss_index"
    vectordb_file_path = os.path.join("data", project, file_name)

    embeddings = initialise()
    vectordb = FAISS.load_local(
        vectordb_file_path, embeddings, allow_dangerous_deserialization=True
    )
    retriever = vectordb.as_retriever(score_threshold=0.3)

    prompt_template = """Given the following context and a question, generate an answer based on this context only.
    In the answer try to provide as much text as possible from "response" section in the source document context without making much changes.
    If the answer is not found in the context, kindly state "I don't know." Don't try to make up an answer.

    CONTEXT: {context}

    QUESTION: {question}"""

    PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )

    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        input_key="query",
        return_source_documents=True,
        chain_type_kwargs={"prompt": PROMPT},
    )

    return chain


if __name__ == "__main__":
    file_path = "codebasics_faqs.csv"
    # create_vector_db(file_path)
    chain = get_qa_chain()
