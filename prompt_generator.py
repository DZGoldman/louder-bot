
import random

def generate_prompt():
    word_array = []

    with open('prompt_bank.txt', 'r') as file:
        for line in file:
            word = line.strip()
            if word:
                word_array.append(word)
    # TODO
    base_prompt= "TODO"
    prompt = base_prompt
    count = random.randint(1, 3)
    for _ in range(random.randint(1, 3)):
        new_word = word_array.pop(random.randint(0, len(word_array) - 1))
        prompt = f"{prompt},{new_word}"
    return prompt
print(generate_prompt())