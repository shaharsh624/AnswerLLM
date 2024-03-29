from langchain_google_genai import GoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import DataFrameLoader
from langchain_community.embeddings import HuggingFaceInstructEmbeddings
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import os
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

llm = GoogleGenerativeAI(model="gemini-pro", temperature=0.1)


def initialise():
    vectordb_file_path = "faiss_index"

    instructor_embeddings = HuggingFaceInstructEmbeddings(
        model_name="hkunlp/instructor-large"
    )

    return vectordb_file_path, instructor_embeddings


def create_vector_db(df):
    df = df

    # Load data from FAQ sheet
    loader = DataFrameLoader(df, page_content_column="prompt")
    data = loader.load()

    vectordb_file_path, instructor_embeddings = initialise()

    # Create a FAISS instance for vector database from 'data'
    vectordb = FAISS.from_documents(documents=data, embedding=instructor_embeddings)

    # Save vector database locally
    vectordb.save_local(vectordb_file_path)


def get_qa_chain():
    vectordb_file_path, instructor_embeddings = initialise()

    # Load the vector database from the local folder
    vectordb = FAISS.load_local(vectordb_file_path, instructor_embeddings)

    # Create a retriever for querying the vector database
    retriever = vectordb.as_retriever(score_threshold=0.7)

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
    # create_vector_db()
    chain = get_qa_chain()
    print(chain("Do you have javascript course?")["result"])
