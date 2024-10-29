
import random

def generate_prompt():
    word_array = []

    with open('prompt_bank.txt', 'r') as file:
        for line in file:
            words = line.split(",")
            for word in words:
                if word.strip():
                    word_array.append(word.strip())
    base_prompt= "CRYPTO,MEME,HYPERPOP,INTERNET,YOUTHFUL,2024"
    count = random.randint(1, 3)
    prompt=""
    for _ in range(random.randint(1, 3)):
        new_word = word_array.pop(random.randint(0, len(word_array) - 1))
        prompt = f"{prompt},{new_word}"
    return base_prompt + prompt
if __name__ == "__main__":
    print("random prompt:")
    print(generate_prompt())