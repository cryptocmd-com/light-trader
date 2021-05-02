import os
import json
import http
import datetime
import logging
from copy import deepcopy
from quart import (Quart, abort, request, jsonify, url_for)

logger = logging.getLogger(__name__)



def make_journal_dir():
    startup_timestamp = datetime.datetime.timestamp(datetime.datetime.now())
    dirName = 'history/' + str(startup_timestamp)
    os.mkdir(dirName)
    return dirName



class strategyJournal():

    def __init__(self, path):
        self._file_Path = path + '/'

    def create_strategy_journal(self, new_strategy, new_strategy_id):
        try:
            filename = self._file_Path + str(new_strategy_id) + '.json'
            now = datetime.datetime.now()
            data = {
                datetime.datetime.timestamp(now) : {
                    "event" : "CREATED",
                    "date" : str(now),
                    "state" : new_strategy.state
                }
                
            }

            with open(filename, 'wt') as fp:
                json.dump(data, fp)
        except (ValueError, TypeError, ArithmeticError) as e:
                logger.exception("Strategy StrategyJournal failled to save Json file.")
                abort(http.HTTPStatus.BAD_REQUEST, str(e))

    def update_strategy_status(self, strategy_id, new_status):
        try:
            now = datetime.datetime.now()
            filename = self._file_Path + str(strategy_id) + '.json'
            with open(filename, 'rt') as json_file:
                strategy = json.load(json_file)
            
            last_update = list(strategy.keys())[-1]
            last_state = deepcopy(strategy[last_update]['state'])
            last_state['status'] = new_status

            strategy[str(datetime.datetime.timestamp(now))] = {
                "event" : "STATUS_CHANGE",
                "date" : str(now),
                "state" : last_state
            }

            with open(filename, 'wt') as fp:
                json.dump(strategy, fp)

        except (ValueError, TypeError, ArithmeticError) as e:
                logger.exception("StrategyJournal Could not update status in Json file.")
                abort(http.HTTPStatus.BAD_REQUEST, str(e))




dirName = make_journal_dir()
strategy_journal = strategyJournal(dirName)