from llama_cpp import Llama

llm = Llama(
    model_path="./biomistral/ggml-model-Q4_K_M.gguf",
    n_ctx=4096,
    n_threads=8  # adjust
)

output = llm(
    "What are the symptoms of diabetes?",
    max_tokens=100
)

print(output["choices"][0]["text"])