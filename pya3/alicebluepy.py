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
    Normal = 'NRML'

def encrypt_string(hashing):
    sha = hashlib.sha256(hashing.encode()).hexdigest()
    return sha

class Aliceblue:
    base_url = "https://a3.aliceblueonline.com/rest/AliceBlueAPIService/api/"
    api_name = "Codifi API Connect - Python Lib "
    version = "1.0.16"
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
            "Authorization": self._user_authorization()
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
    def cancel_order(self, instrument,nestordernmbr):
        data = {'exch': instrument.exchange,
                'nestOrderNumber': nestordernmbr,
                'trading_symbol': instrument.name}
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
        except OSError as e:
            if e.errno == 2:
                self.get_contract_master(exchange)
                contract = pd.read_csv("%s.csv" % exchange)
            else:
                return {"stat":"Not_ok","emsg":e}
        if exchange == 'INDICES':
            filter_contract = contract[contract['symbol'] == symbol.upper()]
            if len(filter_contract) == 0:
                return {"stat": "Not_ok", "emsg": "The symbol is not available in this exchange"}
            else:
                filter_contract = filter_contract.reset_index()
                inst = Instrument(filter_contract['exch'][0], filter_contract['token'][0], filter_contract['symbol'][0],
                                  '', '', '')
                return inst
        else:
            filter_contract = contract[contract['Symbol'] == symbol.upper()]
            if len(filter_contract) == 0:
                return {"stat": "Not_ok", "emsg": "The symbol is not available in this exchange"}
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
                return {"stat":"Not_ok","emsg":e}
        if exchange == 'INDICES':
            filter_contract = contract[contract['token'] == token]
            inst = Instrument(filter_contract['exch'][0], filter_contract['token'][0], filter_contract['symbol'][0],'', '','')
            return inst
        else:
            filter_contract = contract[contract['Token'] == token]
            if len(filter_contract) == 0:
                return {"stat": "Not_ok", "emsg": "The symbol is not available in this exchange"}
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
        except OSError as e:
            if e.errno == 2:
                return {"stat": "Not_ok", "emsg": "Contract master is not available."}
            else:
                return {"stat":"Not_ok","emsg":e}
        if is_fut == False:
            if strike:
                filter_contract = contract[(contract['Exch'] == exch)&(contract['Symbol'] == symbol)&(contract['Option Type'] == option_type)&(contract['Strike Price'] == strike)&(contract['Expiry Date'] == expiry_date.strftime(edate_format))]
            else:
                filter_contract = contract[(contract['Exch'] == exch)&(contract['Symbol'] == symbol)&(contract['Option Type'] == option_type)&(contract['Expiry Date'] == expiry_date.strftime(edate_format))]
        if is_fut == True:
            if strike == None:
                filter_contract = contract[(contract['Exch'] == exch)&(contract['Symbol'] == symbol)&(contract['Option Type'] == 'XX')&(contract['Expiry Date'] == expiry_date.strftime(edate_format))]
            else:
                return {"stat": "Not_ok", "emsg": "No strike price for future"}
        # print(len(filter_contract))
        if len(filter_contract) == 0:
            return {"stat": "Not_ok", "emsg": "No Data"}
        else:
            inst=[]
            filter_contract = filter_contract.reset_index()
            for i in range(len(filter_contract)):
                inst.append(Instrument(filter_contract['Exch'][i], filter_contract['Token'][i], filter_contract['Symbol'][i], filter_contract['Trading Symbol'][i], filter_contract['Expiry Date'][i],filter_contract['Lot Size'][i]))
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
        self.ws.send(json.dumps(initCon))

    def search_instruments(self,exchange,symbol):
        base_url=self.base_url.replace('/AliceBlueAPIService/api','')
        scrip_Url = base_url+"DataApiService/v2/exchange/getScripForSearch"
        # print(scrip_Url)
        data = {'symbol':symbol, 'exchange': [exchange]}
        # print(data)
        scrip_response = self._dummypost(scrip_Url, data)
        if scrip_response ==[]:
            return {'stat':'Not_ok','emsg':'Symbol not found'}
        else:
            inst=[]
            for i in range(len(scrip_response)):
                # print(scrip_response[i])
                inst.append(Instrument(scrip_response[i]['exch'],scrip_response[i]['token'],scrip_response[i]['formattedInsName'],scrip_response[i]['symbol'],'',''))
            return inst

    def start_websocket(self,script_subscription):
        session_request=self.session_id
        if session_request:
            self.subscriptions= script_subscription
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
            # print(script_list)
            for i in range(len(script_list)):
                end_point = '' if i == len(script_list)-1 else '#'
                sub_prams=sub_prams+script_list[i].exchange+'|'+str(script_list[i].token)+end_point
            return sub_prams
        else:
            return {'stat':'Not_ok','emsg':'Script response is not fetched properly. Please check once'}

    def order_history(response_data):
        if response_data:
            old_response_data=[]
            for new_json in response_data:
                old_json = {
                    "validity": new_json['Validity'],
                    "trigger_price": new_json['Trgprc'],
                    "transaction_type": new_json['Trantype'],
                    "trading_symbol": new_json['Trsym'],
                    "rejection_reason": new_json['RejReason'],
                    "quantity": new_json['Qty'],
                    "product": new_json['Pcode'],
                    "price_to_fill": new_json['Prc'],
                    "order_status": new_json['Status'],
                    "oms_order_id": new_json['Nstordno'],
                    "nest_request_id": new_json['RequestID'],
                    "filled_quantity": new_json['Fillshares'],
                    "exchange_time": new_json['orderentrytime'],
                    "exchange_order_id": new_json['ExchOrdID'],
                    "exchange": new_json['Exchange'],
                    "disclosed_quantity": new_json['Dscqty'],
                    "client_id": new_json['user'],
                    "average_price": new_json['Avgprc'],
                    "order_tag":new_json['Remarks']
                }
                old_response_data.append(old_json)
            return old_response_data