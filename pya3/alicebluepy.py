import requests
import json
import hashlib
import enum
import logging
import pandas as pd
from datetime import time,datetime
from time import sleep
from collections import namedtuple
import os
import websocket
import rel
import ssl

import threading

logger = logging.getLogger(__name__)

Instrument = namedtuple('Instrument', ['exchange', 'token', 'symbol','name', 'expiry', 'lot_size'])



class TransactionType(enum.Enum):
    Buy = 'BUY'
    Sell = 'SELL'

class LiveFeedType(enum.IntEnum):
    MARKET_DATA     = 1
    COMPACT         = 2
    SNAPQUOTE       = 3
    FULL_SNAPQUOTE  = 4

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
    Normal = 'NRML'

def encrypt_string(hashing):
    sha = hashlib.sha256(hashing.encode()).hexdigest()
    return sha

class Aliceblue:
    base_url = "https://ant.aliceblueonline.com/rest/AliceBlueAPIService/api/"
    api_name = "Codifi API Connect - Python Lib "
    version = "1.0.29"
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
    __subscribe_callback = None
    __subscribers = None
    script_subscription_instrument =[]
    ws_connection = False
    # response = requests.get(base_url);
    # Getscrip URI
    __ws_thread = None
    __stop_event = None
    market_depth=None


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
        self.__on_error = None
        self.__on_disconnect = None
        self.__on_open = None
        self.__exchange_codes = None

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
            "Authorization": self._user_authorization()
        }
        if req_type == "POST":
            try:
                response = requests.post(method, json=data, headers=_headers, )
            except (requests.ConnectionError, requests.Timeout) as exception:
                return {'stat':'Not_ok','emsg':exception,'encKey':None}
            if response.status_code == 200:
                return json.loads(response.text)
            else:
                emsg=str(response.status_code)+' - '+response.reason
                return {'stat':'Not_ok','emsg':emsg,'encKey':None}

        elif req_type == "GET":
            try:
                response = requests.get(method, json=data, headers=_headers)
            except (requests.ConnectionError, requests.Timeout) as exception:
                return {'stat':'Not_ok','emsg':exception,'encKey':None}
            if response.status_code == 200:
                return json.loads(response.text)
            else:
                emsg=str(response.status_code)+' - '+response.reason
                return {'stat':'Not_ok','emsg':emsg,'encKey':None}

    def _error_response(self,message):
        return {"stat":"Not_ok","emsg":message}
    # Methods to call HTTP Request

    """Userlogin method with userid and userapi_key"""
    def get_session_id(self, data=None):
        data = {'userId': self.user_id.upper()}
        response = self._post("encryption_key", data)
        if response['encKey'] is None:
            return response
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
        orderresp = self._get("orderbook")
        if nextorder == '':
            # orderresp = self._get("orderbook")
            return orderresp
        else:
            # data = {'nestOrderNumber': nextorder}
            # orderhistoryresp = self._post("orderhistory", data)
            # return orderhistoryresp
            for order in orderresp:
                if order['Nstordno'] == nextorder:
                    return order

    """Method to call Cancel Orders"""
    def cancel_order(self,nestordernmbr):
        data = {'nestOrderNumber': nestordernmbr}
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
    def get_scrip_info(self,instrument):
        data = {'exch': instrument.exchange,
                'symbol': str(instrument.token)}
        scripsdetailresp = self._post("scripdetails", data)
        return scripsdetailresp

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
                    order_tag=None,
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
        if is_amo == True:
            complexty = "AMO"
        else:
            complexty = "regular"
        discqty=0
        exch=instrument.exchange
        if (instrument.exchange == 'NFO' or instrument.exchange == 'MCX')and (product_type.value == 'CNC'):
            pCode = "NRML"
        else:
            if product_type.value == 'BO':
                pCode = "MIS"
                complexty = "BO"
            else:
                pCode = product_type.value
        price = price
        prctyp = order_type.value
        qty = quantity
        if is_ioc:
            ret='IOC'
        else:
            ret='DAY'
        trading_symbol=instrument.name
        symbol_id=str(instrument.token)
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
                 "trigPrice": trigPrice,
                 "orderTag":order_tag}]
        # print(data)
        placeorderresp = self._post("placeorder", data)
        if len(placeorderresp)==1:
            return placeorderresp[0]
        else:
            return placeorderresp

    """Method to get Funds Data"""
    def get_balance(self):
        fundsresp = self._get("fundsrecord")
        return fundsresp

    """Method to call Modify Order"""
    def modify_order(self, transaction_type, instrument, product_type, order_id, order_type, quantity, price=0.0,trigger_price=0.0):
        if not isinstance(instrument, Instrument):
            raise TypeError("Required parameter instrument not of type Instrument")

        if not isinstance(order_id, str):
            raise TypeError("Required parameter order_id not of type str")

        if not isinstance(quantity, int):
            raise TypeError("Optional parameter quantity not of type int")

        if type(order_type) is not OrderType:
            raise TypeError("Optional parameter order_type not of type OrderType")

        if ProductType is None:
            raise TypeError("Required parameter product_type not of type ProductType")

        if price is not None and not isinstance(price, float):
            raise TypeError("Optional parameter price not of type float")

        if trigger_price is not None and not isinstance(trigger_price, float):
            raise TypeError("Optional parameter trigger_price not of type float")
        data = {'discqty': 0,
                'exch': instrument.exchange,
                # 'filledQuantity': filledQuantity,
                'nestOrderNumber': order_id,
                'prctyp': order_type.value,
                'price': price,
                'qty': quantity,
                'trading_symbol': instrument.name,
                'trigPrice': trigger_price,
                'transtype': transaction_type.value,
                'pCode': product_type.value}
        # print(data)
        modifyorderresp = self._post("modifyorder", data)
        return modifyorderresp

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

    def place_basket_order(self,orders):
        data=[]
        for i in range(len(orders)):
            order_data = orders[i]
            if 'is_amo' in order_data and order_data['is_amo']:
                complexty = "AMO"
            else:
                complexty = "regular"
            discqty = 0
            exch = order_data['instrument'].exchange
            if order_data['instrument'].exchange == 'NFO' and order_data['product_type'].value == 'CNC':
                pCode = "NRML"
            else:
                pCode = order_data['product_type'].value
            price = order_data['price'] if 'price' in order_data else 0

            prctyp = order_data['order_type'].value
            qty = order_data['quantity']
            if 'is_ioc' in order_data and order_data['is_ioc']:
                ret = 'IOC'
            else:
                ret = 'DAY'
            trading_symbol = order_data['instrument'].name
            symbol_id = str(order_data['instrument'].token)
            transtype = order_data['transaction_type'].value
            trigPrice = order_data['trigger_price'] if 'trigger_price' in order_data else None
            stop_loss = order_data['stop_loss'] if 'stop_loss' in order_data else None
            trailing_sl = order_data['trailing_sl'] if 'trailing_sl' in order_data else None
            square_off = order_data['square_off'] if 'square_off' in order_data else None
            ordertag = order_data['order_tag'] if 'order_tag' in order_data else None
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
                     "trigPrice": trigPrice,
                     "orderTag":ordertag}
            data.append(request_data)
        # print(data)
        placeorderresp = self._post("placeorder", data)
        return placeorderresp

    def get_contract_master(self,exchange):
        if len(exchange) == 3 or exchange == 'INDICES':
            print("NOTE: Today's contract master file will be updated after 08:00 AM. Before 08:00 AM previous day contract file be downloaded.")
            if time(8,00) <= datetime.now().time() or True:
                url= self.base_url_c % exchange.upper()
                response = requests.get(url)
                with open("%s.csv"% exchange.upper(), "w") as f:
                    f.write(response.text)
                return self._error_response("Today contract File Downloaded")
            else:
                return self._error_response("Previous day contract file saved")
        elif exchange is None:
            return self._error_response("Invalid Exchange parameter")
        else:
            return self._error_response("Invalid Exchange parameter")

    def get_instrument_by_symbol(self,exchange, symbol):
        try:
            contract = pd.read_csv("%s.csv" % exchange)
        except OSError as e:
            if e.errno == 2:
                self.get_contract_master(exchange)
                contract = pd.read_csv("%s.csv" % exchange)
            else:
                return self._error_response(e)
        if exchange == 'INDICES':
            filter_contract = contract[contract['symbol'] == symbol.upper()]
            if len(filter_contract) == 0:
                return self._error_response("The symbol is not available in this exchange")
            else:
                filter_contract = filter_contract.reset_index()
                inst = Instrument(filter_contract['exch'][0], filter_contract['token'][0], filter_contract['symbol'][0],
                                  '', '', '')
                return inst
        else:
            filter_contract = contract[(contract['Symbol'] == symbol.upper())|(contract['Trading Symbol'] == symbol.upper())]
            if len(filter_contract) == 0:
                return self._error_response("The symbol is not available in this exchange")
            else:
                filter_contract = filter_contract.reset_index()
                if 'expiry_date' in filter_contract:
                    inst = Instrument(filter_contract['Exch'][0], filter_contract['Token'][0],
                                      filter_contract['Symbol'][0], filter_contract['Trading Symbol'][0],
                                      filter_contract['Expiry Date'][0], filter_contract['Lot Size'][0])
                else:
                    inst = Instrument(filter_contract['Exch'][0], filter_contract['Token'][0],
                                      filter_contract['Symbol'][0], filter_contract['Trading Symbol'][0], '',
                                      filter_contract['Lot Size'][0])
                return inst

    def get_instrument_by_token(self,exchange, token):
        try:
            contract = pd.read_csv("%s.csv" % exchange)
        except OSError as e:
            if e.errno == 2:
                self.get_contract_master(exchange)
                contract = pd.read_csv("%s.csv" % exchange)
            else:
                return self._error_response(e)
        if exchange == 'INDICES':
            filter_contract = contract[contract['token'] == token].reset_index(drop=False)
            inst = Instrument(filter_contract['exch'][0], filter_contract['token'][0], filter_contract['symbol'][0],'', '','')
            return inst
        else:
            filter_contract = contract[contract['Token'] == token]
            if len(filter_contract) == 0:
                return self._error_response("The symbol is not available in this exchange")
            else:
                filter_contract = filter_contract.reset_index()
                if 'expiry_date' in filter_contract:
                    inst = Instrument(filter_contract['Exch'][0], filter_contract['Token'][0], filter_contract['Symbol'][0],
                                      filter_contract['Trading Symbol'][0], filter_contract['Expiry Date'][0],
                                      filter_contract['Lot Size'][0])
                else:
                    inst = Instrument(filter_contract['Exch'][0], filter_contract['Token'][0], filter_contract['Symbol'][0],
                                      filter_contract['Trading Symbol'][0], '', filter_contract['Lot Size'][0])
                return inst

    def get_instrument_for_fno(self,exch,symbol, expiry_date,is_fut=True,strike=None,is_CE = False):
        # print(exch)
        if exch in ['NFO','CDS','MCX','BFO','BCD']:
            if exch == 'CDS':
                edate_format='%d-%m-%Y'
            else:
                edate_format = '%Y-%m-%d'
        else:
            return self._error_response("Invalid exchange")
        if not symbol:
            return self._error_response("Symbol is Null")
        try:
            expiry_date=datetime.strptime(expiry_date, "%Y-%m-%d").date()
        except ValueError as e:
            return self._error_response(e)
        if type(is_CE) is bool:
            if is_CE == True:
                option_type="CE"
            else:
                option_type="PE"
        else:
            return self._error_response("is_fut is not boolean value")
        # print(option_type)
        try:
            contract = pd.read_csv("%s.csv" % exch)
            # print(strike,is_fut)
        except OSError as e:
            if e.errno == 2:
                self.get_contract_master(exch)
                contract = pd.read_csv("%s.csv" % exch)
            else:
                return self._error_response(e)
        if is_fut == False:
            if strike:
                filter_contract = contract[(contract['Exch'] == exch)&((contract['Symbol'] == symbol)|(contract['Trading Symbol'] == symbol))&(contract['Option Type'] == option_type)&(contract['Strike Price'] == strike)&(contract['Expiry Date'] == expiry_date.strftime(edate_format))]
            else:
                filter_contract = contract[(contract['Exch'] == exch)&((contract['Symbol'] == symbol)|(contract['Trading Symbol'] == symbol))&(contract['Option Type'] == option_type)&(contract['Expiry Date'] == expiry_date.strftime(edate_format))]
        if is_fut == True:
            if strike == None:
                filter_contract = contract[(contract['Exch'] == exch)&((contract['Symbol'] == symbol)|(contract['Trading Symbol'] == symbol))&(contract['Option Type'] == 'XX')&(contract['Expiry Date'] == expiry_date.strftime(edate_format))]
            else:
                return self._error_response("No strike price for future")
        # print(len(filter_contract))
        if len(filter_contract) == 0:
            return self._error_response("No Data")
        else:
            inst=[]
            token=[]
            filter_contract = filter_contract.reset_index()
            for i in range(len(filter_contract)):
                if filter_contract['Token'][i] not in token:
                    token.append(filter_contract['Token'][i])
                    inst.append(Instrument(filter_contract['Exch'][i], filter_contract['Token'][i], filter_contract['Symbol'][i], filter_contract['Trading Symbol'][i], filter_contract['Expiry Date'][i],filter_contract['Lot Size'][i]))
            if len(inst) == 1:
                return inst[0]
            else:
                return inst

    def invalid_sess(self,session_ID):
        url = self.base_url + 'ws/invalidateSocketSess'
        headers = {
            'Authorization': 'Bearer ' + self.user_id + ' ' + session_ID,
            'Content-Type': 'application/json'
        }
        payload = {"loginType": "API"}
        datas = json.dumps(payload)
        response = requests.request("POST", url, headers=headers, data=datas)
        return response.json()

    def createSession(self,session_ID):
        url = self.base_url + 'ws/createSocketSess'
        headers = {
            'Authorization': 'Bearer ' + self.user_id + ' ' + session_ID,
            'Content-Type': 'application/json'
        }
        payload = {"loginType": "API"}
        datas = json.dumps(payload)
        response = requests.request("POST", url, headers=headers, data=datas)

        return response.json()

    def __ws_run_forever(self):
        while self.__stop_event.is_set() is False:
            try:
                self.ws.run_forever(ping_interval=3, ping_payload='{"t":"h"}',sslopt={"cert_reqs": ssl.CERT_NONE})
            except Exception as e:
                logger.warning(f"websocket run forever ended in exception, {e}")
            sleep(0.1)

    def on_message(self,ws, message):
        self.__subscribe_callback(message)
        data = json.loads(message)
        # if 's' in data and data['s'] == 'OK':
        #     self.ws_connection =True
        #     data = {
        #         "k": self.subscriptions,
        #         "t": 't',
        #         "m": "compact_marketdata"
        #     }
        #     ws.send(json.dumps(data))

    def on_error(self,ws, error):
        if (type(ws) is not websocket.WebSocketApp):  # This workaround is to solve the websocket_client's compatiblity issue of older versions. ie.0.40.0 which is used in upstox. Now this will work in both 0.40.0 & newer version of websocket_client
            error = ws
        if self.__on_error:
            self.__on_error(error)

    def on_close(self,*arguments, **keywords):
        self.ws_connection = False
        if self.__on_disconnect:
            self.__on_disconnect()

    def stop_websocket(self):
        self.ws_connection = False
        self.ws.close()
        self.__stop_event.set()

    def on_open(self,ws):
        initCon = {
            "susertoken": self.ENC,
            "t": "c",
            "actid": self.user_id + "_API",
            "uid": self.user_id + "_API",
            "source": "API"
        }
        self.ws.send(json.dumps(initCon))
        self.ws_connection = True
        if self.__on_open:
            self.__on_open()

    def subscribe(self, instrument):
        # print("Subscribed")
        scripts=""
        for __instrument in instrument:
            scripts=scripts+__instrument.exchange+"|"+str(__instrument.token)+"#"
        self.subscriptions = scripts[:-1]
        if self.market_depth:
            t = "d" # Subscribe Depth
        else:
            t= "t" # Subsribe token
        data = {
            "k": self.subscriptions,
            "t": t
        }
        # "m": "compact_marketdata"
        self.ws.send(json.dumps(data))

    def unsubscribe(self, instrument):
        # print("UnSubscribed")
        scripts = ""
        if self.subscriptions:
            split_subscribes = self.subscriptions.split('#')
        for __instrument in instrument:
            scripts = scripts + __instrument.exchange + "|" + str(__instrument.token) + "#"
            if self.subscriptions:
                split_subscribes.remove(__instrument.exchange + "|" + str(__instrument.token) )
        self.subscriptions=split_subscribes

        if self.market_depth:
            t = "ud"
        else:
            t= "u"

        data = {
            "k": scripts[:-1],
            "t": t
        }
        self.ws.send(json.dumps(data))

    def search_instruments(self,exchange,symbol):
        base_url=self.base_url.replace('/AliceBlueAPIService/api','')
        scrip_Url = base_url+"DataApiService/v2/exchange/getScripForSearchAPI"
        # print(scrip_Url)
        data = {'symbol':symbol, 'exchange': [exchange]}
        # print(data)
        scrip_response = self._dummypost(scrip_Url, data)
        if scrip_response ==[]:
            return self._error_response('Symbol not found')
        else:
            inst=[]
            for i in range(len(scrip_response)):
                # print(scrip_response[i])
                inst.append(Instrument(scrip_response[i]['exch'],scrip_response[i]['token'],scrip_response[i]['formattedInsName'],scrip_response[i]['symbol'],scrip_response[i]['expiry'],scrip_response[i]['lotSize']))
            return inst

    def start_websocket(self,socket_open_callback=None,socket_close_callback=None,socket_error_callback=None,subscription_callback=None,check_subscription_callback=None,run_in_background=False,market_depth=False):
        if check_subscription_callback != None:
            check_subscription_callback(self.script_subscription_instrument)
        session_request=self.session_id
        self.__on_open = socket_open_callback
        self.__on_disconnect = socket_close_callback
        self.__on_error = socket_error_callback
        self.__subscribe_callback=subscription_callback
        self.market_depth = market_depth
        if self.__stop_event != None and self.__stop_event.is_set():
            self.__stop_event.clear()
        if session_request:
            session_id = session_request
            sha256_encryption1 = hashlib.sha256(session_id.encode('utf-8')).hexdigest()
            self.ENC = hashlib.sha256(sha256_encryption1.encode('utf-8')).hexdigest()
            invalidSess = self.invalid_sess(session_id)
            if invalidSess['stat']=='Ok':
                print("STAGE 1: Invalidate the previous session :",invalidSess['stat'])
                createSess = self.createSession(session_id)
                if createSess['stat']=='Ok':
                    print("STAGE 2: Create the new session :", createSess['stat'])
                    print("Connecting to Socket ...")
                    self.__stop_event = threading.Event()
                    websocket.enableTrace(False)
                    self.ws = websocket.WebSocketApp(self._sub_urls['base_url_socket'],
                                                on_open=self.on_open,
                                                on_message=self.on_message,
                                                on_close=self.on_close,
                                                on_error=self.on_error)

                    # if run_in_background:
                    #         print("Running background!")
                    #         self.__ws_thread = threading.Thread(target=self.__ws_run_forever())
                    #         self.__ws_thread.daemon = True
                    #         self.__ws_thread.start()
                    # else:
                    #     try:
                    #         self.ws.run_forever(dispatcher=rel)  # Set dispatcher to automatic reconnection
                    #         rel.signal(2, rel.abort)  # Keyboard Interrupt
                    #         rel.dispatch()
                    #     except Exception as e:
                    #         print("Error:",e)
                    if run_in_background is True:
                        self.__ws_thread = threading.Thread(target=self.__ws_run_forever)
                        self.__ws_thread.daemon = True
                        self.__ws_thread.start()
                    else:
                        self.__ws_run_forever()

    def get_historical(self, instrument, from_datetime, to_datetime, interval, indices=False):
        # intervals = ["1", "D"]
        payload = json.dumps({"token": str(instrument.token),
                              "exchange": instrument.exchange if not indices else f"{instrument.exchange}::index",
                              "from": str(int(from_datetime.timestamp()))+'000',
                              "to": str(int(to_datetime.timestamp()))+'000',
                              "resolution": interval
                              })
        _headers = {
            "X-SAS-Version": "2.0",
            "User-Agent": self._user_agent(),
            "Authorization": self._user_authorization(),
            'Content-Type': 'application/json'
        }
        lst = requests.post(self.base_url+"chart/history", data=payload,headers=_headers)
        response=lst.json()
        if response['stat'] == 'Not_Ok':
            return response
        else:
            df = pd.DataFrame(lst.json()['result'])
            df = df.rename(columns={'time': 'datetime'})
            df = df[['datetime', 'open', 'high', 'low', 'close', 'volume']]
            return df

class Alice_Wrapper():
    def open_net_position(Net_position):
        open_net_position = [data for data in Net_position if data['Netqty'] != '0']
        return open_net_position

    def close_net_poition(Net_position):
        close_net_position = [data for data in Net_position if data['Netqty'] == '0']
        return close_net_position

    def subscription(script_list):
        if len(script_list) > 0:
            Aliceblue.script_subscription_instrument = script_list
            sub_prams=''
            # print(script_list)
            for i in range(len(script_list)):
                end_point = '' if i == len(script_list)-1 else '#'
                sub_prams=sub_prams+script_list[i].exchange+'|'+str(script_list[i].token)+end_point
            return sub_prams
        else:
            return {'stat':'Not_ok','emsg':'Script response is not fetched properly. Please check once'}

    def get_order_history(response):
        if response:
            pending = []
            completed = []
            for i in range(len(response)):
                data = {
                    "validity": response[i]['Validity'],
                    "user_order_id": response[i]['RequestID'],
                    "trigger_price": response[i]['Trgprc'],
                    "transaction_type": response[i]['Trantype'],
                    "trading_symbol": response[i]['Trsym'],
                    "remaining_quantity": response[i]['Unfilledsize'],
                    "rejection_reason": response[i]['RejReason'],
                    "quantity": response[i]['Qty'],
                    "product": response[i]['Pcode'],
                    "price": response[i]['Prc'],
                    "order_type": response[i]['Prctype'],
                    "order_tag": response[i]['remarks'],
                    "order_status": response[i]['Status'],
                    "order_entry_time": response[i]['iSinceBOE'],
                    "oms_order_id": response[i]['Nstordno'],
                    "nest_request_id": response[i]['RequestID'],
                    "lotsize": response[i]['multiplier'],
                    "login_id": response[i]['user'],
                    "leg_order_indicator": "",
                    "instrument_token": response[i]['token'],
                    "filled_quantity": response[i]['Fillshares'],
                    "exchange_time": response[i]['OrderedTime'],
                    "exchange_order_id": response[i]['ExchOrdID'],
                    "exchange": response[i]['Exchange'],
                    "disclosed_quantity": response[i]['Dscqty'],
                    "client_id": response[i]['accountId'],
                    "average_price": float(response[i]['Avgprc'])
                }
                if response[i]['Status'] == 'open':
                    pending.append(data)
                else:
                    completed.append(data)

            old_response = {
                "status": "success",
                "message": "",
                "data": {
                    "pending_orders": pending,
                    "completed_orders": completed
                }
            }
            return old_response
        else:
            return response

    def get_balance(response):
        cash_pos=[]
        for i in range(len(response)):
            data={
                            "utilized": {
                                "var_margin": response[i]['varmargin'],
                                "unrealised_m2m": response[i]['unrealizedMtomPrsnt'],
                                "span_margin": response[i]['spanmargin'],
                                "realised_m2m": response[i]['realizedMtomPrsnt'],
                                "premium_present": response[i]['premiumPrsnt'],
                                "pay_out": response[i]['payoutamount'],
                                "multiplier": response[i]['multiplier'],
                                "exposure_margin": response[i]['exposuremargin'],
                                "elm": response[i]['elm'],
                                "debits": response[i]['debits']
                            },
                            "segment": response[i]['segment'],
                            "net": response[i]['net'],
                            "category": response[i]['category'],
                            "available": {
                                "pay_in": response[i]['rmsPayInAmnt'],
                                "notionalCash": response[i]['notionalCash'],
                                "direct_collateral_value": response[i]['directcollateralvalue'],
                                "credits": response[i]['credits'],
                                "collateral_value": response[i]['collateralvalue'],
                                "cashmarginavailable": response[i]['cashmarginavailable'],
                                "adhoc_margin": response[i]['adhocMargin']
                            }
                        }
            cash_pos.append(data)
        if 'stat' not in response:
            old_response = {
                "status": "success",
                "message": "",
                "data": {
                    "cash_positions": cash_pos
                }
            }
            return old_response
        else:
            return response

    def get_profile(response):
        if 'stat' not in response:
            exch = response['exchEnabled']
            exch_enabled = []
            if '|' in exch:
                exchange = exch.split('|')
                for ex in exchange:
                    data = ex.split('_')[0].upper()
                    if data != '':
                        exch_enabled.append(data)
            else:
                exch_enabled.append(exch.split('_')[0].upper())
            old_response = {
                "status": "success",
                "message": "",
                "data": {
                    "phone": response['cellAddr'],
                    "pan_number": "",
                    "name": response['accountName'],
                    "login_id": response['accountId'],
                    "exchanges": exch_enabled,
                    "email_address": response['emailAddr'],
                    "dp_ids": [],
                    "broker_name": "ALICEBLUE",
                    "banks": [],
                    "backoffice_enabled": None
                }
            }
            return old_response
        else:
            return response

    def get_daywise_positions(response):
        if 'stat' not in response:
            true = True
            positions = []
            for i in range(len(response)):
                data = {
                    "total_buy_quantity": int(response[i]['Bqty']),
                    "instrument_token": response[i]['Token'],
                    "close_price_mtm": '',
                    "close_price": '',
                    "total_sell_quantity": int(response[i]['Sqty']),
                    "buy_amount_mtm": response[i]['Fillbuyamt'].replace(',', ''),
                    "average_sell_price": response[i]['Sellavgprc'],
                    "sell_amount": response[i]['Fillsellamt'],
                    "average_buy_price_mtm": response[i]['Buyavgprc'],
                    "oms_order_id": '',
                    "trading_symbol": response[i]['Tsym'],
                    "unrealised_pnl": response[i]['unrealisedprofitloss'],
                    "sell_amount_mtm": response[i]['Fillsellamt'],
                    "product": response[i]['Pcode'],
                    "cf_buy_quantity": '',
                    "enabled": '',
                    "cf_average_sell_price": '',
                    "average_buy_price": response[i]['Buyavgprc'],
                    "net_amount_mtm": response[i]['MtoM'],
                    "ltp": response[i]['LTP'],
                    "realised_pnl": response[i]['realisedprofitloss'],
                    "fill_id": response[i]['BEP'],
                    "cf_average_buy_price": '',
                    "cf_sell_quantity": '',
                    "bep": response[i]['BEP'],
                    "buy_amount": response[i]['Fillbuyamt'].replace(',', ''),
                    "client_id": response[i]['actid'],
                    "net_quantity": int(response[i]['Netqty']),
                    "average_sell_price_mtm": response[i]['Sellavgprc'],
                    "buy_quantity": response[i]['Bqty'],
                    "strike_price": response[i]['Stikeprc'],
                    "multiplier": '',
                    "net_amount": response[i]['Netamt'],
                    "exchange": response[i]['Exchange'],
                    "m2m": response[i]['MtoM'],
                    "sell_quantity": response[i]['Sqty']
                }
                positions.append(data)

            old_response = {
                "status": "success",
                "message": "",
                "data": {
                    "positions": positions
                }
            }
            return old_response

    def get_netwise_positions(response):
        if 'stat' not in response:
            positions = []
            true = True
            for i in range(len(response)):
                data = {
                    "total_buy_quantity": int(response[i]['Bqty']),
                    "instrument_token": response[i]['Token'],
                    "close_price_mtm": '',
                    "close_price": '',
                    "total_sell_quantity": int(response[i]['Sqty']),
                    "buy_amount_mtm": response[i]['Fillbuyamt'].replace(',', ''),
                    "average_sell_price": response[i]['Sellavgprc'],
                    "sell_amount": response[i]['Fillsellamt'],
                    "average_buy_price_mtm": response[i]['Buyavgprc'],
                    "oms_order_id": '',
                    "trading_symbol": response[i]['Tsym'],
                    "unrealised_pnl": response[i]['unrealisedprofitloss'],
                    "sell_amount_mtm": response[i]['Fillsellamt'],
                    "product": response[i]['Pcode'],
                    "cf_buy_quantity": '',
                    "enabled": '',
                    "cf_average_sell_price": '',
                    "average_buy_price": response[i]['Buyavgprc'],
                    "net_amount_mtm": response[i]['MtoM'],
                    "ltp": response[i]['LTP'],
                    "realised_pnl": response[i]['realisedprofitloss'],
                    "fill_id": response[i]['BEP'],
                    "cf_average_buy_price": '',
                    "cf_sell_quantity": '',
                    "bep": response[i]['BEP'],
                    "buy_amount": response[i]['Fillbuyamt'].replace(',', ''),
                    "client_id": response[i]['actid'],
                    "net_quantity": int(response[i]['Netqty']),
                    "average_sell_price_mtm": response[i]['Sellavgprc'],
                    "buy_quantity": response[i]['Bqty'],
                    "strike_price": response[i]['Stikeprc'],
                    "multiplier": '',
                    "net_amount": response[i]['Netamt'],
                    "exchange": response[i]['Exchange'],
                    "m2m": response[i]['MtoM'],
                    "sell_quantity": response[i]['Sqty']
                }
                positions.append(data)

            old_response = {
                "status": "success",
                "message": "",
                "data": {
                    "positions": positions
                }
            }
            return old_response

    def get_holding_positions(response):
        if response['stat'] == 'Ok':
            total_holdings = response['HoldingVal']
            holding = []
            client_id = response['clientid']
            for i in range(len(total_holdings)):
                data = {
                    "withheld_qty": total_holdings[i]['WHqty'],
                    "used_quantity": total_holdings[i]['Usedqty'],
                    "trading_symbol": total_holdings[i]['Bsetsym'] if total_holdings[i]['ExchSeg1'] == 'BSE' else total_holdings[i]['Nsetsym'],
                    "target_product": total_holdings[i]['Tprod'],
                    "t1_quantity": total_holdings[i]['SellableQty'],
                    "quantity": total_holdings[i]['Holdqty'],
                    "product": total_holdings[i]['Pcode'],
                    "price": total_holdings[i]['LTcse'],
                    "nse_ltp": total_holdings[i]['LTnse'],
                    "isin": total_holdings[i]['isin'],
                    "instrument_token": total_holdings[i]['Token1'],
                    "holding_update_quantity": total_holdings[i]['HUqty'],
                    "haircut": total_holdings[i]['Haircut'],
                    "exchange": total_holdings[i]['ExchSeg1'],
                    "collateral_update_quantity": total_holdings[i]['CUqty'],
                    "collateral_type": total_holdings[i]['Coltype'],
                    "collateral_quantity": total_holdings[i]['Colqty'],
                    "client_id": client_id,
                    "buy_avg_mtm": total_holdings[i]['pdc'],
                    "buy_avg": total_holdings[i]['Price'],
                    "bse_ltp": total_holdings[i]['LTbse']
                }
                holding.append(data)
            old_response = {
                "status": "success",
                "message": "",
                "data": {
                    "holdings": holding
                }
            }
            return old_response
        else:
            return response

    def place_order(response):
        if response[0]['stat']=='Ok':
            old_response = {'status': 'success', 'message': '', 'data': {'oms_order_id': response[0]['NOrdNo']}}
            return old_response
        else:
            return response

    def place_basket_order(response):
        Flag = 0
        for i in range(len(response)):
            if response[i]['stat'] == 'Ok':
                Flag = Flag + 1
        if Flag - len(response) == 0:
            old_response = {'status': 'success', 'message': 'Order placed successfully', 'data': {}}
            return old_response
        else:
            return response

    def modify_order(response):
        if response['stat'] == 'Ok':
            data = response['Result'].split(":")
            old_response = {'status': 'success', 'message': '', 'data': {'oms_order_id': [data[1]]}}
            return old_response
        else:
            return response

    def get_trade_book(response):
        if response:
            trades = []
            for i in range(len(response)):
                data = {
                    "user_order_id": response[i]['NOReqID'],
                    "transaction_type": response[i]['Trantype'],
                    "trading_symbol": response[i]['Tsym'],
                    "trade_price": float(response[i]['Price']),
                    "trade_id": response[i]['FillId'],
                    "product": response[i]['Pcode'],
                    "order_entry_time": response[i]['iSinceBOE'],
                    "oms_order_id": response[i]['Nstordno'],
                    "instrument_token": response[i]['Symbol'],
                    "filled_quantity": response[i]['Filledqty'],
                    "exchange_time": response[i]['Exchtime'],
                    "exchange_order_id": response[i]['ExchordID'],
                    "exchange": response[i]['Exchange']
                }
                trades.append(data)
            old_response = {
                "status": "success",
                "message": "",
                "data": {
                    "trades": trades
                }
            }
            return old_response
        else:
            return response

    def cancel_order(response):
        if 'stat' in response:
            if response['stat'] == 'Ok':
                old_response={'status': 'success', 'message': '', 'data': {'status': response['stat']}}
            else:
                old_response={'status': '', 'message': '', 'data': {'status': response['stat']}}
            return old_response
        else:
            return response
