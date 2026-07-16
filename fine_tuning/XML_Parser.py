import xml.etree.ElementTree as ET
import pandas as pd

xml_file = "./datasets/faers_xml/1_ADR26Q1.xml"

df = pd.DataFrame(columns=["report_id", "received_date", "age", "drugs", "reactions"])

def dedup_list_of_dicts(lst):
    interim = list({frozenset(dict_val.items()) for dict_val in lst})
    return [dict(item) for item in interim]




drug_characterization_mapping = {
    "1": "Suspect Drug",
    "2": "Secondary Suspect Drug",
    "3": "Concomitant Drug",
    "4": "Interacting Drug"
}

reaction_outcome_mapping = {
    "1": "Recovered/Resolved",
    "2": "Recovering/Resolving",
    "3": "Not Recovered/Not Resolved",
    "4": "Recovered/Resolved with Sequelae",
    "5": "Fatal",
    "6": "Unknown"
}

def faers_data_generator(xml_file):
    for event, elem in ET.iterparse(xml_file, events=("end",)):
        serious_score = 0

        if elem.tag == "safetyreport":
            report = {
                "report_id": elem.findtext("safetyreportid"),
                "literature": elem.find("primarysource").findtext("literaturereference") if elem.find("primarysource") is not None else None,
                "serious": True if elem.findtext("serious") == "1" else False,
                "seriousnessdeath": True if elem.findtext("seriousnessdeath") == "1" else False,
                "seriousnesslifethreatening": True if elem.findtext("seriousnesslifethreatening") == "1" else False,
                "seriousnesshospitalization": True if elem.findtext("seriousnesshospitalization") == "1" else False,
                "seriousnessdisabling": True if elem.findtext("seriousnessdisabling") == "1" else False,
                "seriousnesscongenitalanomali": True if elem.findtext("seriousnesscongenitalanomali") == "1" else False,
                "seriousnessother": True if elem.findtext("seriousnessother") == "1" else False,
                "received_date": elem.findtext("receivedate"),

            }

            patient = elem.find("patient")

            if patient is not None:
                report["age"] = patient.findtext("patientonsetage")
                report["sex"] = patient.findtext("patientsex")
                report["weight"] = patient.findtext("patientweight")
                drugs = []

                for drug in patient.findall("drug"):
                    drug_name = drug.findtext("medicinalproduct")
                    active_substance = drug.find("activesubstance")
                    if active_substance is not None:
                        active_substance = active_substance.findtext("activesubstancename")

                    drug_characterization = drug.findtext("drugcharacterization")

                    drug_speficifics = {
                        "drug_name": drug_name,
                        "active_substance": active_substance,
                        "drug_characterization": drug_characterization_mapping[drug_characterization]
                    }
                    drugs.append(drug_speficifics)
                    
                reactions = []
                reaction_specifics = {}
                for reaction in patient.findall("reaction"):
                    reaction_name = reaction.findtext("reactionmeddrapt")
                    reaction_outcome = reaction.findtext("reactionoutcome")
                    reaction_specifics["reaction_name"] = reaction_name
                    if reaction_outcome in reaction_outcome_mapping:
                        reaction_specifics["outcome"] = reaction_outcome_mapping[reaction_outcome]
                    reactions.append(reaction_specifics)

                report["drugs"] = dedup_list_of_dicts(drugs)
                report["reactions"] = dedup_list_of_dicts(reactions)
            elem.clear()
            yield report

