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


def libor3m_Feb18(discount_curve_handle=None):
    Settings.instance().evaluationDate = Date(18, 2, 2022)

    # deposit with spot 3m libor rate
    helpers = [DepositRateHelper(QuoteHandle(SimpleQuote(0.47957 / 100)),
                                 Period(3, Months), 2, UnitedStates(), Following, False, Actual360())]

    libor3m = USDLibor(Period(3, Months))

    # 3m libor futures (works)
    helpers += [FuturesRateHelper(QuoteHandle(SimpleQuote(100 - rate)),
                                  start, end, Actual360())
                for (start, end, rate) in [
                    (Date(16, 3, 2022), Date(15, 6, 2022), 0.63984342),
                    (Date(15, 6, 2022), Date(21, 9, 2022), 1.153788538),
                    (Date(21, 9, 2022), Date(21, 12, 2022), 1.522141044),
                    (Date(21, 12, 2022), Date(15, 3, 2023), 1.825137242),
                    (Date(15, 3, 2023), Date(21, 6, 2023), 2.00235),
                    (Date(21, 6, 2023), Date(20, 9, 2023), 2.16911)
                ]]

    # swaps
    spread = QuoteHandle()  # spread = 0
    fwdStart = Period(0, Days)

    def swapRateHelper(rate, tenor, discount_curve_handle):
        if discount_curve_handle is None:
            return SwapRateHelper(QuoteHandle(SimpleQuote(rate / 100)), Period(tenor, Years), UnitedStates(),
                                  Semiannual, Following, Thirty360(Thirty360.BondBasis), libor3m, spread, fwdStart)
        else:
            return SwapRateHelper(QuoteHandle(SimpleQuote(rate / 100)), Period(tenor, Years), UnitedStates(),
                                  Semiannual, Following, Thirty360(Thirty360.BondBasis), libor3m, spread, fwdStart,
                                  discount_curve_handle)

    helpers += [swapRateHelper(rate, tenor, discount_curve_handle)
                for tenor, rate in [
                    (2, 1.65990001), (3, 1.815499544), (4, 1.867499948), (5, 1.9017995), (6, 1.925300002), (7, 1.94975),
                    (8, 1.97), (9, 1.987), (10, 2.00675), (11, 2.025), (12, 2.0452), (15, 2.107),
                    (20, 2.107), (25, 2.0843), (30, 2.0524), (40, 1.9333), (50, 1.82925)
                ]]

    # discount curve
    libor3m_curve = PiecewiseLogLinearDiscount(Date(22, 2, 2022), helpers,
                                               Actual365Fixed())  # use referenceDate=Feb22 to match BBG. but why not Feb23
    libor3m_curve.enableExtrapolation()

    return libor3m_curve


def bootstrap_libor3m_Feb18():
    libor3m_curve = libor3m_Feb18()
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
    pd.DataFrame(libor3m_discounts_instr).to_clipboard()


def sofr_Feb18():
    Settings.instance().evaluationDate = Date(18, 2, 2022)

    # deposit with overnight sofr rate
    helpers = [
        DepositRateHelper(QuoteHandle(SimpleQuote(rate / 100)),
                          Period(1, Days), fixingDays,
                          UnitedStates(), Following, False, Actual360())
        for rate, fixingDays in [(0.05, 2)]
    ]
    sofr = Sofr()

    # swaps
    helpers += [OISRateHelper(2, Period(*tenor),
                              QuoteHandle(SimpleQuote(rate / 100)), sofr)
                for rate, tenor in [
                    (0.06, (1, Weeks)),
                    (0.06, (2, Weeks)),
                    (0.063, (3, Weeks)),
                    (0.122, (1, Months)), (0.24925, (2, Months)), (0.34425, (3, Months)), (0.43865, (4, Months)),
                    (0.533, (5, Months)), (0.615, (6, Months)), (0.6825, (7, Months)), (0.755, (8, Months)),
                    (0.819, (9, Months)), (0.8796, (10, Months)), (0.93935, (11, Months)), (0.994, (12, Months)),
                    (1.261, (18, Months)),
                    (1.4345, (2, Years)),
                    (1.5704, (3, Years))
                ]]

    # discount curve
    sofr_curve_c = PiecewiseLogLinearDiscount(Date(23, 2, 2022), helpers, Actual365Fixed())
    sofr_curve_c.enableExtrapolation()

    return sofr_curve_c


def bootstrap_sofr_Feb18():
    sofr_curve_c = sofr_Feb18()
    print('reference date: ', sofr_curve_c.referenceDate())

    reference_date = sofr_curve_c.referenceDate()
    print(reference_date)

    # discount factors
    sofr_discounts_instr = [(d, sofr_curve_c.discount(d)) for d in sofr_curve_c.dates()]
    print(pd.DataFrame(sofr_discounts_instr))
    pd.DataFrame(sofr_discounts_instr).to_clipboard()


def dual_curve_bootstrap_Feb18():
    sofr_curve = sofr_Feb18()
    discount_curve_handle = RelinkableYieldTermStructureHandle()
    discount_curve_handle.linkTo(sofr_curve)
    libor3m_curve = libor3m_Feb18(discount_curve_handle)
    print('reference date: ', libor3m_curve.referenceDate())

    # discount factors
    libor3m_discounts_instr = [(d, libor3m_curve.discount(d)) for d in libor3m_curve.dates()]
    print(pd.DataFrame(libor3m_discounts_instr))
    pd.DataFrame(libor3m_discounts_instr).to_clipboard()


def sofr_Feb25():
    Settings.instance().evaluationDate = Date(25, 2, 2022)

    # deposit with overnight sofr rate
    helpers = [
        DepositRateHelper(QuoteHandle(SimpleQuote(rate / 100)),
                          Period(1, Days), fixingDays,
                          UnitedStates(), Following, False, Actual360())
        for rate, fixingDays in [(0.05, 2)]
    ]
    sofr = Sofr()

    # swaps
    helpers += [OISRateHelper(2, Period(*tenor),
                              QuoteHandle(SimpleQuote(rate / 100)), sofr)
                for rate, tenor in [
                    (0.0533, (1, Weeks)),
                    (0.0547, (2, Weeks)),
                    (0.1275, (3, Weeks)),
                    (0.2066, (1, Months)), (0.2872, (2, Months)), (0.404, (3, Months)), (0.49505, (4, Months)),
                    (0.5791, (5, Months)), (0.65995, (6, Months)), (0.7299, (7, Months)), (0.7935, (8, Months)),
                    (0.865, (9, Months)), (0.93525, (10, Months)), (0.99535, (11, Months)), (1.0483, (12, Months)),
                    (1.3475, (18, Months)),
                    (1.5291, (2, Years)), (1.6578, (3, Years)), (1.687, (4, Years)), (1.702, (5, Years)),
                    (1.71785, (6, Years)), (1.7346, (7, Years)), (1.75065, (8, Years)), (1.76415, (9, Years)),
                    (1.78025, (10, Years)), (1.81225, (12, Years)), (1.8445, (15, Years)), (1.86175, (20, Years)),
                    (1.83475, (25, Years)), (1.79725, (30, Years)), (1.679, (40, Years)), (1.523, (50, Years))
                ]]

    # discount curve
    sofr_curve_c = PiecewiseLogLinearDiscount(Date(1, 3, 2022), helpers, Actual365Fixed())
    sofr_curve_c.enableExtrapolation()

    return sofr_curve_c


def bootstrap_sofr_Feb25():
    sofr_curve_c = sofr_Feb25()
    print('reference date: ', sofr_curve_c.referenceDate())

    reference_date = sofr_curve_c.referenceDate()
    print(reference_date)

    # discount factors
    sofr_discounts_instr = [(d, sofr_curve_c.discount(d)) for d in sofr_curve_c.dates()]
    print(pd.DataFrame(sofr_discounts_instr))
    pd.DataFrame(sofr_discounts_instr).to_clipboard()


def libor3m_Feb25(discount_curve_handle=None):
    Settings.instance().evaluationDate = Date(25, 2, 2022)

    # deposit with spot 3m libor rate
    helpers = [DepositRateHelper(QuoteHandle(SimpleQuote(0.523 / 100)),
                                 Period(3, Months), 2, UnitedStates(), Following, False, Actual360())]

    libor3m = USDLibor(Period(3, Months))

    # 3m libor futures (works)
    helpers += [FuturesRateHelper(QuoteHandle(SimpleQuote(100 - rate)),
                                  start, end, Actual360())
                for (start, end, rate) in [
                    (Date(16, 3, 2022), Date(15, 6, 2022), 0.6724),
                    (Date(15, 6, 2022), Date(21, 9, 2022), 1.19394),
                    (Date(21, 9, 2022), Date(21, 12, 2022), 1.59242),
                    (Date(21, 12, 2022), Date(15, 3, 2023), 1.93555),
                    (Date(15, 3, 2023), Date(21, 6, 2023), 2.13294),
                    (Date(21, 6, 2023), Date(20, 9, 2023), 2.3049)
                ]]

    # swaps
    spread = QuoteHandle()  # spread = 0
    fwdStart = Period(0, Days)

    def swapRateHelper(rate, tenor, discount_curve_handle):
        if discount_curve_handle is None:
            return SwapRateHelper(QuoteHandle(SimpleQuote(rate / 100)), Period(tenor, Years), UnitedStates(),
                                  Semiannual, Following, Thirty360(Thirty360.BondBasis), libor3m, spread, fwdStart)
        else:
            return SwapRateHelper(QuoteHandle(SimpleQuote(rate / 100)), Period(tenor, Years), UnitedStates(),
                                  Semiannual, Following, Thirty360(Thirty360.BondBasis), libor3m, spread, fwdStart,
                                  discount_curve_handle)

    helpers += [swapRateHelper(rate, tenor, discount_curve_handle)
                for tenor, rate in [
                    (2, 1.76185), (3, 1.9055), (4, 1.9427), (5, 1.96145), (6, 1.9815), (7, 1.99865),
                    (8, 2.01635), (9, 2.03085), (10, 2.048), (11, 2.06375), (12, 2.08115), (15, 2.1143),
                    (20, 2.133), (25, 2.107), (30, 2.0697), (40, 1.9508), (50, 1.856)
                ]]

    # discount curve
    libor3m_curve = PiecewiseLogLinearDiscount(Date(1, 3, 2022), helpers, Actual365Fixed())
    libor3m_curve.enableExtrapolation()

    return libor3m_curve


def bootstrap_libor3m_Feb25():
    libor3m_curve = libor3m_Feb25()
    print('reference date: ', libor3m_curve.referenceDate())

    # discount factors
    libor3m_discounts_instr = [(d, libor3m_curve.discount(d)) for d in libor3m_curve.dates()]
    print(pd.DataFrame(libor3m_discounts_instr))
    pd.DataFrame(libor3m_discounts_instr).to_clipboard()


def dual_curve_bootstrap_Feb25():
    sofr_curve = sofr_Feb25()
    discount_curve_handle = RelinkableYieldTermStructureHandle()
    discount_curve_handle.linkTo(sofr_curve)
    libor3m_curve = libor3m_Feb25(discount_curve_handle)
    print('reference date: ', libor3m_curve.referenceDate())

    # discount factors
    libor3m_discounts_instr = [(d, libor3m_curve.discount(d)) for d in libor3m_curve.dates()]
    print(pd.DataFrame(libor3m_discounts_instr))
    pd.DataFrame(libor3m_discounts_instr).to_clipboard()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # bootstrap_sofr_Feb18()
    # bootstrap_libor3m_Feb18()
    # dual_curve_bootstrap_Feb18()

    # bootstrap_sofr_Feb25()
    # bootstrap_libor3m_Feb25()
    dual_curve_bootstrap_Feb25()
