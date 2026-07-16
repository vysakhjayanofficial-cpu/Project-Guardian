
from XML_Parser import faers_data_generator
from llm_util import generate_synthetic_review
# xml_file = "./datasets/faers_xml/XML/3_ADR26Q1.xml"
# generator = faers_data_generator(xml_file)
import json

reaction_score_mapping = {
    "Recovered/Resolved": 1,
    "Recovering/Resolving": 2,
    "Not Recovered/Not Resolved": 3,
    "Recovered/Resolved with Sequelae": 4,
    "Fatal": 5,
    "Unknown": 0
}
def score_case(case):
    score = 0

    # Seriousness
    if case["serious"]:
        score += 3

    # Literature cases are usually higher quality
    if case["literature"]:
        score += 2

    # Number of unique suspect drugs
    suspect_drugs = [
        d for d in case["drugs"]
        if d["drug_characterization"] == "Suspect Drug"
    ]

    score += min(len(suspect_drugs), 3)

    # Reaction outcomes
    for reaction in case["reactions"]:
        score += reaction_score_mapping.get(
            reaction["outcome"], 0
        )

    return score


def FAERS_Data_Maker(generator):
    count = 0
    for element in generator:
        try:
            print("" * 40)
            # element = next(generator)
            score = score_case(element)
            if score >= 6:
                count+=1
                print(f"High-quality Case {count} {element['report_id']} (Score: {score}):")
                generated_review = generate_synthetic_review(element)
                with open(f"./datasets/FAERS_Generated_new/{element['report_id']}_review.json", "w") as f:
                    json.dump(generated_review, f, indent=2)
        except Exception as e:
            print(e)
            print("Skipping Test Case")


if __name__ == "__main__":
    
    xml_file = "./datasets/faers_xml/XML/2_ADR25Q2.xml"
    generator = faers_data_generator(xml_file)
    FAERS_Data_Maker(generator)