
# terreno
# custo (em minutos) de ENTRAR em uma célula de cada tipo
CUSTO_TERRENO = {
    "M": 200,   # montanha
    "A": 30,    # água / mar
    "F": 15,    # floresta
    "R": 5,     # rochoso / acidentado
    ".": 1,     # livre
}

# marcadores do mapa
ORIGEM = "1"
DESTINO = "U"
CUSTO_ORIGEM_DESTINO = 1   # enunciado: origem e destino custam +1 minuto

# Terreno "embaixo" de cada marcador de ginásio (o marcador substitui a letra
# do terreno no arquivo). 'auto' = terreno mais comum entre os 4 vizinhos
# (empate -> o mais barato). Também pode ser uma letra fixa: 'A', 'F', 'R', 'M' ou '.'
TERRENO_SOB_GINASIO = "auto"

# ginásios
# (marcador no mapa -> dificuldade). A ordem desta lista é a ordem 1º..24º Gym.
DIFICULDADE = {
    "2": 35,  "3": 40,  "4": 45,  "5": 50,  "6": 55,  "7": 60,  "8": 65,  "9": 70,
    "B": 75,  "C": 80,  "D": 85,  "E": 90,  "G": 95,  "H": 100, "I": 110, "J": 120,
    "K": 130, "L": 140, "N": 150, "O": 155, "P": 160, "Q": 165, "S": 170, "T": 180,
}

# pokémon
PODER = {            # fator de poder
    "Pikachu": 1.5,
    "Bulbassauro": 1.4,
    "Rattata": 1.3,
    "Caterpie": 1.2,
    "Weedle": 1.1,
}
ENERGIA_INICIAL = 6          # cada Pokémon começa com 6 pontos
PERDA_POR_BATALHA = 1        # e perde 1 por batalha em que participa
ENERGIA_MIN_FINAL = 1        # pelo menos um Pokémon deve chegar com energia >= 1

# busca local
SEMENTE = 42
