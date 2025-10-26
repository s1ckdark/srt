""" Quickstart script for InstaPy usage """

# imports
from main import SRT
from util import parse_cli_args
from dotenv import load_dotenv
import os



if __name__ == "__main__":
    cli_args = parse_cli_args()

    dpt_stn = cli_args.dpt
    arr_stn = cli_args.arr
    dpt_dt = cli_args.dt
    dpt_tm = cli_args.tm
    adult_num = cli_args.adult
    child_num = cli_args.child

    num_trains_to_check = cli_args.num
    want_reserve = cli_args.reserve

    want_train = cli_args.want_train

    # Load environment variables from .env file
    load_dotenv()

    # Get login credentials from environment variables
    login_id = os.getenv('SRT_LOGIN_ID')
    login_psw = os.getenv('SRT_LOGIN_PASSWORD')
    
    # Get phone number from environment variable or set a default value
    phone_number = os.getenv('SRT_PHONE_NUMBER', 'YOUR_DEFAULT_PHONE_NUMBER')

    srt = SRT(dpt_stn, arr_stn, dpt_dt, dpt_tm, adult_num, child_num, num_trains_to_check, want_reserve, want_train)
    # Run the SRT script with the provided credentials
    srt.run(login_id, login_psw, phone_number)
