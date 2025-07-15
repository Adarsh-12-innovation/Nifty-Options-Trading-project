import pandas as pd

from KiteAuto import kite_auth
from fileUtls import is_file_created_or_modified_today, read_from_pickle_file, write_to_pickle_file
from global_strings import kite_wd, nifty_nfo_instruments_file, options_csv, nfo_call_contracts, nfo_put_contracts, \
    full_call_csv, full_put_csv, nfo_call_min_expiry, call_csv, nfo_put_min_expiry, put_csv, call_dictionary, \
    put_dictionary


def get_nfo_instruments(kite):
    if is_file_created_or_modified_today(nifty_nfo_instruments_file):
        return pd.read_pickle(nifty_nfo_instruments_file)
    else:
        instruments_df = pd.DataFrame(kite.instruments(exchange="NFO"))
        instruments_df.to_pickle(nifty_nfo_instruments_file)
        instruments_df.to_csv(options_csv)
        return instruments_df


def get_call_put_contracts(kite):
    all_instruments_df = get_nfo_instruments(kite)
    if is_file_created_or_modified_today(nfo_call_contracts) and is_file_created_or_modified_today(nfo_put_contracts):
        return pd.read_pickle(nfo_call_contracts), pd.read_pickle(nfo_put_contracts)

    else:
        all_call_contracts = all_instruments_df[all_instruments_df['tradingsymbol'].str.startswith('NIFTY') & all_instruments_df['tradingsymbol'].str.endswith('CE')]
        all_call_contracts = all_call_contracts.reset_index(drop=True)
        all_call_contracts.to_pickle(nfo_call_contracts)
        all_call_contracts.to_csv(full_call_csv)

        all_put_contracts = all_instruments_df[all_instruments_df['tradingsymbol'].str.startswith('NIFTY') & all_instruments_df['tradingsymbol'].str.endswith('PE')]
        all_put_contracts = all_put_contracts.reset_index(drop=True)
        all_put_contracts.to_pickle(nfo_put_contracts)
        all_put_contracts.to_csv(full_put_csv)

        return all_call_contracts, all_put_contracts


def call_put_contracts_with_least_expiring_date(kite):

    if is_file_created_or_modified_today(nfo_call_min_expiry) and is_file_created_or_modified_today(nfo_put_min_expiry):
        return pd.read_pickle(nfo_call_min_expiry), pd.read_pickle(nfo_put_min_expiry)

    else:
        call_contracts, put_contracts = get_call_put_contracts(kite)

        min_expiry_date = call_contracts['expiry'].min()

        next_min_expiry_date = call_contracts['expiry'][call_contracts['expiry'] > min_expiry_date].min()

        call_contracts_min_expiry = call_contracts[call_contracts['expiry'] == next_min_expiry_date]
        call_contracts_min_expiry = call_contracts_min_expiry.reset_index(drop=True)
        call_contracts_min_expiry.to_pickle(nfo_call_min_expiry)
        call_contracts_min_expiry.to_csv(call_csv)

        min_expiry_date = put_contracts['expiry'].min()

        next_min_expiry_date = put_contracts['expiry'][put_contracts['expiry'] > min_expiry_date].min()

        put_contracts_min_expiry = put_contracts[put_contracts['expiry'] == next_min_expiry_date]
        put_contracts_min_expiry = put_contracts_min_expiry.reset_index(drop=True)
        put_contracts_min_expiry.to_pickle(nfo_put_min_expiry)
        put_contracts_min_expiry.to_csv(put_csv)

        return call_contracts_min_expiry, put_contracts_min_expiry


def get_dictionary_strike_price_instruments_min_expiry(kite):

    if is_file_created_or_modified_today(call_dictionary) and is_file_created_or_modified_today(put_dictionary):
        return read_from_pickle_file(call_dictionary), read_from_pickle_file(put_dictionary)
    else:
        call_contracts, put_contracts = call_put_contracts_with_least_expiring_date(kite)

        call_strike_dict = {int(row['strike']): row for index, row in call_contracts.iterrows()}
        write_to_pickle_file(call_dictionary, call_strike_dict)

        put_strike_dict = {int(row['strike']): row for index, row in put_contracts.iterrows()}
        write_to_pickle_file(put_dictionary, put_strike_dict)

        return call_strike_dict, put_strike_dict


if __name__ == "__main__":
    ##initialize kite api
    kite, api_key, access_token = kite_auth(kite_wd)
    get_dictionary_strike_price_instruments_min_expiry(kite)
