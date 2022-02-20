from QuantLib import *
import pandas as pd
import matplotlib.pyplot as plt


def print_hi(name):
    date = Date(31, 3, 2015)
    print(date)

    effective_date = Date(1, 1, 2015)
    termination_date = Date(1, 1, 2016)
    tenor = Period(Monthly)
    calendar = TARGET()
    business_convention = Following
    date_generation = DateGeneration.Forward
    end_of_month = False

    schedule = Schedule(effective_date,
                        termination_date,
                        tenor,
                        calendar,
                        business_convention,
                        business_convention,
                        date_generation,
                        end_of_month)
    print(Calendar)

    interest_rate = InterestRate(0.05, ActualActual(), Compounded, Annual)


def bootstrap_eonia():
    # bootstrapping EONIA

    Settings.instance().evaluationDate = Date(11, 12, 2012)

    helpers = [
        DepositRateHelper(QuoteHandle(SimpleQuote(rate / 100)),
                          Period(1, Days), fixingDays,
                          TARGET(), Following, False, Actual360())
        for rate, fixingDays in [(0.04, 0), (0.04, 1), (0.04, 2)]
    ]
    eonia = Eonia()
    helpers += [OISRateHelper(2, Period(*tenor),
                              QuoteHandle(SimpleQuote(rate / 100)), eonia)
                for rate, tenor in [
                    (0.070, (1, Weeks)),
                    (0.069, (2, Weeks)),
                    (0.078, (3, Weeks)),
                    (0.074, (1, Months))
                ]]
    helpers += [DatedOISRateHelper(start_date, end_date,
                                   QuoteHandle(SimpleQuote(rate / 100)), eonia)
                for rate, start_date, end_date in [
                    (0.046, Date(16, January, 2013), Date(13, February, 2013)),
                    (0.016, Date(13, February, 2013), Date(13, March, 2013)),
                    (-0.007, Date(13, March, 2013), Date(10, April, 2013)),
                    (-0.013, Date(10, April, 2013), Date(8, May, 2013)),
                    (-0.014, Date(8, May, 2013), Date(12, June, 2013))]]
    helpers += [OISRateHelper(2, Period(*tenor),
                              QuoteHandle(SimpleQuote(rate / 100)), eonia)
                for rate, tenor in [(0.002, (15, Months)), (0.008, (18, Months)),
                                    (0.021, (21, Months)), (0.036, (2, Years)),
                                    (0.127, (3, Years)), (0.274, (4, Years)),
                                    (0.456, (5, Years)), (0.647, (6, Years)),
                                    (0.827, (7, Years)), (0.996, (8, Years)),
                                    (1.147, (9, Years)), (1.280, (10, Years)),
                                    (1.404, (11, Years)), (1.516, (12, Years)),
                                    (1.764, (15, Years)), (1.939, (20, Years)),
                                    (2.003, (25, Years)), (2.038, (30, Years))]]
    eonia_curve_c = PiecewiseLogCubicDiscount(0, TARGET(), helpers, Actual365Fixed())

    reference_date = eonia_curve_c.referenceDate()
    print(reference_date)

    # print all date tenors from observations
    dates = eonia_curve_c.dates()
    print(dates)

    # print spot rates (after bootstrapping) from observations
    spot_rates = [
        (d, eonia_curve_c.zeroRate(
            eonia_curve_c.dayCounter().yearFraction(eonia_curve_c.referenceDate(), d),
            Compounded,
            Quarterly
        ).rate())
        for d in eonia_curve_c.dates()
    ]
    print(pd.DataFrame(spot_rates))

    eonia_curve_zero_rate = eonia_curve_c.zeroRate(0.05, Compounded, Quarterly)
    eonia_curve_zero_rate_2 = eonia_curve_c.zeroRate(0.05, Compounded, Annual)
    print('quarterly: ', eonia_curve_zero_rate)
    print('annual: ', eonia_curve_zero_rate_2)

    # equivalent yield
    eonia_curve_zero_rate_eq = eonia_curve_zero_rate.equivalentRate(Compounded, Annual, 1)
    print('quarterly -> annual: ', eonia_curve_zero_rate_eq)


def bootstrap_libor3m():
    Settings.instance().evaluationDate = Date(18, 2, 2022)

    # deposit with spot 3m libor rate
    helpers = [DepositRateHelper(QuoteHandle(SimpleQuote(0.47957 / 100)),
                                 Period(3, Months), 1, UnitedStates(), Following, False, Actual360())]
    # 3m libor futures
    libor3m = USDLibor(Period(3, Months))
    helpers += [FuturesRateHelper(QuoteHandle(SimpleQuote(100 - rate)), # 100 - rate    # SimpleQuote(px)
                                  start, end, Actual360()) # , QuoteHandle(SimpleQuote(conv))
                for (start, end, rate) in [
                    # (Date(15, 6, 2022), 0.63984), (Date(21, 9, 2022), 1.15379), (Date(21, 12, 2022), 1.52214),
                    # (Date(15, 3, 2023), 1.82514), (Date(21, 6, 2023), 2.00235), (Date(20, 9, 2023), 2.16911)

                    (Date(16, 3, 2022), Date(15, 6, 2022), 0.63984342),
                    (Date(15, 6, 2022), Date(21, 9, 2022), 1.153788538),
                    (Date(21, 9, 2022), Date(21, 12, 2022), 1.522141044),
                    (Date(21, 12, 2022), Date(15, 3, 2023), 1.825137242),
                    (Date(15, 3, 2023), Date(21, 6, 2023), 2.00235),
                    (Date(21, 6, 2023), Date(20, 9, 2023), 2.16911)

                    # (Date(16, 3, 2022), Date(15, 6, 2022), 99.36, -0.00016),
                    # (Date(15, 6, 2022), Date(21, 9, 2022), 98.845, -0.00121),
                    # (Date(21, 9, 2022), Date(21, 12, 2022), 98.475, -0.00286),
                    # (Date(21, 12, 2022), Date(15, 3, 2023), 98.17, -0.00765),
                    # (Date(15, 3, 2023), Date(21, 6, 2023), 97.99, -0.01089),
                    # (Date(21, 6, 2023), Date(20, 9, 2023), 97.82, -0.01089)
                ]]

    # swaps
    spread = QuoteHandle()  # spread = 0
    fwdStart = Period(0, Days)
    helpers += [SwapRateHelper(QuoteHandle(SimpleQuote(rate / 100)), Period(tenor, Years), TARGET(),
                               Annual, Unadjusted, Thirty360(Thirty360.USA), libor3m, spread, fwdStart)
                for tenor, rate in [
                    (2, 1.6599), (3, 1.8155), (4, 1.8675), (5, 1.9018), (6, 1.9253), (7, 1.94975),
                    (8, 1.97), (9, 1.987), (10, 2.00675), (11, 2.025), (12, 2.0452), (15, 2.107),
                    (20, 2.107), (25, 2.0843), (30, 2.0524), (40, 1.9333), (50, 1.82925)
                ]]

    # discount curve
    libor3m_curve = PiecewiseLinearZero(1, UnitedStates(), helpers, Actual360())
    libor3m_curve.enableExtrapolation()
    print('reference date: ', libor3m_curve.referenceDate())

    # plot forward curve
    # today = libor3m_curve.referenceDate()
    # end = today + Period(5, Years)
    # dates = [Date(serial) for serial in range(today.serialNumber(), end.serialNumber() + 1)]
    # libor3m_rates = [libor3m_curve.forwardRate(d, TARGET().advance(d, 3, Months), Actual360(), Simple).rate() * 100
    #                  for d in dates]
    # plt.plot(libor3m_rates)
    # plt.show()

    # discount factors
    libor3m_discounts_instr = [(d, libor3m_curve.discount(d)) for d in libor3m_curve.dates()]
    print(pd.DataFrame(libor3m_discounts_instr))


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    bootstrap_libor3m()
