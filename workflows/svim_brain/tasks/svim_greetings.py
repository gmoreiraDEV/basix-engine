import json
import requests

def main():
    response = requests.get("https://dummyjson.com/products")
    response.raise_for_status()  # levanta erro se a requisição falhar

    products_data = response.json().get("products", [])

    with open("products.json", "w", encoding="utf-8") as f:
        json.dump(products_data, f, indent=2, ensure_ascii=False)

    print("Arquivo 'products.json' salvo com sucesso!")

if __name__ == "__main__":
    main()
