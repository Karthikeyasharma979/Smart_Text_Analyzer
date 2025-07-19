from langchain_community.document_loaders.pdf import PyPDFDirectoryLoader
DATA_PATH = "./uploads"

def load_pdfs():
    loader = PyPDFDirectoryLoader(DATA_PATH)
    return loader.load()


