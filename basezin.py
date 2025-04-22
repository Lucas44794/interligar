import base64

# Ler o conteúdo do arquivo base.txt
with open("base.txt", "r") as arquivo:
    base64_text = arquivo.read()

# Remover o prefixo "data:image/png;base64,"
base64_text = base64_text.replace("data:image/png;base64,", "").replace("\n", "").replace("\r", "").replace(" ", "")

# Decodificar o Base64
try:
    image_data = base64.b64decode(base64_text)
    
    # Salvar a imagem em um arquivo
    with open("imagem.png", "wb") as imagem:
        imagem.write(image_data)
    
    print("Imagem gerada com sucesso!")
except Exception as e:
    print(f"Erro ao decodificar Base64: {e}")