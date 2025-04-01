import mexc_api as mx
from mexc_api.common.api import Api
from mexc_api.common.enums import Method, OrderType, Side
from mexc_api.spot.endpoints._account import _Account
from mexc_api.spot.endpoints._market import _Market
import requests
import time
from flask import Flask
import threading
import os
import logging

# Configuração do logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuração da API Mexc
api_key = 'mx0vglkJnEzqyCHOA9'
api_secret = 'd46f4b330a67478793d174d0931e576c'

moeda_negociada = "PEPEUSDC"
tempo_candles = "15m"
intervalo_candles = "50"

api = Api(api_key, api_secret)
conta = _Account(api)
conect = _Market(api)

# Variável global para armazenar o status do bot
bot_status = "Bot ainda não iniciou."

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
    global bot_status
    bot_status = "Bot está rodando..."
    logger.info("Iniciando a execução do bot de trading...")  # Log para indicar que o bot foi iniciado

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
            receber = saldo_pepe * valor_moeda

            bot_status = f"Última análise: Média 21={media_rapida:.8f}, Média 45={media_devagar:.8f}"
            logger.info(bot_status)  # Log da análise atual

            if saldo_usdc >= 1 and media_rapida > media_devagar:
                bot_status += " | COMPRA realizada!"
                conta.new_order(
                    symbol="PEPEUSDC",
                    side=Side.BUY,
                    order_type=OrderType.MARKET,
                    quote_order_quantity=str(saldo_usdc)
                )
                logger.info("Compra realizada com sucesso!")  # Log da compra realizada
            else:
                bot_status += " | Nenhuma compra feita."
                logger.info("Nenhuma compra feita.")  # Log para caso não haja compra

            if saldo_pepe >= pepe and media_rapida < media_devagar:
                bot_status += " | VENDA realizada!"
                conta.new_order(
                    symbol="PEPEUSDC",
                    side=Side.SELL,
                    order_type=OrderType.MARKET,
                    quote_order_quantity=str(receber)
                )
                logger.info("Venda realizada com sucesso!")  # Log da venda realizada
            else:
                bot_status += " | Nenhuma venda feita."
                logger.info("Nenhuma venda feita.")  # Log para caso não haja venda

            time.sleep(60)

        except Exception as e:
            bot_status = f"Erro no bot: {e}"
            logger.error(f"Erro no bot: {e}")  # Log do erro
            time.sleep(60)

# Criar e iniciar o Flask
app = Flask(__name__)

@app.route("/")
def home():
    return f"<h1>Trading bot está rodando!</h1><p>{bot_status}</p>"

# Iniciar o bot em uma thread separada
threading.Thread(target=executar_trading, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))