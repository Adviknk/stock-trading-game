from flask import Flask, render_template, request, redirect, session
from sqlHelper import *
from finance import *
from timing import *

app = Flask(__name__)
app.secret_key = 'your_secret_key'


@app.route("/")
@app.route("/home")
@app.route("/home/<username>")
def home(username=''):
    load_users()
    if 'username' in session:
        return render_template('home.html', username=session['username'])
    else:
        return render_template('home.html', username='')


@app.route("/explore")
@app.route("/explore/<username>")
def explore(username=''):
    if 'username' in session:
        return render_template('explore.html', username=session['username'])
    else:
        return render_template('explore.html', username='')


@app.route("/leagues")
@app.route("/leagues/<username>")
def leagues(username=''):
    if 'username' in session:
        user_leagues = get_leagues(username=session['username'])
        return render_template('league-home.html', username=session['username'], all_leagues=user_leagues)
    else:
        return redirect('/login')


@app.route("/account")
@app.route("/account/<username>")
def account(username=''):
    if 'username' in session:
        return render_template('account.html', username=session['username'])
    else:
        return redirect('/login')


@app.route("/login", methods=["GET", "POST"])
def log_in():
    if 'username' in session:
        return redirect('/account')

    if request.method == "GET":
        return render_template("log-in.html")

    if request.method == "POST":
        user_name = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if not authenticate(username=user_name, email=email, password=password):
            return render_template("login-error.html", error='invalid input')

        session['username'] = user_name
        return redirect('/account/' + user_name)


@app.route("/signup", methods=["GET", "POST"])
def sign_up():
    if 'username' in session:
        return redirect('/account')

    if request.method == "GET":
        return render_template("sign-up.html")

    if request.method == "POST":
        first = request.form.get('first')
        last = request.form.get('last')
        user_name = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if user_name == '' or first == '' or last == '' or email == '' or password == '':
            return render_template("signup-error.html", error='username is invalid')

        add_user(first=first, last=last, username=user_name,
                 email=email, password=password)
        session['username'] = user_name

        return redirect('/account/' + user_name)


@app.route("/logout")
def logout():
    session.clear()
    return redirect('/')


@app.route("/create/<username>", methods=["GET", "POST"])
def create(username=''):
    if 'username' in session:

        if request.method == "GET":
            return render_template('create.html', username=session['username'])

        if request.method == "POST":
            id = request.form.get('id')
            name = request.form.get('name')
            pwd = request.form.get('pwd')
            players = request.form.get('players')
            start = request.form.get('date')
            weeks = request.form.get('weeks')
            cash = request.form.get('cash')
            if id == '' or name == '' or pwd == '' or players == '' or start == '' or weeks == '' or cash == '':
                return redirect('/leagues')

            # league id exists
            if league_exists(name):
                return redirect('/leagues')

            create_league(id=id, name=name, password=pwd, players=players, start=start,
                          weeks=weeks, cash=cash, username=get_id(username=username))
            add_schedule(id)

            # add league to leagues

            return redirect('/leagues')

    else:
        return redirect('/login')


@app.route("/join/<username>", methods=["GET", "POST"])
def join(username=''):
    if 'username' in session:
        if request.method == "GET":
            return render_template('join.html', username=session['username'])

        if request.method == "POST":
            id = request.form.get('id')
            name = request.form.get('name')
            pwd = request.form.get('pwd')
            if id == '' or name == '' or pwd == '':
                return redirect('/leagues')

            if correct(id=id, name=name, password=pwd):
                join_league(id=id, name=name, password=pwd,
                            user_id=get_id(username=username))

            # check if the id and pwd are correct and add that league to the
            # users leagues in SQL
            # each league will have an id and all information

            return redirect('/leagues')

    else:
        return redirect('/login')


@app.route("/leagues/<username>/<league_name>/portfolio")
def portfolio(username='', league_name=''):
    # also check if the username in session has a league with that name by checking database
    if 'username' in session:

        # check if league in username database
        user_leagues = get_leagues(username=session['username'])
        cash = get_cash(league=get_league_id(
            name=league_name), user_id=get_id(username))
        stocks = get_stocks(league=get_league_id(
            name=league_name), user_id=get_id(username))
        costs = get_costs(league=get_league_id(
            name=league_name), user_id=get_id(username))
        amounts = get_amounts(league=get_league_id(
            name=league_name), user_id=get_id(username))
        values = get_values(stocks=stocks, value='currentPrice')
        cash = round(cash, 2)
        if league_name in user_leagues:
            return render_template('portfolio.html', username=session['username'], name=league_name, cash=cash, stocks=stocks, amounts=amounts, costs=costs, values=values, count=len(stocks))

    return redirect('/login')


@app.route("/leagues/<username>/<league_name>/portfolio/cashout", methods=["GET", "POST"])
def cash_out(username='', league_name=''):
    if 'username' in session:

        if request.method == "GET":
            user_leagues = get_leagues(username=session['username'])
            if league_name in user_leagues:
                return render_template('cash-out.html', username=session['username'], name=league_name)

        if request.method == "POST":
            stock = request.form.get('stock')

            if (not cashout(league=get_league_id(name=league_name), user_id=get_id(username=username), stock=stock)):
                return render_template('cash-out.html', username=session['username'], name=league_name, alert_message="Invalid")
            else:
                return redirect('/leagues/' + username + '/' + league_name + '/portfolio')

    return redirect('/login')


@app.route("/leagues/<username>/<league_name>/stocks")
def stocks(username='', league_name=''):
    # also check if the username in session has a league with that name by checking database
    if 'username' in session:
        # check if league in username database
        user_leagues = get_leagues(username=session['username'])
        stocks = ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "JPM", "V", "JNJ",
                  "NVDA", "PYPL", "UNH", "HD", "PG", "MA", "DIS", "BAC", "INTC", "XOM", "VZ"]
        current_prices = []
        prev_close = []
        opens = []
        day_lows = []
        regular_day_high = []
        all_array = [current_prices, prev_close,
                     opens, day_lows, regular_day_high]
        values = ['currentPrice', 'previousClose',
                  'open', 'dayLow', 'regularMarketDayHigh']
        for stock in stocks:
            recieved = get_values_array(stock=stock, values=values)
            i = 0
            for array in all_array:
                array.append(recieved[i])
                i = i + 1

        if league_name in user_leagues:
            return render_template('stocks.html', username=session['username'], name=league_name, stocks=stocks, current_prices=current_prices, prev_close=prev_close, opens=opens, day_lows=day_lows, regular_day_high=regular_day_high)

    return redirect('/login')


@app.route("/leagues/<username>/<league_name>/stocks/buy", methods=["GET", "POST"])
def buy_stocks(username='', league_name=''):
    if 'username' in session:
        if request.method == "GET":
            user_leagues = get_leagues(username=session['username'])
            if league_name in user_leagues:
                return render_template('buy-stock.html', username=session['username'], name=league_name)

        if request.method == "POST":
            stock = request.form.get('stock')
            number_shares = request.form.get('shares')

            stock_exists = processOrder(stock=stock, num=number_shares)
            if (stock_exists):
                print(stock_exists)
                buy_stock = buyStock(
                    stock=stock, num=number_shares, league=get_league_id(name=league_name), id=get_id(username=username))
                if (not buy_stock):
                    return render_template('buy-stock.html', username=session['username'], name=league_name, alert_message="Not Enough Money")
                else:
                    return redirect('/leagues/' + username + '/' + league_name + '/portfolio')
            else:
                return render_template('buy-stock.html', username=session['username'], name=league_name, alert_message="Invalid Stock Symbol")

    return redirect('/login')


@app.route("/leagues/<username>/<league_name>/scoreboard")
def scoreboard(username='', league_name=''):
    # also check if the username in session has a league with that name by checking database
    if 'username' in session:
        # check if league in username database
        user_leagues = get_leagues(username=session['username'])
        if league_name in user_leagues:
            return render_template('scoreboard.html', username=session['username'], name=league_name)

    return redirect('/login')


@app.route("/leagues/<username>/<league_name>/standings")
def standings(username='', league_name=''):
    # also check if the username in session has a league with that name by checking database
    if 'username' in session:
        # check if league in username database
        user_leagues = get_leagues(username=session['username'])
        if league_name in user_leagues:
            return render_template('standings.html', username=session['username'], name=league_name)

    return redirect('/login')


@app.route("/leagues/<username>/<league_name>/schedule")
def schedule(username='', league_name=''):
    # also check if the username in session has a league with that name by checking database
    if 'username' in session:
        # check if league in username database
        user_leagues = get_leagues(username=session['username'])
        if league_name in user_leagues:
            return render_template('schedule.html', username=session['username'], name=league_name)

    return redirect('/login')


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)
