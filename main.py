from QuantLib import *
import pandas as pd
import matplotlib.pyplot as plt
import datetime


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


# Feb 18

def _bootstrap_libor3m_Feb18(discount_curve_handle=None):
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
    libor3m_curve = _bootstrap_libor3m_Feb18()
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


def _bootstrap_sofr_Feb18():
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
    sofr_curve_c = _bootstrap_sofr_Feb18()
    print('reference date: ', sofr_curve_c.referenceDate())

    reference_date = sofr_curve_c.referenceDate()
    print(reference_date)

    # discount factors
    sofr_discounts_instr = [(d, sofr_curve_c.discount(d)) for d in sofr_curve_c.dates()]
    print(pd.DataFrame(sofr_discounts_instr))
    pd.DataFrame(sofr_discounts_instr).to_clipboard()


def dual_curve_bootstrap_Feb18():
    sofr_curve = _bootstrap_sofr_Feb18()
    discount_curve_handle = RelinkableYieldTermStructureHandle()
    discount_curve_handle.linkTo(sofr_curve)
    libor3m_curve = _bootstrap_libor3m_Feb18(discount_curve_handle)
    print('reference date: ', libor3m_curve.referenceDate())

    # discount factors
    libor3m_discounts_instr = [(d, libor3m_curve.discount(d)) for d in libor3m_curve.dates()]
    print(pd.DataFrame(libor3m_discounts_instr))
    pd.DataFrame(libor3m_discounts_instr).to_clipboard()


# Feb 25

def _bootstrap_sofr_Feb25():
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
    sofr_curve_c = _bootstrap_sofr_Feb25()
    print('reference date: ', sofr_curve_c.referenceDate())

    reference_date = sofr_curve_c.referenceDate()
    print(reference_date)

    # discount factors
    print('====== sofr discount factors Feb25 =====')
    sofr_discounts_instr = [(d, sofr_curve_c.discount(d)) for d in sofr_curve_c.dates()]
    print(pd.DataFrame(sofr_discounts_instr))
    pd.DataFrame(sofr_discounts_instr).to_clipboard()
    print()


def _bootstrap_libor3m_Feb25(discount_curve_handle=None):
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
    libor3m_curve = _bootstrap_libor3m_Feb25()
    print('reference date: ', libor3m_curve.referenceDate())

    # discount factors
    print('====== libor3m discount factors (raw) Feb25 =====')
    libor3m_discounts_instr = [(d, libor3m_curve.discount(d)) for d in libor3m_curve.dates()]
    print(pd.DataFrame(libor3m_discounts_instr))
    pd.DataFrame(libor3m_discounts_instr).to_clipboard()
    print()


def _dual_curve_bootstrap_Feb25():
    sofr_curve = _bootstrap_sofr_Feb25()
    discount_curve_handle = RelinkableYieldTermStructureHandle()
    discount_curve_handle.linkTo(sofr_curve)
    libor3m_curve = _bootstrap_libor3m_Feb25(discount_curve_handle)

    return libor3m_curve


def dual_curve_bootstrap_Feb25():
    libor3m_curve = _dual_curve_bootstrap_Feb25()
    print('reference date: ', libor3m_curve.referenceDate())

    # discount factors
    print('====== libor3m discount factors (sofr ois discounted) Feb25 =====')
    libor3m_discounts_instr = [(d, libor3m_curve.discount(d)) for d in libor3m_curve.dates()]
    print(pd.DataFrame(libor3m_discounts_instr))
    pd.DataFrame(libor3m_discounts_instr).to_clipboard()
    print()


def compare_libor3m_single_dual_forward_rates_Feb25():
    libor3m_single_curve = _bootstrap_libor3m_Feb25()
    libor3m_dual_curve = _dual_curve_bootstrap_Feb25()

    start = libor3m_single_curve.referenceDate() + Period(9, Years)
    end = start + Period(10, Years)
    dates = [Date(serial) for serial in range(start.serialNumber(), end.serialNumber() + 1)]
    libor3m_rates = [
        (datetime.datetime(d.year(), d.month(), d.dayOfMonth()),
         libor3m_single_curve.forwardRate(d, UnitedStates().advance(d, 3, Months), Actual360(), Simple).rate() * 100,
         libor3m_dual_curve.forwardRate(d, UnitedStates().advance(d, 3, Months), Actual360(), Simple).rate() * 100)
        for d in dates]
    libor3m_rates = list(zip(*libor3m_rates))
    plt.plot(libor3m_rates[0], libor3m_rates[1], 'r')
    plt.plot(libor3m_rates[0], libor3m_rates[2], 'g')
    plt.show()


def check_calibration_fit_Feb25():
    # discount curve
    sofr_curve_handle = YieldTermStructureHandle(_bootstrap_sofr_Feb25())

    # forward term structure (forecast)
    libor3m_curve_handle = YieldTermStructureHandle(_dual_curve_bootstrap_Feb25())

    # price a calibration instrument, expecting ~0 NPV
    # (e.g. 2Y swap with 1.76185% fixed rate)
    calendar = UnitedStates()
    settle_date = Date(1, 3, 2022)
    maturity_date = Date(1, 3, 2024)

    fixed_leg_tenor = Period(6, Months)
    fixed_schedule = Schedule(settle_date, maturity_date,
                              fixed_leg_tenor, calendar,
                              ModifiedFollowing, ModifiedFollowing,
                              DateGeneration.Forward, False)

    float_leg_tenor = Period(3, Months)
    float_schedule = Schedule(settle_date, maturity_date,
                              float_leg_tenor, calendar,
                              ModifiedFollowing, ModifiedFollowing,
                              DateGeneration.Forward, False)

    notional = 10000000
    fixed_rate = 1.76185 / 100
    fixed_leg_daycount = Thirty360(Thirty360.BondBasis)
    float_spread = 0
    float_leg_daycount = Actual360()

    ir_swap = VanillaSwap(VanillaSwap.Payer, notional, fixed_schedule,
                          fixed_rate, fixed_leg_daycount, float_schedule,
                          USDLibor(Period(3, Months), libor3m_curve_handle), float_spread, float_leg_daycount)

    swap_engine = DiscountingSwapEngine(sofr_curve_handle)
    ir_swap.setPricingEngine(swap_engine)

    print('===== check calibration fit Feb25 =====')
    print('par swap rate: ', ir_swap.fairRate() * 100, '%')
    print('npv: ', ir_swap.NPV())
    print()


def price_2y_imm_swap_Feb25():
    # discount curve
    sofr_curve_handle = YieldTermStructureHandle(_bootstrap_sofr_Feb25())

    # forward term structure (forecast)
    libor3m_curve_handle = YieldTermStructureHandle(_dual_curve_bootstrap_Feb25())

    Settings.instance().evaluationDate = Date(25, 2, 2022)

    # IMM 2Y swap at market level of 1.8157% fixed rate
    calendar = UnitedStates()
    effective_date = Date(16, 3, 2022)
    maturity_date = Date(20, 3, 2024)

    fixed_leg_tenor = Period(6, Months)
    fixed_schedule = Schedule(effective_date, maturity_date,
                              fixed_leg_tenor, calendar,
                              ModifiedFollowing, ModifiedFollowing,
                              DateGeneration.ThirdWednesday, False)

    float_leg_tenor = Period(3, Months)
    float_schedule = Schedule(effective_date, maturity_date,
                              float_leg_tenor, calendar,
                              ModifiedFollowing, ModifiedFollowing,
                              DateGeneration.ThirdWednesday, False)

    notional = 10000000
    fixed_rate = 1.8157 / 100
    fixed_leg_daycount = Thirty360(Thirty360.BondBasis)
    float_spread = 0
    float_leg_daycount = Actual360()

    ir_swap = VanillaSwap(VanillaSwap.Payer, notional, fixed_schedule,
                          fixed_rate, fixed_leg_daycount, float_schedule,
                          USDLibor(Period(3, Months), libor3m_curve_handle), float_spread, float_leg_daycount)

    swap_engine = DiscountingSwapEngine(sofr_curve_handle)
    ir_swap.setPricingEngine(swap_engine)

    print('===== price forward starting 2y imm swap Feb25 =====')
    print('par swap rate: ', ir_swap.fairRate() * 100, '%')
    print('npv: ', ir_swap.NPV())
    print('cv01: ', ir_swap.fixedLegBPS())
    print()

    print('fixed_schedule: ', fixed_schedule.dates())
    x = fixed_schedule.dates()
    discount_factors = [(sofr_curve_handle.discount(x[i + 1]) * fixed_leg_daycount.yearFraction(x[i], x[i + 1]))
                        for i, date in enumerate(x[:-1])]
    import numpy as np
    print('cv01 (verify): ', np.array(discount_factors).sum() * notional / 10000)  # 10000 for bps


# EUR Apr 14

def _bootstrap_euribor6m_Apr14(discount_curve_handle=None):
    Settings.instance().evaluationDate = Date(14, 4, 2022)

    euribor6m = Euribor6M()
    print(euribor6m, ': fixing days: ', euribor6m.fixingDays())

    # deposit with spot 6m euribor rate
    helpers = [DepositRateHelper(QuoteHandle(SimpleQuote(-0.317 / 100)),
                                 Period(6, Months), 2, TARGET(), ModifiedFollowing, False, Actual360())]

    # 6m euribor FRAs
    # helpers += [FraRateHelper(QuoteHandle(SimpleQuote(rate / 100)), startMonth, euribor6m)
    helpers += [FraRateHelper(QuoteHandle(SimpleQuote(rate / 100)), startMonth, startMonth + 6, euribor6m.fixingDays(),
                              TARGET(), ModifiedFollowing, True, Actual360())
                for (startMonth, rate) in [
                    (1, -0.235), (2, -0.133), (3, -0.2), (4, 0.08), (5, 0.212), (6, 0.385),
                    (7, 0.514), (8, 0.66), (9, 0.818), (10, 0.96), (11, 1.091), (12, 1.191)
                ]]

    # swaps
    spread = QuoteHandle()  # spread = 0
    fwdStart = Period(0, Days)

    def swapRateHelper(rate, tenor, discount_curve_handle):
        if discount_curve_handle is None:
            return SwapRateHelper(QuoteHandle(SimpleQuote(rate / 100)), Period(tenor, Years), TARGET(),
                                  Semiannual, Following, Thirty360(Thirty360.European), euribor6m, spread, fwdStart)
        else:
            return SwapRateHelper(QuoteHandle(SimpleQuote(rate / 100)), Period(tenor, Years), TARGET(),
                                  Semiannual, Following, Thirty360(Thirty360.European), euribor6m, spread, fwdStart,
                                  discount_curve_handle)

    helpers += [swapRateHelper(rate, tenor, discount_curve_handle)
                for tenor, rate in [
                    (2, 0.7075), (3, 1.024), (4, 1.182), (5, 1.283), (6, 1.348), (7, 1.407),
                    (8, 1.4645), (9, 1.52475), (10, 1.573), (11, 1.6202), (12, 1.653), (15, 1.704),
                    (20, 1.628), (25, 1.508), (30, 1.393), (40, 1.242), (50, 1.122)
                ]]

    # discount curve
    curve_start_date = euribor6m.fixingCalendar().advance(Settings.instance().evaluationDate, euribor6m.fixingDays(),
                                                          Days)
    print('curve_start_date: ', curve_start_date)
    euribor6m_curve = PiecewiseLogLinearDiscount(curve_start_date, helpers, Thirty360(Thirty360.European))
    euribor6m_curve.enableExtrapolation()

    return euribor6m_curve


def bootstrap_euribor6m_Apr14():
    euribor6m_curve = _bootstrap_euribor6m_Apr14()
    print('reference date: ', euribor6m_curve.referenceDate())

    # plot forward curve
    # today = euribor6m_curve.referenceDate()
    # end = today + Period(5, Years)
    # dates = [Date(serial) for serial in range(today.serialNumber(), end.serialNumber() + 1)]
    # euribor6m_rates = [euribor6m_curve.forwardRate(d, TARGET().advance(d, 3, Months), Actual360(), Simple).rate() * 100
    #                  for d in dates]
    # plt.plot(euribor6m_rates)
    # plt.show()

    # discount factors
    euribor6m_discounts_instr = [(d, euribor6m_curve.discount(d)) for d in euribor6m_curve.dates()]
    print(pd.DataFrame(euribor6m_discounts_instr))
    pd.DataFrame(euribor6m_discounts_instr).to_clipboard()


def _bootstrap_estr_Apr14():
    # evaluation date = Apr14
    # ESTR holiday: Apr15, Apr18
    # curve start date = Apr20
    # deposit / swap settlement: T+2

    Settings.instance().evaluationDate = Date(14, 4, 2022)

    estr = Estr()

    print(estr, ': fixing days: ', estr.fixingDays())
    print(estr, ': fixing calendar: ', estr.fixingCalendar())
    print(estr, ': day convention: ', estr.businessDayConvention())

    # deposit with overnight estr rate
    # (apply same deposit rate over today, TN, ON)
    helpers = [
        DepositRateHelper(QuoteHandle(SimpleQuote(rate / 100)),
                          Period(1, Days), fixingDays,
                          estr.fixingCalendar(), Following, False, Actual360())
        for rate, fixingDays in [(-0.586, 0), (-0.586, 1), (-0.586, 2)]
    ]

    # swaps
    helpers += [OISRateHelper(2, Period(*tenor),
                              QuoteHandle(SimpleQuote(rate / 100)), estr)
                for rate, tenor in [
                    (-0.577, (1, Weeks)),
                    (-0.5769, (2, Weeks)),
                    (-0.575, (1, Months)), (-0.5725, (2, Months)), (-0.5635, (3, Months)),
                    (-0.5315, (4, Months)),
                    (-0.505, (5, Months)), (-0.4635, (6, Months)), (-0.4205, (7, Months)),
                    (-0.3855, (8, Months)),
                    (-0.3358, (9, Months)), (-0.279, (10, Months)), (-0.226, (11, Months)),
                    (-0.163, (12, Months)),
                    (0.2045, (18, Months)),
                    (0.484, (2, Years)), (0.774, (3, Years)), (0.918, (4, Years)),
                    (1.006, (5, Years)), (1.067, (6, Years)), (1.129, (7, Years)),
                    (1.1878, (8, Years)), (1.248899519, (9, Years)), (1.306249976, (10, Years)),
                    (1.357649982, (11, Years)), (1.400349975, (12, Years)), (1.487150013, (15, Years)),
                    (1.471650004, (20, Years)), (1.390299976, (25, Years)), (1.306200027, (30, Years)),
                    (1.194999456, (40, Years)), (1.104000032, (50, Years))
                ]]

    # discount curve
    # settlement: T+2
    estr_curve_c = PiecewiseLogLinearDiscount(Date(20, 4, 2022), helpers, Actual365Fixed())
    estr_curve_c.enableExtrapolation()

    return estr_curve_c


def bootstrap_estr_Apr14():
    estr_curve_c = _bootstrap_estr_Apr14()
    print('reference date: ', estr_curve_c.referenceDate())

    reference_date = estr_curve_c.referenceDate()
    print(reference_date)

    # discount factors
    estr_discounts_instr = [(d, estr_curve_c.discount(d)) for d in estr_curve_c.dates()]
    print(pd.DataFrame(estr_discounts_instr))
    pd.DataFrame(estr_discounts_instr).to_clipboard()


def _dual_curve_bootstrap_eur_Apr14():
    estr_curve = _bootstrap_estr_Apr14()
    discount_curve_handle = RelinkableYieldTermStructureHandle()
    discount_curve_handle.linkTo(estr_curve)
    euribor6m_curve = _bootstrap_euribor6m_Apr14(discount_curve_handle)

    return euribor6m_curve


def dual_curve_bootstrap_eur_Apr14():
    euribor6m_curve = _dual_curve_bootstrap_eur_Apr14()
    print('reference date: ', euribor6m_curve.referenceDate())

    # discount factors
    print('====== euribor6m discount factors (estr ois discounted) Apr14 =====')
    euribor6m_discounts_instr = [(d, euribor6m_curve.discount(d)) for d in euribor6m_curve.dates()]
    print(pd.DataFrame(euribor6m_discounts_instr))
    pd.DataFrame(euribor6m_discounts_instr).to_clipboard()
    print()


def price_13y_eur_swap_Apr14():
    # discount curve
    sofr_curve_handle = YieldTermStructureHandle(_bootstrap_estr_Apr14())

    # forward term structure (forecast)
    euribor6m_curve_handle = YieldTermStructureHandle(_dual_curve_bootstrap_eur_Apr14())

    Settings.instance().evaluationDate = Date(14, 4, 2022)

    # 13Y swap at market level of 1.6795% fixed rate
    calendar = UnitedStates()
    effective_date = Date(20, 4, 2022)
    maturity_date = Date(22, 4, 2035)

    fixed_leg_tenor = Period(12, Months)
    fixed_schedule = Schedule(effective_date, maturity_date,
                              fixed_leg_tenor, calendar,
                              ModifiedFollowing, ModifiedFollowing,
                              DateGeneration.Forward, False)

    float_leg_tenor = Period(6, Months)
    float_schedule = Schedule(effective_date, maturity_date,
                              float_leg_tenor, calendar,
                              ModifiedFollowing, ModifiedFollowing,
                              DateGeneration.Forward, False)

    notional = 10000000
    fixed_rate = 1.6795 / 100
    fixed_leg_daycount = Thirty360(Thirty360.European)
    float_spread = 0
    float_leg_daycount = Actual360()

    ir_swap = VanillaSwap(VanillaSwap.Payer, notional, fixed_schedule,
                          fixed_rate, fixed_leg_daycount, float_schedule,
                          Euribor(Period(6, Months), euribor6m_curve_handle), float_spread, float_leg_daycount)

    swap_engine = DiscountingSwapEngine(sofr_curve_handle)
    ir_swap.setPricingEngine(swap_engine)

    print('===== price forward starting 13y swap Apr14 =====')
    print('par swap rate: ', ir_swap.fairRate() * 100, '%')
    print('npv: ', ir_swap.NPV())
    print('cv01: ', ir_swap.fixedLegBPS())
    print()

    print('fixed_schedule: ', fixed_schedule.dates())
    x = fixed_schedule.dates()
    discount_factors = [(sofr_curve_handle.discount(x[i + 1]) * fixed_leg_daycount.yearFraction(x[i], x[i + 1]))
                        for i, date in enumerate(x[:-1])]
    import numpy as np
    print('cv01 (verify): ', np.array(discount_factors).sum() * notional / 10000)  # 10000 for bps


# GBP Apr 14

def _single_curve_bootstrap_sonia_Apr14():
    Settings.instance().evaluationDate = Date(14, 4, 2022)

    sonia = Sonia()
    print(sonia, ': fixing days: ', sonia.fixingDays())

    # deposit with spot 1d sonia rate
    helpers = [DepositRateHelper(QuoteHandle(SimpleQuote(0.6908 / 100)),
                                 Period(1, Days), 0, sonia.fixingCalendar(), sonia.businessDayConvention(), False,
                                 sonia.dayCounter())]

    # swaps
    spread = QuoteHandle()  # spread = 0
    fwdStart = Period(0, Days)

    def swapRateHelper(rate, tenor, periodUnit):
        # single curve bootstrapping
        return SwapRateHelper(QuoteHandle(SimpleQuote(rate / 100)), Period(tenor, periodUnit), sonia.fixingCalendar(),
                              Annual, sonia.businessDayConvention(), sonia.dayCounter(), sonia, spread, fwdStart)

    helpers += [swapRateHelper(rate, tenor, Weeks)
                for tenor, rate in [
                    (1, 0.6905), (2, 0.6906)
                ]]
    helpers += [swapRateHelper(rate, tenor, Months)
                for tenor, rate in [
                    (1, 0.7980), (2, 0.8957), (3, 1.0060), (4, 1.0976), (5, 1.1824), (6, 1.2759),
                    (7, 1.3561), (8, 1.4310), (9, 1.5154), (10, 1.5832), (11, 1.6475), (18, 2.0184)
                ]]
    helpers += [swapRateHelper(rate, tenor, Years)
                for tenor, rate in [
                    (1, 1.7155), (2, 2.1637), (3, 2.1970), (4, 2.1600), (5, 2.1160), (6, 2.0600), (7, 2.0120),
                    (8, 1.9760), (9, 1.9520), (10, 1.9380), (12, 1.9104), (15, 1.8700),
                    (20, 1.8103), (25, 1.7620), (30, 1.7210), (40, 1.6318), (50, 1.5415)
                ]]

    # discount curve
    # settlement: T+0
    curve_start_date = sonia.fixingCalendar().advance(Settings.instance().evaluationDate, 0, Days)
    print('curve_start_date: ', curve_start_date)
    sonia_curve = PiecewiseLogLinearDiscount(curve_start_date, helpers, Actual365Fixed())
    sonia_curve.enableExtrapolation()

    return sonia_curve


def single_curve_bootstrap_sonia_Apr14():
    sonia_curve = _single_curve_bootstrap_sonia_Apr14()
    print('reference date: ', sonia_curve.referenceDate())

    # plot forward curve
    # today = sonia_curve.referenceDate()
    # end = today + Period(5, Years)
    # dates = [Date(serial) for serial in range(today.serialNumber(), end.serialNumber() + 1)]
    # sonia_rates = [euribor6m_curve.forwardRate(d, TARGET().advance(d, 3, Months), Actual360(), Simple).rate() * 100
    #                  for d in dates]
    # plt.plot(sonia_rates)
    # plt.show()

    # discount factors
    euribor6m_discounts_instr = [(d, sonia_curve.discount(d)) for d in sonia_curve.dates()]
    print(pd.DataFrame(euribor6m_discounts_instr))
    pd.DataFrame(euribor6m_discounts_instr).to_clipboard()


# CAD Apr 14

def _bootstrap_cdor3m_Apr14(discount_curve_handle=None):
    Settings.instance().evaluationDate = Date(14, 4, 2022)

    cdor3m = Cdor(Period(3, Months))
    print(cdor3m, ': fixing days: ', cdor3m.fixingDays())
    settlementDay = 0

    # deposit with spot 3m cdor rate
    helpers = [DepositRateHelper(QuoteHandle(SimpleQuote(1.5175 / 100)),
                                 Period(3, Months), settlementDay, cdor3m.fixingCalendar(), ModifiedFollowing, False,
                                 cdor3m.dayCounter())]

    # 3m cdor Futures
    helpers += [FuturesRateHelper(QuoteHandle(SimpleQuote(100 - rate)),
                                  start, end, Actual365Fixed())
                for (start, end, rate) in [
                    (Date(15, 6, 2022), Date(21, 9, 2022), 2.049427292),
                    (Date(21, 9, 2022), Date(21, 12, 2022), 2.688007949),
                    (Date(21, 12, 2022), Date(15, 3, 2023), 3.011173934),
                    (Date(15, 3, 2023), Date(21, 6, 2023), 3.188547234),
                    (Date(21, 6, 2023), Date(20, 9, 2023), 3.255396987),
                    (Date(20, 9, 2023), Date(20, 12, 2023), 3.276738988)
                ]]

    # swaps
    spread = QuoteHandle()  # spread = 0
    fwdStart = Period(0, Days)

    def swapRateHelper(rate, tenor, discount_curve_handle):
        if discount_curve_handle is None:
            return SwapRateHelper(QuoteHandle(SimpleQuote(rate / 100)), Period(tenor, Years), cdor3m.fixingCalendar(),
                                  Semiannual, ModifiedFollowing, Actual365Fixed(), cdor3m, spread, fwdStart)
        else:
            return SwapRateHelper(QuoteHandle(SimpleQuote(rate / 100)), Period(tenor, Years), cdor3m.fixingCalendar(),
                                  Semiannual, ModifiedFollowing, Actual365Fixed(), cdor3m, spread, fwdStart,
                                  discount_curve_handle)

    helpers += [swapRateHelper(rate, tenor, discount_curve_handle)
                for tenor, rate in [
                    (2, 2.836238503), (3, 2.944818497), (4, 2.972025514), (5, 2.996644974), (6, 3.025250077),
                    (7, 3.068000078), (8, 3.121999979), (9, 3.172099948), (10, 3.211602926), (12, 3.264999986),
                    (15, 3.340399981), (20, 3.356899977), (25, 3.278999925), (30, 3.164999962)
                ]]

    # discount curve
    curve_start_date = cdor3m.fixingCalendar().advance(Settings.instance().evaluationDate, settlementDay, Days)
    print('curve_start_date: ', curve_start_date)
    cdor3m_curve = PiecewiseLogLinearDiscount(curve_start_date, helpers, Actual365Fixed())
    cdor3m_curve.enableExtrapolation()

    return cdor3m_curve


def bootstrap_cdor3m_Apr14():
    cdor3m_curve = _bootstrap_cdor3m_Apr14()
    print('reference date: ', cdor3m_curve.referenceDate())

    # plot forward curve
    # today = cdor3m_curve.referenceDate()
    # end = today + Period(5, Years)
    # dates = [Date(serial) for serial in range(today.serialNumber(), end.serialNumber() + 1)]
    # cdor3m_rates = [cdor3m_curve.forwardRate(d, TARGET().advance(d, 3, Months), Actual360(), Simple).rate() * 100
    #                  for d in dates]
    # plt.plot(cdor3m_rates)
    # plt.show()

    # discount factors
    cdor3m_discounts_instr = [(d, cdor3m_curve.discount(d)) for d in cdor3m_curve.dates()]
    print(pd.DataFrame(cdor3m_discounts_instr))
    pd.DataFrame(cdor3m_discounts_instr).to_clipboard()


def _bootstrap_corra_Apr14():
    # evaluation date = Apr14
    # curve start date = Apr14
    # deposit / swap settlement: T+1

    Settings.instance().evaluationDate = Date(14, 4, 2022)

    corra = OvernightIndex('Corra', 0, CADCurrency(), Canada(), Actual365Fixed())
    settlementDay = 1

    print(corra, ': fixing days: ', corra.fixingDays())
    print(corra, ': fixing calendar: ', corra.fixingCalendar())
    print(corra, ': day convention: ', corra.businessDayConvention())

    # deposit with overnight corra rate
    helpers = [
        DepositRateHelper(QuoteHandle(SimpleQuote(rate / 100)),
                          Period(1, Days), fixingDays,
                          corra.fixingCalendar(), Following, False, Actual365Fixed())
        for rate, fixingDays in [(0.95, 1)]
    ]

    # swaps
    # annual payment
    helpers += [OISRateHelper(settlementDay, Period(*tenor),
                              QuoteHandle(SimpleQuote(rate / 100)), corra, paymentFrequency=Annual)
                for rate, tenor in [
                    (0.935, (1, Weeks)),
                    (0.8443, (2, Weeks)),
                    (0.9400, (1, Months)), (1.0730, (2, Months)), (1.1900, (3, Months)),
                    (1.3520, (4, Months)), (1.4660, (5, Months)), (1.5930, (6, Months)), (1.9110, (9, Months)),
                    (2.1140, (1, Years))
                ]]
    # semi-annual payment
    helpers += [OISRateHelper(settlementDay, Period(*tenor),
                              QuoteHandle(SimpleQuote(rate / 100)), corra, paymentFrequency=Semiannual)
                for rate, tenor in [
                    (2.5250, (2, Years)), (2.6340, (3, Years)), (2.6680, (4, Years)),
                    (2.6880, (5, Years)), (2.7580, (7, Years)), (2.9016, (10, Years)),
                    (2.9550, (12, Years)), (3.0304, (15, Years)),
                    (3.0469, (20, Years)), (2.9690, (25, Years)), (2.8550, (30, Years))
                ]]

    # discount curve
    # settlement: T+1
    curve_start_date = corra.fixingCalendar().advance(Settings.instance().evaluationDate, settlementDay, Days)
    corra_curve_c = PiecewiseLogLinearDiscount(curve_start_date, helpers, Actual365Fixed())
    corra_curve_c.enableExtrapolation()

    return corra_curve_c


def bootstrap_corra_Apr14():
    corra_curve_c = _bootstrap_corra_Apr14()
    print('reference date: ', corra_curve_c.referenceDate())

    reference_date = corra_curve_c.referenceDate()
    print(reference_date)

    # discount factors
    corra_discounts_instr = [(d, corra_curve_c.discount(d)) for d in corra_curve_c.dates()]
    print(pd.DataFrame(corra_discounts_instr))
    pd.DataFrame(corra_discounts_instr).to_clipboard()


def _dual_curve_bootstrap_cad_Apr14():
    corra_curve = _bootstrap_corra_Apr14()
    discount_curve_handle = RelinkableYieldTermStructureHandle()
    discount_curve_handle.linkTo(corra_curve)
    cdor3m_curve = _bootstrap_cdor3m_Apr14(discount_curve_handle)

    return cdor3m_curve


def dual_curve_bootstrap_cad_Apr14():
    cdor3m_curve = _dual_curve_bootstrap_cad_Apr14()
    print('reference date: ', cdor3m_curve.referenceDate())

    # discount factors
    print('====== cdor3m_curve discount factors (corra ois discounted) Apr14 =====')
    cdor3m_discounts_instr = [(d, cdor3m_curve.discount(d)) for d in cdor3m_curve.dates()]
    print(pd.DataFrame(cdor3m_discounts_instr))
    pd.DataFrame(cdor3m_discounts_instr).to_clipboard()
    print()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # bootstrap_sofr_Feb18()
    # bootstrap_libor3m_Feb18()
    # dual_curve_bootstrap_Feb18()

    # bootstrap_sofr_Feb25()
    # bootstrap_libor3m_Feb25()
    # dual_curve_bootstrap_Feb25()

    # check_calibration_fit_Feb25()
    # price_2y_imm_swap_Feb25()
    # compare_libor3m_single_dual_forward_rates_Feb25()

    # bootstrap_estr_Apr14()
    # bootstrap_euribor6m_Apr14()
    # dual_curve_bootstrap_eur_Apr14()
    # price_13y_eur_swap_Apr14()

    # single_curve_bootstrap_sonia_Apr14()

    bootstrap_corra_Apr14()
    bootstrap_cdor3m_Apr14()
    dual_curve_bootstrap_cad_Apr14()
