
import mexc_api as mx
from mexc_api.common.api import Api
from mexc_api.common.enums import Method, OrderType, Side
from mexc_api.spot.endpoints._account import _Account
from mexc_api.spot.endpoints._market import _Market
import requests
import time
from datetime import datetime, timedelta

api_key = 'mx0vglkJnEzqyCHOA9'
api_secret = 'd46f4b330a67478793d174d0931e576c'

moeda_negociada = "PEPEUSDC"    # CRYPTO MOEDA
tempo_candles = "15m"           # Pode ser "1m", "5m", "15m", "1h", "1d", etc
intervalo_candles = "50"        # QUANTOS CANDLES FECHADOS QUER QUE RETORNA

api = Api(api_key, api_secret)        #API PARA SER USADA
conta = _Account(api)                 #PREPARANDO PARA USAR FUNÇÃO
conta1 = conta.get_account_info()     #FUNÇÃO DA CONTA PARA OBTER INFORMAÇÕES
conta2 = conta1['balances']           #SO PARA OBTER O SALDO
conect = _Market(api)


print(a)

# Função para consultar o saldo
def Saldo(ativo):
    # Filtrando o ativo específico de forma segura
    disponivel = next((b for b in conta1.get('balances', []) if b.get('asset') == ativo), None)
    return float(disponivel['free']) if disponivel else 0.0

# Função para obter os dados históricos de candles
def obter_dados():
    url = "https://api.mexc.com/api/v3/klines"
    params = {
        "symbol": moeda_negociada,  # ativo negociado
        "interval": tempo_candles,  # Intervalo do candle
        "limit": intervalo_candles  # Número de registros retornados
    }
    response = requests.get(url, params=params)
    return response.json()

# Função para calcular a média móvel
class Media:
    def Fechamentos(self, numero_candles, dados_candles):
        self.numero_candles = int(numero_candles)
        oi = [float(candle[4]) for candle in dados_candles[-(self.numero_candles):]]  # Preço de fechamento
        valor_da_media = sum(oi) / len(oi)
        return round(valor_da_media, 9)

# Função principal do trading
def executar_trading():
    saldo_usdc = Saldo("USDC")
    saldo_pepe = Saldo("PEPE")
    a = conect.test()
    # Obtendo os dados dos candles mais recentes
    dados_candles = obter_dados()

    # Calculando as médias móveis
    medias = Media()
    valor_moeda = medias.Fechamentos(1, dados_candles)
    media_rapida = medias.Fechamentos(21, dados_candles)
    media_devagar = medias.Fechamentos(45, dados_candles)
    pepe = round (1/valor_moeda)

    # Exibindo as médias móveis
    print(f"Período 21: {media_rapida:.8f}")
    print(f"Período 45: {media_devagar:.8f}")

    # Definindo a lógica de compra e venda
    if saldo_usdc >= 1:
        if media_rapida > media_devagar:
            print("COMPRA")
            ordem = conta.new_order(
             symbol = "PEPEUSDC" ,
             side = Side.BUY ,
             order_type = OrderType.MARKET ,
             quote_order_quantity = saldo_usdc
             )
        else:
            print("ordem não aplicada para comprar")
    else:
        print("saldo insuficiente para comprar")
            # Lógica de compra a ser implementada
    if saldo_pepe >= pepe:
        if media_rapida < media_devagar:
            print("VENDA")
            ordem = conta.new_order(
             symbol = "PEPEUSDC" ,
             side = Side.SELL ,
             order_type = OrderType.MARKET ,
             quantity = saldo_pepe 
             )
        else:
            print("ordem não aplicada para venda")
    else:
        print("saldo insuficiente para venda")

            # Lógica de venda a ser implementada

# Função para calcular o tempo até o próximo múltiplo de 5 minutos
def tempo_para_proximo_5min():
    agora = datetime.now()
    minutos_restantes = 1 - (agora.minute % 1)  # Calcular quantos minutos faltam para o próximo múltiplo de 5
    proximo_horario = agora + timedelta(minutes=minutos_restantes, seconds=-agora.second, microseconds=-agora.microsecond)
    return (proximo_horario - agora).total_seconds()

# Loop contínuo no final do código
if __name__ == "__main__":
    while True:
        print("\n🔄 Atualizando médias móveis e verificando sinais de trade...")

        # Chama a função de trading
        executar_trading()

        # Espera até o próximo múltiplo de 5 minutos
        tempo_espera = tempo_para_proximo_5min()
        print(f"Aguardando {tempo_espera} segundos até o próximo múltiplo de 5 minutos...")
        time.sleep(tempo_espera)  # Aguarda até o próximo horário exato