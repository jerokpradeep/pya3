from pya3 import *
alice = Aliceblue(user_id='COD001',api_key='RXbK2LvJQCJbt8ixcKKQHUDJhNTsdzY0z1BeDeuifNpQnmfYBQUDbhx2qu68lo3kkVZk0G8uvGJeUs4icne1bCdD66GrtYx8nRVlbgBr4lJOx0ArOFDGb4eLHQx2j6cQ')
response = alice.get_session_id()
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
                     is_amo = False)
   )
