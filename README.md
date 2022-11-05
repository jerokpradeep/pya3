
# Official Python SDK for Alice Blue API

The Official Python library for communicating with the Alice Blue APIs.

Alice Blue Python library provides an easy to use wrapper over the HTTPS APIs.

The HTTP calls have been converted to methods and JSON responses are wrapped into Python-compatible objects.


* __Author: [CodiFi](https://github.com/jerokpradeep)__
* **Current Version: 1.0.29**


## Installation

This module is installed via pip:

```
pip install pya3
```

To force upgrade existing installations:
```
pip uninstall pya3
pip --no-cache-dir install --upgrade pya3
```

### Prerequisites

Python >=3.7


## Getting started with API

### Overview
There is only two class in the whole library: `AliceBlue` and `Alice_Wrapper`. The `get_session_id` static method is used to retrieve a Session ID from the alice blue server. A Session ID is valid until the trading account logout.
With a Session ID, you can instantiate an AliceBlue object. Ideally you only need to create a Session ID once every time login the trading account with password. After you have the Session ID, you can store it
separately for re-use.

#### NOTE: User should Login through Web(ant.aliceblueonline.com) or SSO or Mobile at least once in a day, before connecting the API

### Rate Limits
The following are the rate limits for API users:
1. Orders - NOT LIMITED. Placing a new order, Modifying an existing order, square off positions and Cancelling an order are all not limited.
2. All other requests - Limited to 1800 requests per 15 minutes. This limit will be reset every 15 minutes to 1800 again.

**Note:** In order to make sure all clients requests are treated equally, AliceBlue has set up certain limits to the number of requests each client can make through API. 
### REST Documentation
The original REST API that this SDK is based on is available online.
   [Alice Blue API REST documentation](https://v2api.aliceblueonline.com)

## Using the API

### Get a Session ID
1. Import pya3
```python
from pya3 import *
```

### Create AliceBlue Object
1. You can create an AliceBlue object with your `UserID` and `API Key`.
```python
alice = Aliceblue(user_id='username',api_key='API_KEY')
```

2. You can get a Session ID by running following command. Store it once a day
```python
print(alice.get_session_id()) # Get Session ID
```

3. You can run commands here to check your connectivity
```python
print(alice.get_balance()) # get balance / margin limits
print(alice.get_profile()) # get profile
print(alice.get_daywise_positions()) # get daywise positions
print(alice.get_netwise_positions()) # get all netwise positions
print(alice.get_holding_positions()) # get holding positions
```
### Alice Wrapper
1. Check Net Position Wrapper (Open/Close) Position:
```
Net_position = alice.get_netwise_positions()

open_position= Alice_Wrapper.open_net_position(Net_position)
print("Open position :",open_position)

close_position = Alice_Wrapper.close_net_poition(Net_position)
print("Close position :",close_position)
```
2. Order History response wrapper:
```commandline
order_history_response = alice.get_order_history('')
print(Alice_Wrapper.get_order_history(order_history_response))
```

3. Balance response wrapper:
```commandline
get_balance_response=alice.get_balance()
print(Alice_Wrapper.get_balance(get_balance_response))
```

4. Profile response wrapper:
```commandline
get_profile_response=alice.get_profile()
print(Alice_Wrapper.get_profile(get_profile_response))
```

### Get master contracts

Getting master contracts allow you to search for instruments by symbol name and place orders.

Master contracts are stored as an CSV at local by token number and by symbol name. Whenever you get a trade update, order update, or quote update, the library will check if master contracts are loaded. If they are, it will attach the instrument object directly to the update. By default all master contracts of all enabled exchanges in your personal profile will be downloaded. i.e. If your profile contains the following as enabled exchanges `['NSE','CDS', 'BSE','BFO', 'MCX', NFO','INDICES']` all contract notes of all exchanges will be downloaded by default. If you feel it takes too much time to download all exchange, or if you don't need all exchanges to be downloaded, you can specify which exchange to download contract notes while creating the AliceBlue object.


```python
alice.get_contract_master("MCX")
alice.get_contract_master("NFO")
alice.get_contract_master("NSE")
alice.get_contract_master("BSE")
alice.get_contract_master("CDS")
alice.get_contract_master("BFO")
alice.get_contract_master("INDICES")
```

This will reduce a few milliseconds in object creation time of AliceBlue object.

### Get tradable instruments
Symbols can be retrieved in multiple ways. Once you have the master contract loaded for an exchange, you can get an instrument in many ways.

Get a single instrument by it's name:
```python
print(alice.get_instrument_by_symbol('NSE','ONGC'))
print(alice.get_instrument_by_symbol('BSE','TATASTEEL'))
print(alice.get_instrument_by_symbol('MCX','GOLDM'))
print(alice.get_instrument_by_symbol('INDICES','NIFTY 50'))
print(alice.get_instrument_by_symbol('INDICES','NIFTY BANK'))
```

Get a single instrument by it's token number (generally useful only for BSE Equities):
```python
print(alice.get_instrument_by_token("MCX",239484))
print(alice.get_instrument_by_token('BSE',500325))
print(alice.get_instrument_by_token('NSE',22))
print(alice.get_instrument_by_token('INDICES',26000)) # Nifty Indices
print(alice.get_instrument_by_token('INDICES',26009)) # Bank Nifty
```

Get FNO instruments easily by mentioning expiry, strike & call or put.

```python
print(alice.get_instrument_for_fno(exch="NFO",symbol='BANKNIFTY', expiry_date="2022-09-25", is_fut=True,strike=None, is_CE=False))
print(alice.get_instrument_for_fno(exch="NFO",symbol='BANKNIFTY', expiry_date="2022-09-04", is_fut=False,strike=37700, is_CE=False))
print(alice.get_instrument_for_fno(exch="NFO",symbol='BANKNIFTY', expiry_date="2022-09-04", is_fut=False,strike=37700, is_CE=True))
print(alice.get_instrument_for_fno(exch="CDS",symbol='USDINR', expiry_date="2022-09-16", is_fut=True,strike=None, is_CE=False))
print(alice.get_instrument_for_fno(exch="CDS",symbol='USDINR', expiry_date="2022-09-23", is_fut=False,strike=79.50000, is_CE=False))
print(alice.get_instrument_for_fno(exch="CDS",symbol='USDINR', expiry_date="2022-09-28", is_fut=False,strike=79.50000, is_CE=True))
```

### Search for symbols
Search for multiple instruments by matching the name. This works case insensitive and returns all instrument which has the name in its symbol. It does not require contract master file.
```python
all_sensex_scrips = alice.search_instruments('BSE', 'SENSEX')
print(all_sensex_scrips)
```
The above code results multiple symbol which has 'sensex' in its symbol.


#### Instrument object

Instruments are represented by instrument objects. These are named-tuples that are created while getting the master contracts. They are used when placing an order and searching for an instrument. The structure of an instrument tuple is as follows:

```python

Instrument = namedtuple('Instrument', ['exchange', 'token', 'symbol','name', 'expiry', 'lot_size'])

```


All instruments have the fields mentioned above. Wherever a field is not applicable for an instrument (for example, equity instruments don't have strike prices), that value will be `None`


### Place an order
Place limit, market, SL, SL-M, AMO, BO, CO orders

```python
# TransactionType.Buy, OrderType.Market, ProductType.Delivery

print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%1%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
print(
   alice.place_order(transaction_type = TransactionType.Buy,
                     instrument = alice.get_instrument_by_symbol('NSE', 'INFY'),
                     quantity = 1,
                     order_type = OrderType.Market,
                     product_type = ProductType.Delivery,
                     price = 0.0,
                     trigger_price = None,
                     stop_loss = None,
                     square_off = None,
                     trailing_sl = None,
                     is_amo = False,
                     order_tag='order1')
   )

# TransactionType.Buy, OrderType.Market, ProductType.Intraday

print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%2%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
print(
   alice.place_order(transaction_type = TransactionType.Buy,
                     instrument = alice.get_instrument_by_symbol('NSE', 'INFY'),
                     quantity = 1,
                     order_type = OrderType.Market,
                     product_type = ProductType.Intraday,
                     price = 0.0,
                     trigger_price = None,
                     stop_loss = None,
                     square_off = None,
                     trailing_sl = None,
                     is_amo = False,
                     order_tag='order1')
)

# TransactionType.Buy, OrderType.Market, ProductType.CoverOrder

print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%3%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
print(
   alice.place_order(transaction_type = TransactionType.Buy,
                     instrument = alice.get_instrument_by_symbol('NSE', 'INFY'),
                     quantity = 1,
                     order_type = OrderType.Market,
                     product_type = ProductType.CoverOrder,
                     price = 0.0,
                     trigger_price = 7.5, # trigger_price Here the trigger_price is taken as stop loss (provide stop loss in actual amount)
                     stop_loss = None,
                     square_off = None,
                     trailing_sl = None,
                     is_amo = False,
                     order_tag='order1')
)


# TransactionType.Buy, OrderType.Limit, ProductType.BracketOrder
# OCO Order can't be of type market

print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%4%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
print(
   alice.place_order(transaction_type = TransactionType.Buy,
                     instrument = alice.get_instrument_by_symbol('NSE', 'INFY'),
                     quantity = 1,
                     order_type = OrderType.Limit,
                     product_type = ProductType.BracketOrder,
                     price = 8.0,
                     trigger_price = None,
                     stop_loss = 6.0,
                     square_off = 10.0,
                     trailing_sl = None,
                     is_amo = False,
                     order_tag='order1')
)

# TransactionType.Buy, OrderType.Limit, ProductType.Intraday

print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%5%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
print(
   alice.place_order(transaction_type = TransactionType.Buy,
                     instrument = alice.get_instrument_by_symbol('NSE', 'INFY'),
                     quantity = 1,
                     order_type = OrderType.Limit,
                     product_type = ProductType.Intraday,
                     price = 8.0,
                     trigger_price = None,
                     stop_loss = None,
                     square_off = None,
                     trailing_sl = None,
                     is_amo = False,
                     order_tag='order1')
)


# TransactionType.Buy, OrderType.Limit, ProductType.CoverOrder

print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%6%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
print(
   alice.place_order(transaction_type = TransactionType.Buy,
                     instrument = alice.get_instrument_by_symbol('NSE', 'INFY'),
                     quantity = 1,
                     order_type = OrderType.Limit,
                     product_type = ProductType.CoverOrder,
                     price = 7.0,
                     trigger_price = 6.5, # trigger_price Here the trigger_price is taken as stop loss (provide stop loss in actual amount)
                     stop_loss = None,
                     square_off = None,
                     trailing_sl = None,
                     is_amo = False,
                     order_tag='order1')
)

###############################

# TransactionType.Buy, OrderType.StopLossMarket, ProductType.Delivery

print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%7%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
print(
   alice.place_order(transaction_type = TransactionType.Buy,
                     instrument = alice.get_instrument_by_symbol('NSE', 'INFY'),
                     quantity = 1,
                     order_type = OrderType.StopLossMarket,
                     product_type = ProductType.Delivery,
                     price = 0.0,
                     trigger_price = 8.0,
                     stop_loss = None,
                     square_off = None,
                     trailing_sl = None,
                     is_amo = False,
                     order_tag='order1')
)


# TransactionType.Buy, OrderType.StopLossMarket, ProductType.Intraday

print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%8%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
print(
   alice.place_order(transaction_type = TransactionType.Buy,
                     instrument = alice.get_instrument_by_symbol('NSE', 'INFY'),
                     quantity = 1,
                     order_type = OrderType.StopLossMarket,
                     product_type = ProductType.Intraday,
                     price = 0.0,
                     trigger_price = 8.0,
                     stop_loss = None,
                     square_off = None,
                     trailing_sl = None,
                     is_amo = False,
                     order_tag='order1')
)



# TransactionType.Buy, OrderType.StopLossMarket, ProductType.CoverOrder
# CO order is of type Limit and And Market Only

# TransactionType.Buy, OrderType.StopLossMarket, ProductType.BO
# BO order is of type Limit and And Market Only

###################################

# TransactionType.Buy, OrderType.StopLossLimit, ProductType.Delivery

print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%9%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
print(
   alice.place_order(transaction_type = TransactionType.Buy,
                     instrument = alice.get_instrument_by_symbol('NSE', 'INFY'),
                     quantity = 1,
                     order_type = OrderType.StopLossMarket,
                     product_type = ProductType.Delivery,
                     price = 8.0,
                     trigger_price = 8.0,
                     stop_loss = None,
                     square_off = None,
                     trailing_sl = None,
                     is_amo = False,
                     order_tag='order1')
)


# TransactionType.Buy, OrderType.StopLossLimit, ProductType.Intraday

print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%10%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
print(
   alice.place_order(transaction_type = TransactionType.Buy,
                     instrument = alice.get_instrument_by_symbol('NSE', 'INFY'),
                     quantity = 1,
                     order_type = OrderType.StopLossLimit,
                     product_type = ProductType.Intraday,
                     price = 8.0,
                     trigger_price = 8.0,
                     stop_loss = None,
                     square_off = None,
                     trailing_sl = None,
                     is_amo = False,
                     order_tag='order1')
)



# TransactionType.Buy, OrderType.StopLossLimit, ProductType.CoverOrder
# CO order is of type Limit and And Market Only


# TransactionType.Buy, OrderType.StopLossLimit, ProductType.BracketOrder

print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%11%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
print(
   alice.place_order(transaction_type = TransactionType.Buy,
                     instrument = alice.get_instrument_by_symbol('NSE', 'INFY'),
                     quantity = 1,
                     order_type = OrderType.StopLossLimit,
                     product_type = ProductType.BracketOrder,
                     price = 8.0,
                     trigger_price = 8.0,
                     stop_loss = 1.0,
                     square_off = 1.0,
                     trailing_sl = 20,
                     is_amo = False,
                     order_tag='order1')
)
```

### Place basket order
Basket order is used to buy or sell group of securities simultaneously.
```python
order1 = {  "instrument"        : alice.get_instrument_by_symbol('NSE', 'INFY'),
            "order_type"        : OrderType.Market,
            "quantity"          : 1,
            "transaction_type"  : TransactionType.Buy,
            "product_type"      : ProductType.Delivery,
            "order_tag"         : "Order1"}
order2 = {  "instrument"        : alice.get_instrument_by_symbol('NSE', 'SBIN'),
            "order_type"        : OrderType.Limit,
            "quantity"          : 2,
            "price"             : 280.0,
            "transaction_type"  : TransactionType.Sell,
            "product_type"      : ProductType.Intraday,
            "order_tag"         : "Order2"}
orders = [order1, order2]
print(alice.place_basket_order(orders))
```

### Websocket
Connect the Websocket and subscribe script. To get market depth please set market_depth as `True`
```python
LTP = 0
socket_opened = False
subscribe_flag = False
subscribe_list = []
unsubscribe_list = []

def socket_open():  # Socket open callback function
    print("Connected")
    global socket_opened
    socket_opened = True
    if subscribe_flag:  # This is used to resubscribe the script when reconnect the socket.
        alice.subscribe(subscribe_list)

def socket_close():  # On Socket close this callback function will trigger
    global socket_opened, LTP
    socket_opened = False
    LTP = 0
    print("Closed")

def socket_error(message):  # Socket Error Message will receive in this callback function
    global LTP
    LTP = 0
    print("Error :", message)

def feed_data(message):  # Socket feed data will receive in this callback function
    global LTP, subscribe_flag
    feed_message = json.loads(message)
    if feed_message["t"] == "ck":
        print("Connection Acknowledgement status :%s (Websocket Connected)" % feed_message["s"])
        subscribe_flag = True
        print("subscribe_flag :", subscribe_flag)
        print("-------------------------------------------------------------------------------")
        pass
    elif feed_message["t"] == "tk":
        print("Token Acknowledgement status :%s " % feed_message)
        print("-------------------------------------------------------------------------------")
        pass
    else:
        print("Feed :", feed_message)
        LTP = feed_message[
            'lp'] if 'lp' in feed_message else LTP  # If LTP in the response it will store in LTP variable

# Socket Connection Request
alice.start_websocket(socket_open_callback=socket_open, socket_close_callback=socket_close,
                      socket_error_callback=socket_error, subscription_callback=feed_data, run_in_background=True,market_depth=False)

while not socket_opened:
    pass

subscribe_list = [alice.get_instrument_by_token('INDICES', 26000)]
alice.subscribe(subscribe_list)
print(datetime.now())
sleep(10)
print(datetime.now())
# unsubscribe_list = [alice.get_instrument_by_symbol("NSE", "RELIANCE")]
# alice.unsubscribe(unsubscribe_list)
# sleep(8)

# Stop the websocket
alice.stop_websocket()
sleep(10)
print(datetime.now())

# Connect the socket after socket close
alice.start_websocket(socket_open_callback=socket_open, socket_close_callback=socket_close,
                      socket_error_callback=socket_error, subscription_callback=feed_data, run_in_background=True)

```

### Modify an order

```python
print(
   alice.modify_order(transaction_type = TransactionType.Buy,
                     instrument = alice.get_instrument_by_token('MCX', 242508),
                     order_id="220803000207716",
                     quantity = 1,
                     order_type = OrderType.Limit,
                     product_type = ProductType.Delivery,
                     price=30.0,
                     trigger_price = None)
)
```

### Cancel an order

```python
print(alice.cancel_order('191015000018737')) #Cancel an open order
print(alice.cancel_order('220803000207716')) #Cancel an open order
```

### Getting order history and trade details

#### Get order history of a particular order
```python
print(alice.get_order_history('220803000207716'))
```

#### Get order history of all orders.
```python
print(alice.get_order_history(''))
```

#### Get trade book
```python
print(alice.get_trade_book())
```

#### Get Script Info
Get Current OHLC, Upper and Lower circuit data
```python
print(alice.get_scrip_info(alice.get_instrument_by_token('MCX', 242508)))
```

#### Get Historical Data
Get Historical data of Open, High, Low, Close and Volume of Minutes, Day and Month.
```python
from datetime import datetime

alice = Aliceblue(user_id='',api_key='')

instrument = alice.get_instrument_by_symbol("NFO", "RELIANCE")
from_datetime = datetime.now() - datetime.timedelta(days=7)     # From last & days
to_datetime = datetime.now()                                    # To now
interval = "1"       # ["1", "D"]
indices = False      # For Getting index data
print(alice.get_historical(instrument, from_datetime, to_datetime, interval, indices))

```

### Order properties as enums
Order properties such as TransactionType, OrderType, and others have been safely classified as enums so you don't have to write them out as strings

#### TransactionType
Transaction types indicate whether you want to buy or sell. Valid transaction types are of the following:

* `TransactionType.Buy` - buy
* `TransactionType.Sell` - sell

#### OrderType
Order type specifies the type of order you want to send. Valid order types include:

* `OrderType.Market` - Place the order with a market price
* `OrderType.Limit` - Place the order with a limit price (limit price parameter is mandatory)
* `OrderType.StopLossLimit` - Place as a stop loss limit order
* `OrderType.StopLossMarket` - Place as a stop loss market order

#### ProductType
Product types indicate the complexity of the order you want to place. Valid product types are:

* `ProductType.Intraday` - Intraday order that will get squared off before market close
* `ProductType.Delivery` - Delivery order that will be held with you after market close
* `ProductType.CoverOrder` - Cover order
* `ProductType.BracketOrder` - One cancels other order. Also known as bracket order


## Read this before creating an issue
Before creating an issue in this library, please follow the following steps.

1. Search the problem you are facing is already asked by someone else. There might be some issues already there, either solved/unsolved related to your problem. Go to [issues](https://github.com/jerokpradeep/pya3/issues)
2. If you feel your problem is not asked by anyone or no issues are related to your problem, then create a new issue.
3. Describe your problem in detail while creating the issue. If you don't have time to detail/describe the problem you are facing, assume that I also won't be having time to respond to your problem.
4. Post a sample code of the problem you are facing. If I copy paste the code directly from issue, I should be able to reproduce the problem you are facing.
5. Before posting the sample code, test your sample code yourself once. Only sample code should be tested, no other addition should be there while you are testing.
6. Have some print() function calls to display the values of some variables related to your problem.
7. Post the results of print() functions also in the issue.
8. Use the insert code feature of github to inset code and print outputs, so that the code is displayed neat. ![image](https://user-images.githubusercontent.com/38440742/85207234-4dc96f80-b2f5-11ea-990c-df013dd69cf2.png)
9. If you have multiple lines of code, use triple grave accent ( ``` ) to insert multiple lines of code. [Example:](https://docs.github.com/en/github/writing-on-github/creating-and-highlighting-code-blocks) ![image](https://user-images.githubusercontent.com/38440742/89105781-343a3e00-d3f2-11ea-9f86-92dda88aa5bf.png)

