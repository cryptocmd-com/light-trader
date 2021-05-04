import os
import json
import http
import datetime
import logging
from copy import deepcopy
from quart import (Quart, abort, request, jsonify, url_for)

logger = logging.getLogger(__name__)


def datetime_to_name(t: datetime.datetime):
   return t.isoformat().split('+')[0].replace(':', '')

def make_journal_dir():
    startup_timestamp = datetime.datetime.now().isoformat()
    startup_timestamp = startup_timestamp.split('.')[0].replace(':', '')
    dirName = os.path.join('journal', str(startup_timestamp))
    os.mkdir(dirName)
    return dirName



class strategyJournal():

    def __init__(self, path):
        self._file_Path = path

    def create_strategy_journal(self, new_strategy, new_strategy_id):
        try:
            path = os.path.join(self._file_Path , str(new_strategy_id), "")
            os.mkdir(path)
            now =  datetime.datetime.now()
            filename = '{}.json'.format(datetime_to_name(now))
            data = {
                    "event" : "CREATED",
                    "timestamp" : now.isoformat(),
                    "state" : new_strategy.state   
            }

            with open(path + filename, 'wt') as fp:
                json.dump(data, fp)
        except (ValueError, TypeError, ArithmeticError) as e:
                logger.exception("Strategy StrategyJournal failled to save Json file.")
                abort(http.HTTPStatus.BAD_REQUEST, str(e))

    def update_strategy_status(self, strategy_id, new_status):
        try:
            path = os.path.join(self._file_Path , str(strategy_id), "")
            now = datetime.datetime.now()
            filename = '{}.json'.format(datetime_to_name(now))
            
            state = {}
            state['status'] = new_status

            strategy = {
                "event" : "STATUS_CHANGE",
                "timestamp" : now.isoformat(),
                "state" : state
            }

            with open(path + filename, 'wt') as fp:
                json.dump(strategy, fp)

        except (ValueError, TypeError, ArithmeticError) as e:
                logger.exception("StrategyJournal Could not update status in Json file.")
                abort(http.HTTPStatus.BAD_REQUEST, str(e))


dirName = make_journal_dir()
strategy_journal = strategyJournal(dirName)