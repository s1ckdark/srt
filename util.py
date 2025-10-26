import argparse

def parse_cli_args():

    parser = argparse.ArgumentParser(description='')

    parser.add_argument("--user", help="Username", type=str, metavar="1234567890")
    parser.add_argument("--psw", help="Password", type=str, metavar="abc1234")
    parser.add_argument("--dpt", help="Departure Station", type=str, metavar="동탄")
    parser.add_argument("--arr", help="Arrival Station", type=str, metavar="동대구")
    parser.add_argument("--dt", help="Departure Date", type=str, metavar="20220118")
    parser.add_argument("--tm", help="Departure Time", type=str, metavar="08, 10, 12, ...")
    parser.add_argument("--adult", help="Number of Adults", type=int, metavar="2", default=1)
    parser.add_argument("--child", help="Number of Children", type=int, metavar="2", default=0)

    parser.add_argument("--num", help="no of trains to check", type=int, metavar="4", default=4)
    parser.add_argument("--reserve", help="Reserve or not", type=bool, metavar="2", default=False)
    parser.add_argument("--want_train", help="Train number", type=str, metavar="KTX 1234", default=None)

    args = parser.parse_args()

    return args
