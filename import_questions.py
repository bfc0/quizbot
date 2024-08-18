import os
import re
import json
import redis
import argparse


def extract_questions(content):

    pattern = re.compile(
        r"Вопрос\s*\d*:\s*(.*?)\nОтвет:\s*(.*?)(?:\nЗачет:\s*(.*?))?(?:\nКомментарий:\s*(.*?))?(?:\nИсточник|\Z)",
        re.DOTALL,
    )
    matches = pattern.findall(content)
    extracted_questions = []

    for match in matches:

        question = match[0].strip()
        answer = match[1].strip()
        secondary_answer = match[2].strip() if match[2] else None
        commentary = match[3].strip() if match[3] else None
        extracted_questions.append(
            (question, answer, secondary_answer, commentary))
    return extracted_questions


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", help="directory with questions")
    parser.add_argument("--limit", help="limit of files to process", default=1)
    args = parser.parse_args()
    limit = args.limit

    r = redis.Redis(host="localhost", port=6379, db=0)

    for filename in os.listdir(args.directory)[:limit]:
        file_path = os.path.join(args.directory, filename)
        with open(file_path, "r", encoding="koi8-r") as file:
            content = file.read().replace("\\n", "").replace("\n", "")
            questions = extract_questions(content)

            for item in questions:
                extracted_question, primary_answer, secondary_answer, explanation = item
                question = {
                    "question": extracted_question,
                    "primary_answer": primary_answer,
                    "secondary_answer": secondary_answer,
                    "explanation": explanation,
                }
                key = r.incr("question_id")
                r.set(f"question:{key}", json.dumps(question))


if __name__ == "__main__":
    main()
