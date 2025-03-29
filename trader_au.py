import mexc_api as mx
from mexc_api.common.api import Api
from mexc_api.common.enums import Method, OrderType, Side
from mexc_api.spot.endpoints._account import _Account
from mexc_api.spot.endpoints._market import _Market
import requests
import time
from datetime import datetime, timedelta
from flask import Flask
import threading
import os

# Inicializa Flask
app = Flask(__name__)

@app.route('/')
def home():
    executar_trading()
    return executar_trading()

# Configuração da API Mexc
api_key = 'mx0vglkJnEzqyCHOA9'
api_secret = 'd46f4b330a67478793d174d0931e576c'

moeda_negociada = "PEPEUSDC"
tempo_candles = "15m"
intervalo_candles = "50"

api = Api(api_key, api_secret)
conta = _Account(api)
conect = _Market(api)

# Função para consultar o saldo
def Saldo(ativo):
    conta1 = conta.get_account_info()
    disponivel = next((b for b in conta1.get('balances', []) if b.get('asset') == ativo), None)
    return float(disponivel['free']) if disponivel else 0.0

# Função para obter os dados históricos de candles
def obter_dados():
    url = "https://api.mexc.com/api/v3/klines"
    params = {"symbol": moeda_negociada, "interval": tempo_candles, "limit": intervalo_candles}
    response = requests.get(url, params=params)
    return response.json()

# Função para calcular a média móvel
class Media:
    def Fechamentos(self, numero_candles, dados_candles):
        valores = [float(candle[4]) for candle in dados_candles[-int(numero_candles):]]
        return round(sum(valores) / len(valores), 9)

# Função principal do trading
def executar_trading():
    while True:
        try:
            saldo_usdc = Saldo("USDC")
            saldo_pepe = Saldo("PEPE")
            dados_candles = obter_dados()

            medias = Media()
            valor_moeda = medias.Fechamentos(1, dados_candles)
            media_rapida = medias.Fechamentos(21, dados_candles)
            media_devagar = medias.Fechamentos(45, dados_candles)
            pepe = round(1 / valor_moeda)

            print(f"Período 21: {media_rapida:.8f}")
            print(f"Período 45: {media_devagar:.8f}")

            if saldo_usdc >= 1 and media_rapida > media_devagar:
                print("COMPRA")
                conta.new_order(
                    symbol="PEPEUSDC",
                    side=Side.BUY,
                    order_type=OrderType.MARKET,
                    quote_order_quantity=saldo_usdc
                )
            else:
                print("Ordem não aplicada para compra")

            if saldo_pepe >= pepe and media_rapida < media_devagar:
                print("VENDA")
                conta.new_order(
                    symbol="PEPEUSDC",
                    side=Side.SELL,
                    order_type=OrderType.MARKET,
                    quantity=saldo_pepe
                )
            else:
                print("Ordem não aplicada para venda")

            print(saldo_usdc, saldo_pepe, pepe)
            time.sleep(30)  # Aguarda 30 segundos antes da próxima iteração

        except Exception as e:
            print(f"Erro no bot: {e}")
            time.sleep(10)  # Espera antes de tentar novamente em caso de erro

# Iniciar o servidor Flask
def start_web_server():
    port = int(os.environ.get("PORT", 10000))  # Render define a variável PORT automaticamente
    app.run(host='0.0.0.0', port=port)

# Rodar o bot e o servidor Flask em threads separadas
if __name__ == "__main__":
    executar_trading()
    start_web_server()