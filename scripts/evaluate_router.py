"""
Router Evaluation Script — Module A1.3
========================================
Evaluate fine-tuned Router accuracy and confusion matrix.
"""

import json
import torch
from loguru import logger
from tqdm import tqdm
from sklearn.metrics import classification_report, confusion_matrix
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_PATH = "models/router-qwen-1.5b-lora" # or base model for testing
TEST_DATA = "data/training/router/test_set.jsonl"

def evaluate():
    logger.info(f"Evaluating model at {MODEL_PATH}...")
    
    # Check if model exists, otherwise use base model for placeholder eval
    model_to_use = MODEL_PATH if os.path.exists(MODEL_PATH) else "Qwen/Qwen2.5-1.5B-Instruct"
    
    tokenizer = AutoTokenizer.from_pretrained(model_to_use)
    model = AutoModelForCausalLM.from_pretrained(
        model_to_use, 
        torch_dtype=torch.float16, 
        device_map="auto"
    )

    y_true = []
    y_pred = []

    with open(TEST_DATA, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    for line in tqdm(lines, desc="Evaluating"):
        data = json.loads(line)
        text = data["text"]
        label = data["intent"]

        # Prepare prompt
        prompt = f"<|im_start|>system\nPhân loại ý định vào: order, faq, consultant, ignore. Trả về JSON: {{\"action\": \"intent\"}}<|im_end|>\n"
        prompt += f"<|im_start|>user\n{text}<|im_end|>\n<|im_start|>assistant\n"
        
        inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
        with torch.no_grad():
            outputs = model.generate(**inputs, max_new_tokens=20, do_sample=False)
        
        response = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
        
        # Parse result
        try:
            pred_intent = json.loads(response).get("action", "ignore")
        except:
            # Fallback parsing
            pred_intent = "ignore"
            for m in ["order", "faq", "consultant", "ignore"]:
                if m in response.lower():
                    pred_intent = m
                    break
        
        y_true.append(label)
        y_pred.append(pred_intent)

    # Report
    print("\n" + "="*50)
    print("ROUTER EVALUATION REPORT")
    print("="*50)
    print(classification_report(y_true, y_pred))
    
    # Accuracy Check
    from sklearn.metrics import accuracy_score
    acc = accuracy_score(y_true, y_pred)
    if acc >= 0.92:
        logger.info(f"✅ PASSED: Accuracy = {acc:.2%}")
    else:
        logger.warning(f"❌ FAILED: Accuracy = {acc:.2%}. Need >= 92%")

if __name__ == "__main__":
    import os
    if not os.path.exists(TEST_DATA):
        logger.error(f"Test data not found at {TEST_DATA}")
    elif not torch.cuda.is_available():
        logger.error("GPU required for evaluation.")
    else:
        evaluate()
