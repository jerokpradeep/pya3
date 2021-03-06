import requests
import json
import hashlib
import enum
import logging
import pandas as pd
from datetime import time,datetime
from collections import namedtuple
import os
import websocket
import rel

logger = logging.getLogger(__name__)

Instrument = namedtuple('Instrument', ['exchange', 'token', 'symbol','name', 'expiry', 'lot_size'])


class TransactionType(enum.Enum):
    Buy = 'BUY'
    Sell = 'SELL'

class OrderType(enum.Enum):
    Market = 'MKT'
    Limit = 'L'
    StopLossLimit = 'SL'
    StopLossMarket = 'SL-M'

class ProductType(enum.Enum):
    Intraday = 'MIS'
    Delivery = 'CNC'
    CoverOrder = 'CO'
    BracketOrder = 'BO'

def encrypt_string(hashing):
    sha = hashlib.sha256(hashing.encode()).hexdigest()
    return sha

class Aliceblue:
    # BASE_URL
    base_url = "https://a3.aliceblueonline.com/rest/AliceBlueAPIService/api/"
    api_name = "Codifi API Connect - Python Lib "
    version = "1.0.7"
    base_url_c = "https://v2api.aliceblueonline.com/restpy/static/contract_master/%s.csv"

    # Products
    PRODUCT_INTRADAY = "MIS"
    PRODUCT_COVER_ODRER = "CO"
    PRODUCT_CNC = "CNC"
    PRODUCT_BRACKET_ORDER = "BO"
    PRODUCT_NRML = "NRML"

    # Order Type
    REGULAR_ORDER = "REGULAR"
    LIMIT_ORDER = "L"
    STOPLOSS_ORDER = "SL"
    MARKET_ORDER = "MKT"

    # Transaction type
    BUY_ORDER = "BUY"
    SELL_ORDER = "SELL"

    # Positions
    RETENTION_DAY = "DAY" or "NET"

    # Exchanges
    EXCHANGE_NSE = "NSE"
    EXCHANGE_NFO = "NFO"
    EXCHANGE_CDS = "CDS"
    EXCHANGE_BSE = "BSE"
    EXCHANGE_BFO = "BFO"
    EXCHANGE_BCD = "BCD"
    EXCHANGE_MCX = "MCX"

    # Status constants
    STATUS_COMPLETE = "COMPLETE"
    STATUS_REJECTED = "REJECTED"
    STATUS_CANCELLED = "CANCELLED"
    ENC = None
    ws = None
    subscriptions = None

    # response = requests.get(base_url);
    # Getscrip URI

    _sub_urls = {
        # Authorization
        "encryption_key": "customer/getAPIEncpkey",
        "getsessiondata": "customer/getUserSID",

        # Market Watch
        "marketwatch_scrips": "marketWatch/fetchMWScrips",
        "addscrips": "marketWatch/addScripToMW",
        "getmarketwatch_list": "marketWatch/fetchMWList",
        "scripdetails": "ScripDetails/getScripQuoteDetails",
        "getdelete_scrips": "marketWatch/deleteMWScrip",

        # OrderManagement
        "squareoffposition": "positionAndHoldings/sqrOofPosition",
        "position_conversion": "positionAndHoldings/positionConvertion",
        "placeorder": "placeOrder/executePlaceOrder",
        "modifyorder": "placeOrder/modifyOrder",
        "marketorder": "placeOrder/executePlaceOrder",
        "exitboorder": "placeOrder/exitBracketOrder",
        "bracketorder": "placeOrder/executePlaceOrder",
        "positiondata": "positionAndHoldings/positionBook",
        "orderbook": "placeOrder/fetchOrderBook",
        "tradebook": "placeOrder/fetchTradeBook",
        "holding": "positionAndHoldings/holdings",
        "orderhistory": "placeOrder/orderHistory",
        "cancelorder": "placeOrder/cancelOrder",
        "profile": "customer/accountDetails",
        # Funds
        "fundsrecord": "limits/getRmsLimits",
        # Websockey
        "base_url_socket" :"wss://ws1.aliceblueonline.com/NorenWS/"

    }

    # Common Method
    def __init__(self,
                 user_id,
                 api_key,
                 base=None,
                 session_id=None,
                 disable_ssl=False):

        self.user_id = user_id.upper()
        self.api_key = api_key
        self.disable_ssl = disable_ssl
        self.session_id = session_id
        self.base = base or self.base_url

    def _get(self, sub_url, data=None):
        """Get method declaration"""
        url = self.base + self._sub_urls[sub_url]
        return self._request(url, "GET", data=data)

    def _post(self, sub_url, data=None):
        """Post method declaration"""
        url = self.base + self._sub_urls[sub_url]
        return self._request(url, "POST", data=data)

    def _dummypost(self, url, data=None):
        """Post method declaration"""
        return self._request(url, "POST", data=data)

    def _user_agent(self):
        return self.api_name + self.version

    """Authorization get to call all requests"""
    def _user_authorization(self):
        if self.session_id:
            return "Bearer " + self.user_id.upper() + " " + self.session_id
        else:
            return ""

    """Common request to call POST and GET method"""
    def _request(self, method, req_type, data=None):
        """
        Headers with authorization. For some requests authorization
        is not required. It will be send as empty String
        """
        _headers = {
            "X-SAS-Version": "2.0",
            "User-Agent": self._user_agent(),
            "Authorization": self._user_authorization(),

        }
        if req_type == "POST":
            try:
                response = requests.post(method, json=data, headers=_headers, )
            except (requests.ConnectionError, requests.Timeout) as exception:
                return {'stat':'Not_ok','emsg':'Please Check the Internet connection.','encKey':None}
            if response.status_code == 200:
                return json.loads(response.text)
            else:
                emsg=str(response.status_code)+' - '+response.reason
                return {'stat':'Not_ok','emsg':emsg,'encKey':None}

        elif req_type == "GET":
            try:
                response = requests.get(method, json=data, headers=_headers)
            except (requests.ConnectionError, requests.Timeout) as exception:
                return {'stat':'Not_ok','emsg':'Please Check the Internet connection.','encKey':None}
            return json.loads(response.text)

    # Methods to call HTTP Request

    """Userlogin method with userid and userapi_key"""
    def get_session_id(self, data=None):
        data = {'userId': self.user_id.upper()}
        response = self._post("encryption_key", data)
        if response['encKey'] is None:
            return response['emsg']
        else:
            data = encrypt_string(self.user_id.upper() + self.api_key + response['encKey'])
        data = {'userId': self.user_id.upper(), 'userData': data}
        res = self._post("getsessiondata", data)

        if res['stat'] == 'Ok':
            self.session_id = res['sessionID']
        return res

    """GET Market watchlist"""
    def getmarketwatch_list(self):
        marketwatchrespdata = self._get("getmarketwatch_list")
        return marketwatchrespdata

    """GET Tradebook Records"""
    def get_trade_book(self):
        tradebookresp = self._get("tradebook")
        return tradebookresp

    def get_profile(self):
        profile = self._get("profile")
        return profile

    """GET Holdings Records"""
    def get_holding_positions(self):
        holdingresp = self._get("holding")
        return holdingresp

    """GET Orderbook Records"""
    def order_data(self):
        orderresp = self._get("orderbook")
        return orderresp

    def get_order_history(self, nextorder):
        if nextorder == '':
            orderresp = self._get("orderbook")
            return orderresp
        else:
            data = {'nestOrderNumber': nextorder}
            orderhistoryresp = self._post("orderhistory", data)
            return orderhistoryresp

    """Method to call Cancel Orders"""
    def cancel_order(self, exchange,
                     nestordernmbr,
                     tradingsymbol):
        data = {'exch': exchange,
                'nestOrderNumber': nestordernmbr,
                'trading_symbol': tradingsymbol}
        cancelresp = self._post("cancelorder", data)
        return cancelresp

    def marketwatch_scripsdata(self, mwname, ):
        data = {'mwName': mwname, }
        marketwatchresp = self._post("marketwatch_scrips", data)
        return marketwatchresp

    """Method to call Add Scrips"""
    def addscrips(self,
                  mwname,
                  exchange,
                  token):
        data = {'mwName': mwname,
                'exch': exchange,
                'symbol': token, }
        addscripsresp = self._post("addscrips", data)
        return addscripsresp

    """Method to call Delete Scrips"""
    def deletescrips(self,
                     mwname,
                     exchange,
                     token):
        data = {'mwName': mwname,
                'exch': exchange,
                'symbol': token, }
        deletescripsresp = self._post("getdelete_scrips", data)
        return deletescripsresp

    """Method to call Scrip Details"""
    # def get_instrument_by_token(self,
    #                    exchange,
    #                    token):
    #     data = {'exch': exchange,
    #             'symbol': token}
    #     scripsdetailresp = self._post("scripdetails", data)
    #     return scripsdetailresp

    """Method to call Squareoff Positions"""
    def squareoff_positions(self,
                            exchange,
                            pCode,
                            qty,
                            tokenno,
                            symbol):
        data = {'exchSeg': exchange,
                'pCode': pCode,
                'netQty': qty,
                'tockenNo': tokenno,
                'symbol': symbol}
        squareoffresp = self._post("squareoffposition", data)
        return squareoffresp

    """Method to call  Place Order"""
    def place_order(self, transaction_type, instrument, quantity, order_type,
                    product_type, price=0.0, trigger_price=None,
                    stop_loss=None, square_off=None, trailing_sl=None,
                    is_amo=False,
                    order_tag='order1',
                    is_ioc=False):
        if transaction_type is None:
            raise TypeError("Required parameter transaction_type not of type TransactionType")

        if instrument is None:
            raise TypeError("Required parameter instrument not of type Instrument")

        if not isinstance(quantity, int):
            raise TypeError("Required parameter quantity not of type int")

        if order_type is None:
            raise TypeError("Required parameter order_type not of type OrderType")

        if product_type is None:
            raise TypeError("Required parameter product_type not of type ProductType")

        if price is not None and not isinstance(price, float):
            raise TypeError("Optional parameter price not of type float")

        if trigger_price is not None and not isinstance(trigger_price, float):
            raise TypeError("Optional parameter trigger_price not of type float")
        complexty = "regular"
        discqty=0
        exch=instrument['exch']
        pCode = product_type.value
        price = price
        prctyp = order_type.value
        qty = quantity
        if is_ioc:
            ret='IOC'
        else:
            ret='DAY'
        if exch == 'NSE' or exch == 'BSE':
            trading_symbol=instrument['symbol']
        else:
            trading_symbol = instrument['tradingSymbol']
        symbol_id=instrument['token']
        transtype=transaction_type.value
        trigPrice=trigger_price
        # print("pCode:",instrument)
        data = [{'complexty': complexty,
                 'discqty': discqty,
                 'exch': exch,
                 'pCode': pCode,
                 'price': price,
                 'prctyp': prctyp,
                 'qty': qty,
                 'ret': ret,
                 'symbol_id': symbol_id,
                 'trading_symbol': trading_symbol,
                 'transtype': transtype,
                 "stopLoss": stop_loss,
                 "target": square_off,
                 "trailing_stop_loss": trailing_sl,
                 'trigPrice': trigPrice}]
        # print(data)
        placeorderresp = self._post("placeorder", data)
        return placeorderresp

    """Method to call  Bracket Order"""
    def bracket_order(self,
                      complexty,
                      discqty,
                      exch,
                      pCode,
                      price,
                      prctyp,
                      qty,
                      ret,
                      stopLoss,
                      symbol_id,
                      target,
                      trailing_stop_loss,
                      trading_symbol,
                      transtype,
                      trigPrice):
        data = [{'complexty': complexty,
                 'discqty': discqty,
                 'exch': exch,
                 'pCode': pCode,
                 'price': price,
                 'prctyp': prctyp,
                 'qty': qty,
                 'ret': ret,
                 'target': target,
                 'stopLoss': stopLoss,
                 'trailing_stop_loss': trailing_stop_loss,
                 'symbol_id': symbol_id,
                 'trading_symbol': trading_symbol,
                 'transtype': transtype,
                 'trigPrice': trigPrice}]
        bracketorderresp = self._post("bracketorder", data)
        return bracketorderresp

    """Method to get Funds Data"""

    def get_balance(self):
        fundsresp = self._get("fundsrecord")
        return fundsresp

    """Method to call Modify Order"""

    def modifyorder(self,
                    discqty,
                    exch,
                    filledQuantity,
                    nestOrderNumber,
                    prctyp,
                    price,
                    qty,
                    trading_symbol,
                    trigPrice,
                    transtype,
                    pCode):
        data = {'discqty': discqty,
                'exch': exch,
                'filledQuantity': filledQuantity,
                'nestOrderNumber': nestOrderNumber,
                'prctyp': prctyp,
                'price': price,
                'qty': qty,
                'trading_symbol': trading_symbol,
                'trigPrice': trigPrice,
                'transtype': transtype,
                'pCode': pCode}
        modifyorderresp = self._post("modifyorder", data)
        return modifyorderresp

    """Method to call Market Order"""

    def marketorder(self,
                    complexty,
                    discqty,
                    exch,
                    pCode,
                    prctyp,
                    price,
                    qty,
                    ret,
                    symbol_id,
                    trading_symbol,
                    transtype,
                    trigPrice):
        data = [{'complexty': complexty,
                 'discqty': discqty,
                 'exch': exch,
                 'pCode': pCode,
                 'prctyp': prctyp,
                 'price': price,
                 'qty': qty,
                 'ret': ret,
                 'symbol_id': symbol_id,
                 'trading_symbol': trading_symbol,
                 'transtype': transtype,
                 'trigPrice': trigPrice}]
        marketorderresp = self._post("marketorder", data)
        return marketorderresp

    """Method to call Exitbook  Order"""

    def exitboorder(self,nestOrderNumber,symbolOrderId,status, ):
        data = {'nestOrderNumber': nestOrderNumber,
                'symbolOrderId': symbolOrderId,
                'status': status, }
        exitboorderresp = self._post("exitboorder", data)
        return exitboorderresp

    """Method to get Position Book"""

    def positionbook(self,ret, ):
        data = {'ret': ret, }
        positionbookresp = self._post("positiondata", data)
        return positionbookresp

    def get_daywise_positions(self):
        data = {'ret': 'DAY' }
        positionbookresp = self._post("positiondata", data)
        return positionbookresp

    def get_netwise_positions(self,):
        data = {'ret': 'NET' }
        positionbookresp = self._post("positiondata", data)
        return positionbookresp
    """Method to get Scripsforsearch"""

    def search_instruments(self,exchange, symbol):

        scrip_Url = "https://a3.aliceblueonline.com/rest/DataApiService/v2/exchange/getScripForSearch"
        data = {'symbol': symbol, 'exchange': [exchange]}
        scrip_response = self._dummypost(scrip_Url, data)
        return scrip_response

    # def get_instrument_by_symbol(self,exchange, symbol):
    #
    #     scrip_Url = "https://a3.aliceblueonline.com/rest/DataApiService/v2/exchange/getScripForSearch"
    #     data = {'symbol': symbol, 'exchange': ['ALL']}
    #     scrip_response = self._dummypost(scrip_Url, data)
    #     if 'stat' in scrip_response:
    #         return scrip_response['emsg']
    #     else:
    #         if len(scrip_response)>=1:
    #             return scrip_response[0]
    #         else:
    #             return scrip_response

    def place_basket_order(self,orders):
        data=[]
        for i in range(len(orders)):
            order_data = orders[i]
            complexty = "regular"
            discqty = 0
            exch = order_data['instrument']['exch']
            pCode = order_data['product_type'].value
            price = order_data['price'] if 'price' in order_data else 0

            prctyp = order_data['order_type'].value
            qty = order_data['quantity']
            if 'is_ioc' in order_data and order_data['is_ioc']:
                ret = 'IOC'
            else:
                ret = 'DAY'
            if exch == 'NSE' or exch == 'BSE':
                trading_symbol = order_data['instrument']['symbol']
            else:
                trading_symbol = order_data['instrument']['tradingSymbol']
            symbol_id = order_data['instrument']['token']
            transtype = order_data['transaction_type'].value
            trigPrice = order_data['trigger_price'] if 'trigger_price' in order_data else None
            stop_loss = order_data['stop_loss'] if 'stop_loss' in order_data else None
            trailing_sl = order_data['trailing_sl'] if 'trailing_sl' in order_data else None
            square_off = order_data['square_off'] if 'square_off' in order_data else None

            request_data={'complexty': complexty,
                     'discqty': discqty,
                     'exch': exch,
                     'pCode': pCode,
                     'price': price,
                     'prctyp': prctyp,
                     'qty': qty,
                     'ret': ret,
                     'symbol_id': symbol_id,
                     'trading_symbol': trading_symbol,
                     'transtype': transtype,
                     "stopLoss": stop_loss,
                     "target": square_off,
                     "trailing_stop_loss": trailing_sl,
                     'trigPrice': trigPrice}

            data.append(request_data)
        # print(data)
        placeorderresp = self._post("placeorder", data)
        return placeorderresp

    def get_contract_master(self,exchange):
        if len(exchange) == 3:
            print("NOTE: Today's contract master file will be updated after 08:00 AM. Before 08:00 AM previous day contract file be downloaded.")
            if time(8,00) <= datetime.now().time():
                url= self.base_url_c % exchange.upper()
                response = requests.get(url)
                with open("%s.csv"% exchange.upper(), "w") as f:
                    f.write(response.text)
                return {"stat":"ok","msg":"Today contract File Downloaded"}
            else:
                return {"stat":"ok","msg":"Previous day contract file saved"}
        elif exchange is None:
            return {"stat": "Not_ok", "emsg": "Invalid Exchange parameter"}
        else:
            return {"stat":"Not_ok","emsg":"Invalid Exchange parameter"}

    def get_instrument_by_symbol(self,exchange, symbol):
        try:
            contract = pd.read_csv("%s.csv" % exchange)
            filter_contract = contract[contract['symbol'] == symbol.upper()]
            if len(filter_contract) == 0:
                return {"stat": "Not_ok", "emsg": "The symbol is not available in this exchange"}
            else:
                filter_contract = filter_contract.reset_index()
                if 'expiry_date' in filter_contract:
                    inst = Instrument(filter_contract['exch'][0], filter_contract['token'][0], filter_contract['symbol'][0], filter_contract['trading_symbol'][0], filter_contract['expiry_date'][0],filter_contract['lot_size'][0])
                else:
                    inst = Instrument(filter_contract['exch'][0], filter_contract['token'][0],filter_contract['symbol'][0], filter_contract['trading_symbol'][0],'', filter_contract['lot_size'][0])
                return inst
        except OSError as e:
            if e.errno == 2:
                return {"stat": "Not_ok", "emsg": "Contract master is not available."}
            else:
                return {"stat":"Not_ok","emsg":e}

    def get_instrument_by_token(self,exchange, token):
        try:
            contract = pd.read_csv("%s.csv" % exchange)
            filter_contract = contract[contract['Token'] == token]
            if len(filter_contract) == 0:
                return {"stat": "Not_ok", "emsg": "The symbol is not available in this exchange"}
            else:
                filter_contract = filter_contract.reset_index()
                if 'expiry_date' in filter_contract:
                    inst = Instrument(filter_contract['Exch'][0], filter_contract['Token'][0], filter_contract['Symbol'][0], filter_contract['Trading Symbol'][0], filter_contract['Expiry Date'][0],filter_contract['Lot Size'][0])
                else:
                    inst = Instrument(filter_contract['Exch'][0], filter_contract['Token'][0],filter_contract['Symbol'][0], filter_contract['Trading Symbol'][0],'', filter_contract['Lot Size'][0])
                return inst
        except OSError as e:
            if e.errno == 2:
                return {"stat": "Not_ok", "emsg": "Contract master is not available."}
            else:
                return {"stat":"Not_ok","emsg":e}

    def get_instrument_for_fno(self,exch,symbol, expiry_date,is_fut=True,strike=None,is_CE = False):
        # print(exch)
        if exch in ['NFO','CDS','MCX','BFO','BCD']:
            pass
        else:
            return {"stat":"Not_ok","emsg":"Invalid exchange"}
        if not symbol:
            return {"stat": "Not_ok", "emsg": "Symbol is Null"}
        try:
            expiry_date=datetime.strptime(expiry_date, "%d-%m-%Y").date()
        except ValueError as e:
            return {"stat": "Not_ok", "emsg": e}
        if type(is_CE) is bool:
            if is_CE == True:
                option_type="CE"
            else:
                option_type="PE"
        else:
            return {"stat": "Not_ok", "emsg": "is_fut is not boolean value"}
        # print(option_type)
        try:
            contract = pd.read_csv("%s.csv" % exch)
            # print(strike,is_fut)
            if is_fut == False:
                if strike:
                    filter_contract = contract[(contract['exch'] == exch)&(contract['symbol'] == symbol)&(contract['option_type'] == option_type)&(contract['strike_price'] == strike)&(contract['expiry_date'] == expiry_date.strftime('%Y-%m-%d'))]
                else:
                    filter_contract = contract[(contract['exch'] == exch)&(contract['symbol'] == symbol)&(contract['option_type'] == option_type)&(contract['expiry_date'] == expiry_date.strftime('%Y-%m-%d'))]
            if is_fut == True:
                if strike == None:
                    filter_contract = contract[(contract['exch'] == exch)&(contract['symbol'] == symbol)&(contract['option_type'] == 'XX')&(contract['strike_price'] == 0)&(contract['expiry_date'] == expiry_date.strftime('%Y-%m-%d'))]
                else:
                    return {"stat": "Not_ok", "emsg": "No strike price for future"}
            # print(len(filter_contract))
            if len(filter_contract) == 0:
                return {"stat": "Not_ok", "emsg": "No Data"}
            else:
                inst=[]
                filter_contract = filter_contract.reset_index()
                for i in range(len(filter_contract)):
                    inst.append(Instrument(filter_contract['exch'][i], filter_contract['token'][i], filter_contract['symbol'][i], filter_contract['trading_symbol'][i], filter_contract['expiry_date'][i],filter_contract['lot_size'][i]))
                return inst
        except OSError as e:
            if e.errno == 2:
                return {"stat": "Not_ok", "emsg": "Contract master is not available."}
            else:
                return {"stat":"Not_ok","emsg":e}

    def get_sessionu(self):
        BASEURL = 'https://a3uat.aliceblueonline.com/rest/AliceBlueAPIService'
        url = BASEURL + "/api/customer/getAPIEncpkey"

        payload = json.dumps({
            "userId": self.user_id
        })
        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        data = response.json()
        # print(data)
        if 'encKey' in data and data['encKey']:
            encKey = data['encKey']
            url = BASEURL + "/api/customer/getUserSID"
            key = self.user_id + self.api_key + encKey
            hash = hashlib.sha256(key.encode('utf-8')).hexdigest()
            payload = json.dumps({
                "userId": self.user_id,
                "userData": hash
            })
            headers = {
                'Content-Type': 'application/json'
            }

            response = requests.request("POST", url, headers=headers, data=payload)
            # print(response.text)
            return response.json()
        else:
            return response.json()

    def invalid_sess(self,session_ID):
        BASEURL = 'https://a3uat.aliceblueonline.com/rest/AliceBlueAPIService'
        url = BASEURL + '/api/ws/invalidateWsSession'
        headers = {
            'Authorization': 'Bearer ' + self.user_id + ' ' + session_ID,
            'Content-Type': 'application/json'
        }
        payload = {"loginType": "API"}
        datas = json.dumps(payload)
        response = requests.request("POST", url, headers=headers, data=datas)
        return response.json()

    def createSession(self,session_ID):
        BASEURL = 'https://a3uat.aliceblueonline.com/rest/AliceBlueAPIService'
        url = BASEURL + '/api/ws/createWsSession'

        headers = {
            'Authorization': 'Bearer ' + self.user_id + ' ' + session_ID,
            'Content-Type': 'application/json'
        }
        payload = {"loginType": "API"}
        datas = json.dumps(payload)
        response = requests.request("POST", url, headers=headers, data=datas)

        # print(response.text)
        return response.json()

    def on_message(self,ws, message):
        print(message)
        data = json.loads(message)
        if 's' in data and data['s'] == 'OK':
            print("Socket Connected.")
            data = {
                "k": self.subscriptions,
                "t": 't',
                "m": "compact_marketdata"
            }
            ws.send(json.dumps(data))

    def on_error(self,ws, error):
        print(error)

    def on_close(self,ws, close_status_code, close_msg):
        print("### closed ###")

    def on_open(self,ws):
        initCon = {
            "susertoken": self.ENC,
            "t": "c",
            "actid": self.user_id + "_API",
            "uid": self.user_id + "_API",
            "source": "API"
        }
        print(initCon)
        self.ws.send(json.dumps(initCon))
        # ws.send(initCon)

    def start_websocket(self,script_subscription):
        session_request=self.get_sessionu()
        if 'sessionID' in session_request:
            self.subscriptions= script_subscription
            session_id = session_request['sessionID']
            sha256_encryption1 = hashlib.sha256(session_id.encode('utf-8')).hexdigest()
            self.ENC = hashlib.sha256(sha256_encryption1.encode('utf-8')).hexdigest()
            invalidSess = self.invalid_sess(session_id)
            if invalidSess['stat']=='Ok':
                print("STAGE 1: invalidSess :",invalidSess['stat'])
                createSess = self.createSession(session_id)
                if createSess['stat']=='Ok':
                    print("STAGE 2: createSess :", createSess['stat'])
                    print("Connecting Socket ...")
                    websocket.enableTrace(False)
                    self.ws = websocket.WebSocketApp(self._sub_urls['base_url_socket'],
                                                on_open=self.on_open,
                                                on_message=self.on_message,
                                                on_close=self.on_close,
                                                on_error=self.on_error)
                    self.ws.run_forever(dispatcher=rel)  # Set dispatcher to automatic reconnection
                    rel.signal(2, rel.abort)  # Keyboard Interrupt
                    rel.dispatch()



class Alice_Wrapper():
    def open_net_position(Net_position):
        open_net_position = [data for data in Net_position if data['Netqty'] != '0']
        return open_net_position

    def close_net_poition(Net_position):
        close_net_position = [data for data in Net_position if data['Netqty'] == '0']
        return close_net_position

    def subscription(script_list):
        if len(script_list) > 0:
            sub_prams=''
            for i in range(len(script_list)):
                end_point = '' if i == len(script_list)-1 else '#'
                sub_prams=sub_prams+script_list[i].exchange+'|'+str(script_list[0].token)+end_point
            return sub_prams