import time
import sys
import traceback
from KiteAuto import kite_auth, check_kite_validity, kite_auto_set, set_access_token
from Telegram_utls import send_telegram_message, build_and_run_app

sys.stdout = open('C:\\Users\\Administrator\\Downloads\\Nifty-project\\Task Scheduler Task Output logs\\output2.log',
                      'a')
sys.stderr = open('C:\\Users\\Administrator\\Downloads\\Nifty-project\\Task Scheduler Task Output logs\\error2.log',
                      'a')

if __name__ == "__main__":

    invalid = True
    msg = None
    count = 0
    while invalid:
        try:
            kite_, api_key_, access_token_ = kite_auth()
            if check_kite_validity(kite_):
                msg = "Access Token is Valid"
                invalid = False
            else:
                msg = "Access Token is Invalid"
        except Exception as e:
            msg = f"Access Token could not be checked because the following exception occurred\n {e}"
            print(traceback.format_exc())

        send_telegram_message(msg)

        count = count + 1

        if invalid:
            time.sleep(120)
            request_token, access_token = kite_auto_set()
            set_access_token(request_token, access_token)

        if count == 8:
            break


    if invalid:
        build_and_run_app(msg)
