import os
import re
import argparse


def extract_qa_commentary(content):

    # pattern = re.compile(
    #     r"Вопрос\s*\d*:\s*(.*?)\nОтвет:\s*(.*?)\nКомментарий:\s*(.*?)(?:\nИсточник|\Z)",
    #     re.DOTALL,
    # )

    pattern = re.compile(
        r"Вопрос\s*\d*:\s*(.*?)\nОтвет:\s*(.*?)(?:\nЗачет:\s*(.*?))?(?:\nКомментарий:\s*(.*?))?(?:\nИсточник|\Z)",
        re.DOTALL,
    )
    matches = pattern.findall(content)
    qa_commentary_list = []

    for match in matches:

        question = match[0].strip()
        answer = match[1].strip()
        secondary_answer = match[2].strip() if match[2] else None
        commentary = match[3].strip() if match[3] else None
        qa_commentary_list.append(
            (question, answer, secondary_answer, commentary))
    return qa_commentary_list


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", help="directory with questions")
    args = parser.parse_args()

    for filename in os.listdir(args.directory):
        file_path = os.path.join(args.directory, filename)
        with open(file_path, "r", encoding="koi8-r") as file:
            content = file.read()
            qas = extract_qa_commentary(content)
            for qqq in qas:
                q, a, secondary_a, commentary = qqq
                print(f"{q=}\n{a=}\n{secondary_a}\n{commentary=}")

        break


if __name__ == "__main__":
    main()
