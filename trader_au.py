
from flask import Flask, jsonify
import threading
import time
from datetime import datetime, timedelta
import mexc_api as mx
from mexc_api.common.api import Api
from mexc_api.common.enums import Method, OrderType, Side
from mexc_api.spot.endpoints._account import _Account
from mexc_api.spot.endpoints._market import _Market
import requests

# Inicializando o Flask
app = Flask(__name__)

# Definindo as variáveis de API
api_key = 'mx0vglkJnEzqyCHOA9'
api_secret = 'd46f4b330a67478793d174d0931e576c'
moeda_negociada = "PEPEUSDC"
tempo_candles = "15m"
intervalo_candles = "50"

# Conectando à API
api = Api(api_key, api_secret)
conta = _Account(api)
conta1 = conta.get_account_info()
conect = _Market(api)

# Função para consultar o saldo
def Saldo(ativo):
    disponivel = next((b for b in conta1.get('balances', []) if b.get('asset') == ativo), None)
    return float(disponivel['free']) if disponivel else 0.0

# Função para obter os dados históricos de candles
def obter_dados():
    url = "https://api.mexc.com/api/v3/klines"
    params = {
        "symbol": moeda_negociada,
        "interval": tempo_candles,
        "limit": intervalo_candles
    }
    response = requests.get(url, params=params)
    return response.json()

# Função para calcular a média móvel
class Media:
    def Fechamentos(self, numero_candles, dados_candles):
        self.numero_candles = int(numero_candles)
        oi = [float(candle[4]) for candle in dados_candles[-(self.numero_candles):]]
        valor_da_media = sum(oi) / len(oi)
        return round(valor_da_media, 9)

# Função principal do trading
def executar_trading():
    saldo_usdc = Saldo("USDC")
    saldo_pepe = Saldo("PEPE")
    a = conect.test()
    dados_candles = obter_dados()

    medias = Media()
    valor_moeda = medias.Fechamentos(1, dados_candles)
    media_rapida = medias.Fechamentos(21, dados_candles)
    media_devagar = medias.Fechamentos(45, dados_candles)
    pepe = round(1 / valor_moeda)

    print(f"Período 21: {media_rapida:.8f}")
    print(f"Período 45: {media_devagar:.8f}")

    if saldo_usdc >= 1:
        if media_rapida > media_devagar:
            print("COMPRA")
            ordem = conta.new_order(
                symbol="PEPEUSDC",
                side=Side.BUY,
                order_type=OrderType.MARKET,
                quote_order_quantity=saldo_usdc
            )
            print(ordem)
        else:
            print("ordem não aplicada para comprar")
    else:
        print("saldo insuficiente para comprar")

    if saldo_pepe >= pepe:
        if media_rapida < media_devagar:
            print("VENDA")
            ordem = conta.new_order(
                symbol="PEPEUSDC",
                side=Side.SELL,
                order_type=OrderType.MARKET,
                quantity=saldo_pepe
            )
            print(ordem)
        else:
            print("ordem não aplicada para venda")
    else:
        print("saldo insuficiente para venda")

# Função para calcular o tempo até o próximo múltiplo de 5 minutos
def tempo_para_proximo_5min():
    agora = datetime.now()
    minutos_restantes = 5 - (agora.minute % 5)
    proximo_horario = agora + timedelta(minutes=minutos_restantes, seconds=-agora.second, microseconds=-agora.microsecond)
    return (proximo_horario - agora).total_seconds()

# Endpoint para verificar o status do trading
@app.route('/status', methods=['GET'])
def status():
    return jsonify({"status": "Trading está rodando."})

# Função para rodar o trading em um thread separado
def rodar_trading_em_thread():
    while True:
        print("\n🔄 Atualizando médias móveis e verificando sinais de trade...")
        executar_trading()

        # Espera até o próximo múltiplo de 5 minutos
        tempo_espera = tempo_para_proximo_5min()
        print(f"Aguardando {tempo_espera} segundos até o próximo múltiplo de 5 minutos...")
        time.sleep(tempo_espera)

# Função para iniciar o servidor Flask
def iniciar_servidor():
    flask_thread = threading.Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': 10000})
    flask_thread.daemon = True
    flask_thread.start()

# Iniciar o servidor Flask e o trading em paralelo
if __name__ == "__main__":
    iniciar_servidor()
    rodar_trading_em_thread()
