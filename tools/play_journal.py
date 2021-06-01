import glob
import json
import os.path
import argparse
import iso8601
import toml
import requests
from decimal import Decimal

def parse_args():
    args = argparse.ArgumentParser()
    args.add_argument(
        '--journal', '-j',
        required=True,
        metavar='journal_dir',
        help='Journal directory, point the folder name. Example: .../python play_journal -j journal'
    )
    args.add_argument(
        '--dry', '-d',
        action='store_true',
        help='Dry-run, prints all the strategies without sending them. '
    )
    args.add_argument(
        '--time', '-t',
        metavar='launch_time',
        help='Journal starting at a particular time. Example: .../python play_journal -j journal -t 2021-05-05T124017'
    )
    args.add_argument(
        '--all', '-a',
        action='store_true',
        help='Write all strategy states. Useless right now.'
    )

    return args.parse_args()


def _get_highest_sorted_filename(
    listing: list,
    name_filter=(lambda _: True)
) -> str:
    for f in sorted(listing, reverse=True):
        if name_filter(f):
            return f

    return None


def _is_valid_date(s: str) -> bool:
    try:
        iso8601.parse_date(s)
        return True
    except iso8601.ParseError:
        return False


def _get_launch_dir(
    journal_name: str,
    name: str
) -> str:
    wildcard = os.path.join(
        journal_name, name or '*')
    
    dir_names = glob.glob(wildcard)
    latest_dir_name = _get_highest_sorted_filename(
        dir_names,
        lambda d: _is_valid_date(os.path.basename(d))
    )
    if latest_dir_name is None:
        raise RuntimeError(f"No directory matching '{wildcard}'")

    return latest_dir_name


def _get_latest_strategy_states(
    journal_name: str,
    launch_id: str
) -> list:
    launch_dir = _get_launch_dir(
        journal_name, launch_id
    )
    strategy_subdirs = glob.glob(
        os.path.join(launch_dir, '*'))

    latest_file_for_strategy = [
        _get_highest_sorted_filename(
            glob.glob(os.path.join(dir_name, '*'))
        ) for dir_name in strategy_subdirs
    ]

    return [
        json.load(open(f_name, 'rt'))
        for f_name in latest_file_for_strategy
        if f_name is not None
    ]


def read_config():
    config_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    config_path = os.path.join(config_dir, 'config.toml')
    return toml.load(config_path)


def send_req_to_light_trader(req):
    config = read_config()
    return requests.post('http://localhost:5000/strategy_advice/telegram/', json = req, auth=('telegram', 'qawsed'))


def main():
    args = parse_args()
    for state in _get_latest_strategy_states(
        args.journal, args.time
    ):
        # TODO: This should be the behavior only when both
        # the dry-run and write all strategy states flags are set.
        if args.dry:
            print('POST', json.dumps(state, indent=2))
            req = state['state']
            del req['strategy_id']

        else:
            req = state['state']
            if (req['status'] == 'ACTIVE' or 
                req['status'] == 'PAUSED' or
                (req['status'] == 'STOPPED' and Decimal(req['position']) != 0)
                ):
                del req['strategy_id']
                print(req)
                r = send_req_to_light_trader(req=req)
                print('Code: {}.\nText: {}.\n'.format(r.status_code,r.text))

            
            


# Note: this is a very early version of the script, which can only run in "dry-run"
# mode. To run it: tools/play_journal.py -j <journal dir>

if __name__ == '__main__':
    main()
