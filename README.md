# Konkka – Share costs of a joint project

This is just me practicing Curses for building retro CLI apps with Python 3 standard library. The only requirement is to have Python 3 installed.

<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-refresh-toc -->
**Table of Contents**

- [Main features](#main-feature)
- [Setting up the Curses UI](#setting-up-the-curses-ui)
- [Example "back-end" calculation](#example-back-end-calculation)

<!-- markdown-toc end -->


## Main features

Assume you have a project (e.g. a holiday trip) with N friends. You decide that
each bill (such as restaurant meals and coffees) shall be paid by one person
(might be different case by case); you will balance out costs after the trip.

This program 

- Calculates the balancing action with **minimal number of transactions**.
- Provides a retro "CLI Excel" user interface for carrying out calculations

## Setting up the Curses UI

1. Clone ``https://github.com/malmgrek/konkka``.
2. Navigate to ``konkka`` directory.
3. Run program ``app.py`` with the Python interpreter.

![alt text](./doc/source/images/screenshot.png "Screenshot")

## Example "back-end" calculation

Using the calculation "back-end" with a random example:

``` python
    users = ["Alex", "Andy", "John", "Nick", "Greg", "Fred",
             "Gust", "Buck", "Tony", "Matt", "Burt", "Earl"]
    bills = {
        f"bill_{i}": {
            user: {
                "payment": round(100.0 * random.random(), 0),
                "share": 1./len(users)
            }
            for user in users
        } for i in range(20)
    }

    # ----- Define accounting state --------
    state = State(users=users, bills=bills)
    balance = state.calculate_balance()
    money_flow = state.calculate_flow()
    # --------------------------------------

    print("\nBills:\n")
    for (bill_id, data) in bills.items():
        numbers = "".join(f"{v['payment']:<5}" for (k, v) in data.items())
        print(f"{bill_id:>10}| {' '.join(users)}\n" + f"{'Paid':>10}| {numbers}")
    print("\nMoney flow:\n")
    for (payer, payee, amount) in money_flow:
        print(f"{payer:>6} pays {round(amount, 1):>5} to {payee}"
```

Will print out something like:

``` text
Bills:

    bill_0| Alex Andy John Nick Greg Fred Gust Buck Tony Matt Burt Earl
      Paid| 86.0 27.0 71.0 95.0 87.0 24.0 19.0 10.0 10.0 45.0 32.0 57.0
    bill_1| Alex Andy John Nick Greg Fred Gust Buck Tony Matt Burt Earl
      Paid| 98.0 18.0 21.0 76.0 72.0 42.0 29.0 8.0  96.0 12.0 35.0 24.0
    bill_2| Alex Andy John Nick Greg Fred Gust Buck Tony Matt Burt Earl
      Paid| 4.0  48.0 73.0 50.0 2.0  69.0 37.0 91.0 72.0 63.0 11.0 89.0
    bill_3| Alex Andy John Nick Greg Fred Gust Buck Tony Matt Burt Earl
      Paid| 89.0 40.0 9.0  9.0  33.0 9.0  97.0 96.0 90.0 41.0 95.0 48.0
    bill_4| Alex Andy John Nick Greg Fred Gust Buck Tony Matt Burt Earl
      Paid| 87.0 60.0 36.0 51.0 60.0 26.0 85.0 15.0 17.0 25.0 20.0 93.0
    bill_5| Alex Andy John Nick Greg Fred Gust Buck Tony Matt Burt Earl
      Paid| 93.0 8.0  37.0 73.0 33.0 69.0 87.0 43.0 98.0 13.0 42.0 38.0
    bill_6| Alex Andy John Nick Greg Fred Gust Buck Tony Matt Burt Earl
      Paid| 79.0 83.0 55.0 15.0 25.0 28.0 17.0 55.0 40.0 5.0  35.0 53.0
    bill_7| Alex Andy John Nick Greg Fred Gust Buck Tony Matt Burt Earl
      Paid| 40.0 10.0 53.0 28.0 38.0 16.0 15.0 1.0  28.0 98.0 64.0 57.0
    bill_8| Alex Andy John Nick Greg Fred Gust Buck Tony Matt Burt Earl
      Paid| 57.0 62.0 44.0 84.0 25.0 68.0 10.0 65.0 62.0 6.0  38.0 25.0
    bill_9| Alex Andy John Nick Greg Fred Gust Buck Tony Matt Burt Earl
      Paid| 28.0 79.0 73.0 29.0 95.0 19.0 13.0 68.0 75.0 31.0 37.0 89.0
   bill_10| Alex Andy John Nick Greg Fred Gust Buck Tony Matt Burt Earl
      Paid| 70.0 85.0 29.0 23.0 98.0 66.0 56.0 87.0 90.0 2.0  94.0 2.0
   bill_11| Alex Andy John Nick Greg Fred Gust Buck Tony Matt Burt Earl
      Paid| 67.0 11.0 18.0 48.0 39.0 88.0 45.0 93.0 64.0 2.0  32.0 95.0
   bill_12| Alex Andy John Nick Greg Fred Gust Buck Tony Matt Burt Earl
      Paid| 99.0 82.0 81.0 58.0 19.0 40.0 7.0  69.0 60.0 12.0 77.0 79.0
   bill_13| Alex Andy John Nick Greg Fred Gust Buck Tony Matt Burt Earl
      Paid| 23.0 25.0 53.0 97.0 48.0 60.0 43.0 46.0 37.0 52.0 61.0 69.0
   bill_14| Alex Andy John Nick Greg Fred Gust Buck Tony Matt Burt Earl
      Paid| 63.0 94.0 88.0 26.0 29.0 10.0 95.0 76.0 34.0 22.0 33.0 85.0
   bill_15| Alex Andy John Nick Greg Fred Gust Buck Tony Matt Burt Earl
      Paid| 78.0 42.0 53.0 63.0 5.0  87.0 86.0 41.0 49.0 56.0 59.0 83.0
   bill_16| Alex Andy John Nick Greg Fred Gust Buck Tony Matt Burt Earl
      Paid| 1.0  56.0 1.0  22.0 89.0 22.0 43.0 8.0  76.0 87.0 16.0 27.0
   bill_17| Alex Andy John Nick Greg Fred Gust Buck Tony Matt Burt Earl
      Paid| 15.0 62.0 45.0 26.0 47.0 66.0 59.0 26.0 21.0 91.0 92.0 37.0
   bill_18| Alex Andy John Nick Greg Fred Gust Buck Tony Matt Burt Earl
      Paid| 5.0  35.0 20.0 100.011.0 38.0 9.0  29.0 99.0 48.0 20.0 67.0
   bill_19| Alex Andy John Nick Greg Fred Gust Buck Tony Matt Burt Earl
      Paid| 88.0 91.0 63.0 59.0 54.0 43.0 55.0 9.0  43.0 76.0 77.0 45.0

Money flow:

  Matt pays 181.3 to Alex
  Fred pays  98.7 to Earl
  Gust pays  81.7 to Tony
  Greg pays  79.7 to Tony
  John pays  65.7 to Earl
  Buck pays  43.3 to Nick
  Matt pays  20.5 to Andy
  Burt pays  10.8 to Tony
  Buck pays   8.8 to Andy
  Burt pays   8.0 to Earl
  Buck pays   0.7 to Earl
```

## TODO

- Browser version
