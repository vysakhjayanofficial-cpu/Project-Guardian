from XML_Parser import faers_data_generator
from llm_util import generate_synthetic_review
from pathlib import Path
from test_case_gen import FAERS_Data_Maker

XML_file_path = Path("./datasets/faers_xml/XML/")


for item in XML_file_path.iterdir():
    print(item)
    if item.is_file() and item.suffix.lower() == ".xml":
        generator = faers_data_generator(item)
        FAERS_Data_Maker(generator)