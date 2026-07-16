import requests
import zipfile
faers_links = [
    "https://fis.fda.gov/content/Exports/faers_xml_2025Q4.zip",
    "https://fis.fda.gov/content/Exports/faers_xml_2025q3.zip",
    "https://fis.fda.gov/content/Exports/faers_xml_2025q2.zip",
    "https://fis.fda.gov/content/Exports/faers_xml_2025q1.zip"
]

for url in faers_links:
    output_file = url.split('/')[-1]
    
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    with open(output_file, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    print(f"Download complete {output_file}")

    import zipfile
    
    zip_path = f"./{output_file}"
    target_folder = "XML/"

    with zipfile.ZipFile(zip_path, "r") as z:
        for member in z.namelist():
            if member.startswith(target_folder):
                if member.lower().endswith(".xml"):
                    z.extract(member, "./")

    