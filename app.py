import os
from google.cloud import storage
import vertexai
from vertexai.generative_models import GenerativeModel

PROJECT_ID = os.environ["GCP_PROJECT_ID"]
LOCATION = os.getenv("GCP_LOCATION", "us-central1")
BUCKET_NAME = os.environ["GCS_BUCKET_NAME"]
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def validate_storage():
    print("[Storage] Validando acesso ao bucket...")
    client = storage.Client(project=PROJECT_ID)

    blobs = client.list_blobs(BUCKET_NAME, max_results=5)
    print(f"[Storage] Objetos encontrados em gs://{BUCKET_NAME}:")

    found = False
    for blob in blobs:
        found = True
        print(f"- {blob.name}")

    if not found:
        print("[Storage] Bucket acessível, mas sem objetos ou sem objetos retornados.")


def validate_gemini():
    print("[Gemini] Validando chamada ao Vertex AI Gemini...")
    vertexai.init(project=PROJECT_ID, location=LOCATION)

    model = GenerativeModel(GEMINI_MODEL)
    response = model.generate_content("Responda apenas: OK")

    print("[Gemini] Resposta:")
    print(response.text)


def main():
    print("[App] Iniciando validação GCP WIF...")
    print(f"[App] GOOGLE_APPLICATION_CREDENTIALS={os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}")
    validate_storage()
    validate_gemini()
    print("[App] Validação finalizada com sucesso.")


if __name__ == "__main__":
    main()
