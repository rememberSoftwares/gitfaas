from Help import *
from Config import PROMPT_VALUE

class Question:

    def __init__(self):
        pass

    def ask_boolean_question(self, question:str, help_id: str):
        while True:
            print(question)
            answer = input(PROMPT_VALUE)
            if answer.lower() == "y" or answer.lower() == "yes":
                return True
            elif answer.lower() == "n" or answer.lower() == "no":
                return False
            elif answer.lower() == "?":
                Help.show_help_for(help_id)
            print("Please answer 'y/yes', 'n/no' or '?' for help on this question")

    def ask_int_question(self, question:str, help_id: str):
        print(question)

        while True:
            answer = input(PROMPT_VALUE)
            if answer == "?":
                Help.show_help_for(help_id)
            elif answer.isdigit() is not True:
                print("Please answer a numeric value or '?' for help on this question")
            else:
                return int(answer)

    def ask_str_question(self, question: str, can_be_empty:bool, help_id: str, default: str = None):
        print(question)
        while True:
            answer = input(PROMPT_VALUE)
            if answer == "?":
                Help.show_help_for(help_id)
            elif can_be_empty is False and answer == "":
                print("Please answer something")
            elif can_be_empty is True and answer == "":
                return default
            else:
                return answer

    def ask_choice_question(self, question: str, available_answers:[], help_id: str):
        print(question)
        while True:
            answer = input(PROMPT_VALUE)
            if answer == "?":
                Help.show_help_for(help_id)
            elif answer.lower() in available_answers:
                return answer
            else:
                print(f"Please answer with one of the following answers {available_answers}")