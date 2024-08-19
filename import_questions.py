import os
import re
import json
import redis
import argparse


def extract_questions(content: str) -> list[dict[str, str | None]]:
    pattern = re.compile(
        r"Вопрос\s*\d*:\s*(.*?)\nОтвет:\s*(.*?)(?:\nЗачет:\s*(.*?))?(?:\nКомментарий:\s*(.*?))?(?:\nИсточник|\Z)",
        re.DOTALL,
    )
    matches = pattern.findall(content)
    extracted_questions = [
        {
            "question": match[0].strip().replace("\n", ""),
            "primary_answer": match[1].strip(),
            "secondary_answer": match[2].strip() if match[2] else None,
            "explanation": match[3].strip().replace("\n", "") if match[3] else None,
        } for match in matches
    ]

    return extracted_questions


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", help="directory with questions")
    parser.add_argument("--limit", help="limit of files to process", default=1)
    parser.add_argument("--host", help="redis host", default="localhost")
    parser.add_argument("--port", help="redis port", default=6379)
    args = parser.parse_args()
    limit = args.limit

    r = redis.Redis(host=args.host, port=args.port)

    for filename in os.listdir(args.directory)[:limit]:
        file_path = os.path.join(args.directory, filename)
        with open(file_path, "r", encoding="koi8-r") as file:
            content = file.read()
        questions = extract_questions(content)

        for question in questions:
            key = r.incr("question_id")
            r.set(f"question:{key}", json.dumps(question))


if __name__ == "__main__":
    main()
