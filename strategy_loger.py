import json
import datetime
import logging

class strategy_loger():

    def __init__(self, path, logger):
        self._file_Path = path + '/'
        self.logger = logger

    def create_strategy_log(self, new_strategy, new_strategy_id):
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

            with open(filename, 'w') as fp:
                json.dump(data, fp)
        except (ValueError, TypeError, ArithmeticError) as e:
                self.logger.exception(
                "Strategy logger failled to save Json file.")
                abort(http.HTTPStatus.BAD_REQUEST, str(e))




