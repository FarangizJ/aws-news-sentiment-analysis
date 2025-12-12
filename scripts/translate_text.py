import boto3
from utils import load_file, save_to_file, upload_to_s3

translate = boto3.client("translate")

def translate_uzbek():
    text = load_file("data/uzbek.txt")

    response = translate.translate_text(
        Text=text,
        SourceLanguageCode="uz",
        TargetLanguageCode="en"
    )

    translated = response["TranslatedText"]
    save_to_file("data/uzbek_translated.txt", translated)
    upload_to_s3("data/uzbek_translated.txt", "uzbek_translated.txt")
    print("Uzbek translated → English")

if __name__ == "__main__":
    translate_uzbek()
