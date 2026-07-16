from unsloth import FastLanguageModel
import torch
import json

from datasets import Dataset
from pathlib import Path
max_seq_length = 2048
dtype = None
load_in_4bit = True


MODEL_PATH = "./models/"

model,tokenizer = FastLanguageModel.from_pretrained(
    model_name = MODEL_PATH,
    max_seq_length = max_seq_length,
    dtype = dtype,
    load_in_4bit = load_in_4bit
)

model  = FastLanguageModel.get_peft_model(model,
                                          r= 16,
                                          lora_alpha= 32,
                                          lora_dropout= 0.05,
                                          target_modules = ["q_proj", "k_proj", "v_proj", "o_proj","gate_proj","up_proj", "down_proj"],
                                          bias = "none",
                                          use_gradient_checkpointing = True,
                                          random_state = 1771,
                                          use_rslora = False,
                                          loftq_config = None
                                          )




prompt = """
Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction: You are a medical review assistant. You will be given a summary of a medical review and you need to provide JSON formmat output that includes the following information:
1 . "meddra_pt": the preferred term of the medical event
2. "meddra_soc": the system organ class of the medical event
3. "primary_event": the primary adverse event reported
4. "secondary_events": the secondary adverse events reported
5. "seriousness_assessment": the seriousness assessment of the medical event
6. "seriousness_rationale": the rationale for the seriousness assessment
7. "causality_assessment": the causality assessment of the medical event
8. "causality_rationale": the rationale for the causality assessment
9. "labeling_status": the labeling status of the medical event
10. "labeling_rationale": the rationale for the labeling status
11. "review_confidence_score": the confidence score of the review.

Rules:
- Return JSON only.
- Do not invent demographics.
- Do not invent dates.
- Do not invent laboratory values.
- If information is unavailable, explain uncertainty.


### Input: 
{}

### Response:

{}  
"""

EOS_TOKEN = tokenizer.eos_token

def formatting_function(json_obj):
    input_str = json_obj["review_summary"]
    output_str = f"""
    {{
        "meddra_pt": "{json_obj["meddra_pt"]}",
        "meddra_soc": "{json_obj["meddra_soc"]}",
        "primary_event": "{json_obj["primary_event"]}",
        "secondary_events": "{json_obj["secondary_events"]}",
        "seriousness_assessment": "{json_obj["seriousness_assessment"]}",
        "seriousness_rationale": "{json_obj["seriousness_rationale"]}",
        "causality_assessment": "{json_obj["causality_assessment"]}",
        "causality_rationale": "{json_obj["causality_rationale"]}",
        "labeling_status": "{json_obj["labeling_status"]}",
        "labeling_rationale": "{json_obj["labeling_rationale"]}",
        "review_confidence_score": "{json_obj["review_confidence_score"]}"
    }}

    """

    return input_str, output_str

json_path = Path("./datasets/FAERS_Generated_new/")


def data_generator(json_path):
    texts = []
    for json_file in json_path.glob("*.json"):
        with open(json_file, "r") as f:
            json_obj = json.load(f)
            input_str, output_str = formatting_function(json_obj)
            prompt_str = prompt.format(input_str, output_str) + EOS_TOKEN
            texts.append(prompt_str)
    return {"text": texts}

from datasets import Dataset
dataset = Dataset.from_dict(data_generator(json_path))
    


from trl import SFTTrainer, SFTConfig

trainer = SFTTrainer(
    model=model,
    train_dataset=dataset,
    dataset_text_field="text",
    max_seq_length=max_seq_length,
    packing=False,
    args=SFTConfig(
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
        warmup_steps=5,
        max_steps=60,
        learning_rate=2e-4,
        logging_steps=1,
        optim = "adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="linear",
        seed=1771,
        output_dir="./fine_models",
        report_to= "none"
    )
)

trainer.train()


prompt = """
Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction: You are a medical review assistant. You will be given a summary of a medical review and you need to provide JSON formmat output that includes the following information:
1 . "meddra_pt": the preferred term of the medical event
2. "meddra_soc": the system organ class of the medical event
3. "seriousness_assessment": the seriousness assessment of the medical event described in detail
4. "seriousness_rationale": the rationale for the seriousness assessment described in detail
5. "causality_assessment": the causality assessment of the medical event described in detail
6. "causality_rationale": the rationale for the causality assessment described in detail
7. "labeling_status": the labeling status of the medical event described in detail
8. "labeling_rationale": the rationale for the labeling status described in detail

### Input: 
{}

### Response:

{}  
"""

FastLanguageModel.for_inference(model) # Enable native 2x faster inference
inputs = tokenizer(
    text=[
        prompt.format(
            "A 47-year-old patient experienced constipation, which was classified as a serious adverse event. The patient was taking multiple medications, including VEDOLIZUMAB (Suspect Drug), TYLENOL (Secondary Suspect Drug), PENTASA (Secondary Suspect Drug), PREDNISONE (Secondary Suspect Drug), and CIPRO (Secondary Suspect Drug).",
            ""
        )
], return_tensors = "pt").to("cuda")

outputs = model.generate(**inputs, max_new_tokens = 512, use_cache = True)
print(tokenizer.batch_decode(outputs))

model.save_pretrained_merged(
    "qwen_merged",
    tokenizer,
    save_method="merged_16bit"
)