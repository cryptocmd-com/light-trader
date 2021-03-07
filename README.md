# LightTrader: A customizable trading bot for the Binance exchange

## General

LightTrader is a simple trading bot for the Binance exchange. It subscribes to
live candle data for instruments, and executes strategies. Currently,
there's little support for position management, so the strategies should enter
position at market price, and specify take-profit and stop-loss prices,
which are sent to the exchange as soon as the position is entered successfully.

LightTrader is meant to be controlled via an API, which allows strategies to be
set-up on the fly.

## Setup

To run LightTrader on your environment:

* Set-up a and activate a virtual environment

```bash
python3 -m venv .venv
# Example for Bash, if using Windows CMD run the appropriate command for it
. .venv/bin/activate
```

* Install the dependencies

```bash
pip3 install -r requirements.txt
```

* Set up the credentials for the server
  * Obtain Binance credentials. For testing and integration it's strongly advised
  to start with test credentials from https://dev.binance.vision
* Copy `examples/config.toml` to `config.toml` and customize it.
  * Leave the connection setting as test, or change to 'live' if you want that.
  * Set `api_key` and `api_secret` to the value of an API key for
  the Binance environment you're using.
  * Define user-names and their corresponding passwords in the `user_passwords`
  section. Specifically, define the password for the user `telegram`.
  Optionally you may define other user-names in the same format. 
* Set-up the credentials to be used for exercising the server
  * In the `examples/` subdirectory copy .env.example to .env
  * Set the TELEGRAM_USER_PASSWORD to the same value as the
  password you set for the `telegram` user in the `[user_passwords]`
  section of `config.toml`
* Customize the log level if necessary, by setting the `level` entry
  in the `logging` section of `config.toml`.
  For an example you can consult `examples/config.toml`.
* Add the directory for this project to your Visual Studio Code
  workspace.
* Install the _REST Client_ extension for Visual Studio Code.

## Running

* In the debugging view choose the _Python: Quart_ for this project,
and run. You should see some log messages.
* Open `examples/api_examples.http` and run some requests. Specifically,
send POST requests to the `strategy_advice/telegram/` endpoint, which initializes
some trading strategies. You should see your requests accepted with status 200/201
or rejected with error messages, according to the descriptions in the comments.

###  Executing a strategy which typically trades on the test exchange

This procedure can be used to set-up a strategy which typically trades every
few minutes on the Binance test exchange.

* Set-up debug logging as explained above. This isn't necessary but provides
  better observability.
* Start the server.
* Open `examples/api_examples.http` and run the _Long BNBUSDT_ example. This will start
  a first strategy, and register for market-data on BNBUSDT.
* Open `examples/adaptive_strategy.http` and run the first example.
  If no candle is shown, repeat until a candle is shown.
* Run the second example in `examples/adaptive_strategy.http`.
  This creates a strategy based on the values of the candle. If you
  get an error that either the stop-loss or the take-profit prices
  equal the entry price, run the first example again until you get
  a new candle, and then repeat this stage.
* Follow the log messages. Within a few minutes the strategy you
  just created should see indications that the strategy opened and
  closed positions.

### Running in production

For production use, the [Hypercorn](https://gitlab.com/pgjones/hypercorn) server is recommended.
To invoke it on the default port, which is 8000, and accept
connections from outside:

```bash
hypercorn -b 0.0.0.0 app:app
```

It's possible to specify a custom port, e.g. to use port 5000:

```bash
hypercorn -b 0.0.0.0:5000 app:app
```

## Monitoring

We use _uptimerobot.com_ to verify that our service is up.
Since this is a cloud service, we need to make our trading server accessible
using a public hostname. To set that up:

* Set-up a publicly accessible URL for the server. This could be done by running
  a the cloud server, or using a tool like _ngrok_. Please note, that
  when started in development mode from VS Code,
  the trading server listens on port 5000 by default.
* Ensure you can access the _/status_ endpoint. E.g., if the hostname
  is: _https://47bcab0f0c3f.ngrok.io/_ then the status endpoint is
  _https://47bcab0f0c3f.ngrok.io/status_. It should return a JSON
  object like this:

```JSON
{"overall":"ok"}
```

* Open an account on https://uptimerobot.com
* Set-up a monitor for the status endpoint. You should see in the
  logging messages indications of HTTP HEAD requests to the URL
  every 5 minutes.
* Indicate your e-mail address as the address for alerts. Ensure
  you get an alert when you take the server down and another one
  when you start it again.
  If you want _uptimerobot.com_ to stop alerting, you can pause
  the monitor. To monitor again, you can start it.
