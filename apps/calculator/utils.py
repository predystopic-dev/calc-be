# import torch
# from transformers import pipeline, BitsAndBytesConfig, AutoProcessor, LlavaForConditionalGeneration
# from PIL import Image

# # quantization_config = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16)
# quantization_config = BitsAndBytesConfig(
#     load_in_4bit=True,
#     bnb_4bit_compute_dtype=torch.float16
# )


# model_id = "llava-hf/llava-1.5-7b-hf"
# processor = AutoProcessor.from_pretrained(model_id)
# model = LlavaForConditionalGeneration.from_pretrained(model_id, quantization_config=quantization_config, device_map="auto")
# # pipe = pipeline("image-to-text", model=model_id, model_kwargs={"quantization_config": quantization_config})

# def analyze_image(image: Image):
#     prompt = "USER: <image>\nAnalyze the equation or expression in this image, and return answer in format: {expr: given equation in LaTeX format, result: calculated answer}"

#     inputs = processor(prompt, images=[image], padding=True, return_tensors="pt").to("cuda")
#     for k, v in inputs.items():
#         print(k,v.shape)

#     output = model.generate(**inputs, max_new_tokens=20)
#     generated_text = processor.batch_decode(output, skip_special_tokens=True)
#     for text in generated_text:
#         print(text.split("ASSISTANT:")[-1])

import google.generativeai as genai
import logging
import ast
import json
from PIL import Image
from constants import GEMINI_API_KEY

logger = logging.getLogger(__name__)
logger.addHandler(logging.FileHandler('logs.log'))
genai.configure(api_key=GEMINI_API_KEY)

def analyze_image(img: Image, dict_of_vars: dict):
    model = genai.GenerativeModel(model_name="gemini-1.5-flash")
    dict_of_vars_str = json.dumps(dict_of_vars, ensure_ascii=False)
    prompt = (
        f"YOU CAN HAVE THREE TYPES OF EQUATIONS/EXPRESSIONS IN THIS IMAGE, AND ONLY ONE CASE SHALL APPLY EVERY TIME: "
        f"1. Simple mathematical expressions like 2+2, 3*4, 5/6, 7-8 etc. : This case, need to solve and return the answer in format as LIST OF ONE DICT [{{expr: given expression, result: calculated answer}}]"
        f"2. Set of Equations like x^2 + 2x + 1 = 0, 3y + 4x = 0, 5x^2 + 6y + 7 = 12 etc. : This case, need to solve for given variable, and format should be COMMA SEPARATED LIST OF DICTS, dict 1 as {{expr: x, result: 2, assign: True}}, and dict 2 as {{expr: y, result: 5, assign: True}} This example is assuming x was calculated as 2, and y as 5. Have as many dicts as vars"
        f"3. Assigning values to variables like x = 4, y = 5, z = 6 etc. : This case, you need to assign values to variables and return another key in dict called {{assign: True}}, and keep variable as expr and value as result in original dictionary. RETURN AS LIST OF DICTS"
        f"4. Analyzing Graphical Math problems, like word problems represented in graphical form, for eg, cars colliding, trigonometric problem, pythagoras theorem problems etc., and return the answer in format as LIST OF ONE DICT [{{expr: given expression, result: calculated answer}}]"
        f"Analyze the equation or expression in this image and return the answer acccording to given rules: "
        f"make sure to use extra backslashes for escape characters like \\f->\\\\f, \\n->\\\\n etc. "
        f"Here is a dictionary of user assigned variables, if given expression has any of these variables, "
        f"use its actual value from this dictionary accordingly: {dict_of_vars_str}. "
        f"DO NOT USE BACKTICKS OR MARKDOWN FORMATTING"
        f"PROPERLY QUOTE THE KEYS AND VALUES IN THE DICTIONARY FOR EASIER PARSING WITH python's ast.literal_eval"
    )
    response = model.generate_content([prompt, img])
    logging.info(f"Response from Gemini API: {response}\n")
    print(response.text)
    answers = []
    try:
        answers = ast.literal_eval(response.text)
    except Exception as e:
        logging.error(f"Error in parsing response from Gemini API: {e}")
        print(f"Error in parsing response from Gemini API: {e}")
    print('returned answer ', answers)
    for answer in answers:
        if 'assign' in answer:
            answer['assign'] = True
        else:
            answer['assign'] = False
    return answers