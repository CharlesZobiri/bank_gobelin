import random
import string

def generate_iban():
    return ''.join(random.choices(string.digits, k=34))
