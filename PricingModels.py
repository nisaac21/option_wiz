import numpy as np
from scipy.stats import norm
from scipy.optimize import newton

from typing import Literal

from utils import validate_option_type, validate_d_i
from quant_math import gbm_simulation, merton_jump_diff, heston_path
from PayOff import PayOff, PayOffEuropean
from Options import Option

from abc import ABC, abstractmethod

### MONTE CARLO THETA NOT WORKING ###

# POTENTIAL ABSTRACTION
# class PricingModel(ABC):

#     @abstractmethod
#     def __init__(self) -> None:
#         pass

#     @abstractmethod
#     def option_price(self) -> None:
#         pass

#     @abstractmethod
#     def delta(self) -> float:
#         pass

#     @abstractmethod
#     def gamma(self) -> float:
#         pass

#     @abstractmethod
#     def vega(self) -> float:
#         pass

#     @abstractmethod
#     def theta(self) -> float:
#         pass

#     @abstractmethod
#     def rho(self) -> float:
#         pass

#     @abstractmethod
#     def greeks(self) -> dict:
#         pass

# # POTENTIAL ABSTRACTION
# # class Simulator(PricingModel):

#     def _time_steps(self):
#         """Amount of hours in self.T years"""

#         return int(self.T * 252 * 6.5)

#     @abstractmethod
#     def _get_pricing_params(self) -> dict:
#         pass

#     def delta(self) -> float:
#         """Returns the Delta value of an option through finite differencing

#         Returns
#         -------
#             delta : (float) representing the option price's sensitivity to underlying price"""

#         delta_S = self.T / self._time_steps()

#         params = self._get_pricing_params()

#         params_delta = params.copy()

#         params_delta['S'] += delta_S

#         return (self.option_price(params_delta)
#                 - self.option_price(params_delta)) / delta_S

#     def gamma(self) -> float:
#         """Returns the Gamma value of an option through finite differencing

#         Returns
#         -------
#             gamma : (float) representing the option delta's sensitivity to underlying price"""

#         delta_S = self.T / self._time_steps()

#         params = self._get_pricing_params()

#         params_delta_up = params.copy()
#         params_delta_up['S'] += delta_S

#         params_delta_down = params.copy()
#         params_delta_down['S'] -= delta_S

#         return (self.mc_option_price(params_delta_up) -
#                 2 * self.mc_option_price(params) +
#                 self.mc_option_price(params_delta_down)) / (delta_S ** 2)

#     def vega(self) -> float:
#         """Returns the Vega value of an option through finite_differencing
#         Returns
#         -------
#             vega : (float) representing the option price's sensitivity to volatility"""

#         delta_sigma = self.T / self._time_steps(self.T)

#         params = self._get_pricing_params()

#         params_delta = params.copy()

#         params_delta['sigma'] += delta_sigma

#         return (self.mc_option_price(params_delta)
#                 - self.mc_option_price(params)) / delta_sigma

#     def theta(self, S: float, K: float, r: float, sigma: float, T: float, pay_off: PayOff,
#               option_type: Literal["call", "put"] = 'call', num_sims: int = 1000,
#               random_draws: np.array = None, random_jump_draws: np.array = None) -> float:
#         """Returns the Theta value of an option through finite differencing

#         Parameters
#         ----------
#             S : (float) underlying price

#             K : (float) strike price

#             r : (float) risk-free rate, 0.05 means 5%

#             sigma : (float) volatility, 0.05 means 5%

#             T : (float) time till maturity in years

#             pay_off : (PayOff) class for determining optoin intrinsic value at expiration

#             option_type : (str) one of ['call' or 'put'] for desired option type

#             num_sims : (int) number of simultaions to run

#             random_jump_draws : (np.array) pre-sample random draws for the jump component of the model in size (int(T * 252 * 6.5), num_sims)

#         Returns
#         -------
#             theta : (float) representing the option price's sensitivity to time passed, AKA time value"""

#         validate_option_type(option_type)

#         delta_T = T / self._time_steps(T)  # one extra time step

#         if random_draws is None:
#             random_draws = self._random_draws(T + delta_T, num_sims)

#         return (self.mc_option_price(S, K, r, sigma, T + delta_T, option_type, num_sims, random_draws, random_jump_draws=random_jump_draws)
#                 - self.mc_option_price(S, K, r, sigma, T, option_type, num_sims, random_draws[:-2, :], random_jump_draws=random_jump_draws[:-2, :])) / delta_T

#     def rho(self, S: float, K: float, r: float, sigma: float, T: float, pay_off: PayOff,
#             option_type: Literal["call", "put"] = 'call', num_sims: int = 1000,
#             random_draws: np.array = None, random_jump_draws: np.array = None) -> float:
#         """Returns the Rho value of an option through finite_differencing =

#         Returns
#         -------
#             rho : (float) representing the option price's sensitivity to interest rate changes"""

#         validate_option_type(option_type)

#         delta_rho = self.T / self._time_steps(self.T)

#         params = self._get_pricing_params()

#         params_delta = params.copy()

#         params_delta['rho'] += delta_rho

#         return (self.mc_option_price(params_delta)
#                 - self.mc_option_price(params)) / delta_rho


class AnalyticFormula():
    """Class for analytically deriving option characteristic"""

    def __init__(self):
        pass

    def _get_d_i(self, S: float, K: float, r: float,
                 sigma: float, T: float, i: Literal[1, 2]) -> float:
        """Returns the d_i components of the balck scholes formula where i is 1 or 2

        Parameters
        ----------
            S : (float) underlying price 

            K : (float) strike price 

            r : (float) risk-free rate, 0.05 means 5% 

            sigma : (float) volatility, 0.05 means 5% 

            T : (float) time till maturity in years 

            i : (int) either 1 or 2 representing d_1 or d_2 of black scholes formula

        Returns
        -------
            d_i : (float) representing respective component of black scholes formula"""

        validate_d_i(i)

        sigma_sqrt_t = sigma * np.sqrt(T)
        return (np.log(S / K) + (r + np.power(-1, i - 1) * (sigma ** 2) / 2) * T) / sigma_sqrt_t

    def black_scholes_price(self, S: float, K: float,
                            r: float, sigma: float, T: float, option_type: Literal["call", "put"] = 'call') -> float:
        """Calculates the call price of the option using Black-Scholes Formula

        Parameters
        ----------
            S : (float) underlying price 

            K : (float) strike price 

            r : (float) risk-free rate, 0.05 means 5% 

            sigma : (float) volatility, 0.05 means 5% 

            T : (float) time till maturity in years 

            option_type : (str) one of ['call' or 'put'] for desired option type

        Returns
        -------
            option_price : (float) calculated option price"""

        validate_option_type(option_type)

        d_1 = self._get_d_i(S, K, r, sigma, T, 1)

        d_2 = self._get_d_i(S, K, r, sigma, T, 2)

        if option_type == 'call':
            return S * norm.cdf(d_1) - K * np.exp(- r * T) * norm.cdf(d_2)
        else:
            return norm.cdf(-d_2) * K * np.exp(- r * T) - norm.cdf(- d_1) * S

    def delta(self, S: float, K: float,
              r: float, sigma: float, T: float, option_type: Literal["call", "put"] = 'call') -> float:
        """Returns the Delta value of an option through analytic formula

        Parameters
        ----------
            S : (float) underlying price 

            K : (float) strike price 

            r : (float) risk-free rate, 0.05 means 5% 

            sigma : (float) volatility, 0.05 means 5% 

            T : (float) time till maturity in years 

            option_type : (str) one of ['call' or 'put'] for desired option type

        Returns
        -------
            delta : (float) representing the option price's sensitivity to underlying price"""
        validate_option_type(option_type)

        option_change = 0 if option_type == 'call' else 1

        d_1 = self._get_d_i(S, K, r, sigma, T, 1)

        return norm.cdf(d_1) - option_change

    def gamma(self, S: float, K: float,
              r: float, sigma: float, T: float,) -> float:
        """Returns the Gamma value of an option through analytic formula

        Parameters
        ----------
            S : (float) underlying price 

            K : (float) strike price 

            r : (float) risk-free rate, 0.05 means 5% 

            sigma : (float) volatility, 0.05 means 5% 

            T : (float) time till maturity in years 

        Returns
        -------
            gamma : (float) representing the option delta's sensitivity to underlying price"""

        d_1 = self._get_d_i(S, K, r, sigma, T, 1)

        return norm.pdf(d_1) / (S * sigma * np.sqrt(T))

    def vega(self, S: float, K: float,
             r: float, sigma: float, T: float,) -> float:
        """Returns the Vega value of an option through analytic formula

        Parameters
        ----------
            S : (float) underlying price 

            K : (float) strike price 

            r : (float) risk-free rate, 0.05 means 5% 

            sigma : (float) volatility, 0.05 means 5% 

            T : (float) time till maturity in years 

        Returns
        -------
            vega : (float) representing the option price's sensitivity to volatility"""

        d_1 = self._get_d_i(S, K, r, sigma, T, 1)

        return S * norm.pdf(d_1) * np.sqrt(T)

    def theta(self, S: float, K: float,
              r: float, sigma: float, T: float, option_type: Literal["call", "put"] = 'call') -> float:
        """Returns the Theta value of an option through analytic formula

        Parameters
        ----------
            S : (float) underlying price 

            K : (float) strike price 

            r : (float) risk-free rate, 0.05 means 5% 

            sigma : (float) volatility, 0.05 means 5% 

            T : (float) time till maturity in years 

            option_type : (str) one of ['call' or 'put'] for desired option type

        Returns
        -------
            theta : (float) representing the option price's sensitivity to time passed, AKA time value"""
        validate_option_type(option_type)

        d_1 = self._get_d_i(S, K, r, sigma, T, 1)
        d_2 = self._get_d_i(S, K, r, sigma, T, 2)

        option_change = 1 if option_type == 'call' else -1

        return ((- S * norm.pdf(d_1) * sigma) / (2 * np.sqrt(T))) - \
            option_change * r * K * \
            np.exp(- r * T) * norm.cdf(option_change * d_2)

    def rho(self, S: float, K: float,
            r: float, sigma: float, T: float, option_type: Literal["call", "put"] = 'call') -> float:
        """Returns the Rho value of an option through analytic formula

        Parameters
        ----------
            S : (float) underlying price 

            K : (float) strike price 

            r : (float) risk-free rate, 0.05 means 5% 

            sigma : (float) volatility, 0.05 means 5% 

            T : (float) time till maturity in years 

            option_type : (str) one of ['call' or 'put'] for desired option type

        Returns
        -------
            rho : (float) representing the option price's sensitivity to interest rate changes"""

        validate_option_type(option_type)

        d_2 = self._get_d_i(S, K, r, sigma, T, 2)

        option_change = 1 if option_type == 'call' else -1

        return option_change * K * T * np.exp(- r * T) * norm.cdf(option_change * d_2)

    def implied_volatility(self, S: float, K: float,
                           r: float, T: float, option_price: float, option_type: Literal["call", "put"] = 'call'):
        """Utilizes the newton-raphson algorithm to compute the implied volatility of an option. Assumes 
        black-sholes is the pricing function and uses vega as its relevant derivative.

        For initial guess formula using Brenner and Subrahmanyam (1988) findings:
        https://www.researchgate.net/publication/245065192_A_Simple_Formula_to_Compute_the_Implied_Standard_Deviation

        Parameters
        ----------
            S : (float) underlying price 

            K : (float) strike price 

            r : (float) risk-free rate, 0.05 means 5% 

            sigma : (float) volatility, 0.05 means 5% 

            T : (float) time till maturity in years 

            option_price : (float) observered price of the option

            option_type : (str) one of ['call' or 'put'] for desired option type

        Returns
        -------
            implied_volatility : (float) where 0.05 means 5% """

        intial_vol = np.sqrt(2 * np.pi / T) * (option_price / S)

        def f(x): return self.black_scholes_price(
            S, K, r, x, T, option_type) - option_price

        def fprime(x): return self.vega(S, K, r, x, T)

        return newton(func=f, fprime=fprime, x0=intial_vol)


class MonteCarlo():
    """Class utilizes Monte Carlo techniques to determine option qualities based on jump diffusion """

    def __init__(self):
        pass

    def _random_draws(self, T, num_sims):
        """Returns a standard random sample"""

        time_steps = self._time_steps(T)

        return np.random.normal(0, 1, size=(time_steps, num_sims))

    def _random_jump_draws(self, T: float, num_sims: int, lambda_j: float = 0.1, mu_j: float = -0.2,  sigma_j: float = 0.3):
        """Returns a random sample of the jump component in Merton's jump-diffusion model

        Parameters
        ----------
            T : (float) total time to simulate over

            num_sim : (int) number of simulations to run 

            lambda_j : (float) jump intensity

            mu_j : (float) average jump size 

            sigma_j : (float) jump size volatility

        Returns
        -------
        """

        n_steps = self._time_steps(T)
        dt = T / n_steps
        return np.random.normal(mu_j, sigma_j, size=(n_steps, num_sims)) * np.random.poisson(lambda_j * dt, size=(n_steps, num_sims))

    def option_price(self, S0: float, K: float, r: float, sigma: float,
                     T: float, pay_off: PayOff, lambda_j: float = 0.1,
                     mu_j: float = -0.2, sigma_j: float = 0.3,
                     jump_diff: bool = True, num_sims: int = 1000, random_draws: np.array = None, random_jump_draws: np.array = None):
        """Returns the price of a Euopean option using a Monte Carlo Simulation. Note 
        that the price gets more accurate as the simulations increase 

        Parameters
        ----------
            S : (float) underlying price 

            K : (float) strike price 

            r : (float) risk-free rate, 0.05 means 5% 

            sigma : (float) volatility, 0.05 means 5% 

            T : (float) time till maturity in years 

            pay_off : (PayOff) class for determining optoin intrinsic value at expiration  

            num_sims : *OPTIONAL* (int) number of Monte Carlo Simulations to run

            random_draws : *OPTIONAL* (np.array) randomly sample paths from standard normal in size (int(T * 252 * 6.5), num_sims)

            random_jump_draws : (np.array) pre-sample random draws for the jump component of the model in size (int(T * 252 * 6.5), num_sims)
        Returns
        -------
            option_price : (float) calculated option price"""

        total_trading_hours = self._time_steps(T)

        if jump_diff:
            sims = merton_jump_diff(S0=S, mu=r, sigma=sigma, lambda_j=lambda_j,
                                    mu_j=mu_j, sigma_j=sigma_j, T=T, n_steps=total_trading_hours,
                                    random_draws=random_draws, num_sims=num_sims, random_jump_draws=random_jump_draws)
        else:
            # simulating various option paths with Geometric Brownian Motion
            sims = gbm_simulation(S0=S, mu=r,
                                  n_steps=total_trading_hours, T=T,
                                  sigma=sigma, num_sims=num_sims, random_draws=random_draws)

        # determining all payouts from various paths
        payoffs = pay_off.pay_off(sims)

        # calculating option price
        return np.exp(- r * T) * np.mean(payoffs)

    def delta(self, S: float, K: float, r: float, sigma: float, T: float, pay_off: PayOff,
              option_type: Literal["call", "put"] = 'call', num_sims: int = 1000,
              random_draws: np.array = None, random_jump_draws: np.array = None) -> float:
        """Returns the Delta value of an option through finite differencing and monte_carlo simulations

        Parameters
        ----------
            S : (float) underlying price 

            K : (float) strike price 

            r : (float) risk-free rate, 0.05 means 5% 

            sigma : (float) volatility, 0.05 means 5% 

            T : (float) time till maturity in years

            pay_off : (PayOff) class for determining optoin intrinsic value at expiration

            option_type : (str) one of ['call' or 'put'] for desired option type

            num_sims : (int) number of simulations to run 

            random_draws : (np.array) randomly sample paths from standard normal in size (int(T * 252 * 6.5), num_sims)

            random_jump_draws : (np.array) pre-sample random draws for the jump component of the model in size (int(T * 252 * 6.5), num_sims)

        Returns
        -------
            delta : (float) representing the option price's sensitivity to underlying price"""

        validate_option_type(option_type)

        delta_S = T / self._time_steps(T)

        if random_draws is None:
            random_draws = self._random_draws(T, num_sims)

        if random_jump_draws is None:
            random_jump_draws = self._random_jump_draws(T, num_sims)

        return (self.mc_option_price(S=S+delta_S, K=K, r=r, sigma=sigma, T=T, option_type=option_type, num_sims=num_sims, random_draws=random_draws, pay_off=pay_off, random_jump_draws=random_jump_draws)
                - self.mc_option_price(S=S, K=K, r=r, sigma=sigma, T=T, option_type=option_type, num_sims=num_sims, random_draws=random_draws, pay_off=pay_off, random_jump_draws=random_jump_draws)) / delta_S

    def gamma(self, S: float, K: float, r: float, sigma: float, T: float, pay_off: PayOff,
              option_type: Literal["call", "put"] = 'call', num_sims: int = 1000,
              random_draws: np.array = None, random_jump_draws: np.array = None) -> float:
        """Returns the Gamma value of an option through finite differencing

        Parameters
        ----------
            S : (float) underlying price 

            K : (float) strike price 

            r : (float) risk-free rate, 0.05 means 5% 

            sigma : (float) volatility, 0.05 means 5% 

            T : (float) time till maturity in years   

            pay_off : (PayOff) class for determining optoin intrinsic value at expiration

            option_type : (str) one of ['call' or 'put'] for desired option type

            num_sims : (int) number of simulations to run 

            random_draws : (np.array) randomly sample paths from standard normal in size (int(T * 252 * 6.5), num_sims)

            random_jump_draws : (np.array) pre-sample random draws for the jump component of the model in size (int(T * 252 * 6.5), num_sims)

        Returns
        -------
            gamma : (float) representing the option delta's sensitivity to underlying price"""

        validate_option_type(option_type)

        if random_draws is None:
            random_draws = self._random_draws(T, num_sims)

        if random_jump_draws is None:
            random_jump_draws = self._random_jump_draws(T, num_sims)

        delta_S = T / self._time_steps(T)

        return (self.mc_option_price(S=S + delta_S, K=K, r=r, sigma=sigma, T=T, option_type=option_type, num_sims=num_sims,
                                     random_draws=random_draws, pay_off=pay_off, random_jump_draws=random_jump_draws) -
                2 * self.mc_option_price(S=S, K=K, r=r, sigma=sigma, T=T, option_type=option_type, num_sims=num_sims,
                                         random_draws=random_draws, pay_off=pay_off, random_jump_draws=random_jump_draws) +
                self.mc_option_price(S=S-delta_S, K=K, r=r, sigma=sigma, T=T, option_type=option_type, num_sims=num_sims,
                                     random_draws=random_draws, pay_off=pay_off, random_jump_draws=random_jump_draws)) / (delta_S ** 2)

    def vega(self, S: float, K: float, r: float, sigma: float, T: float, pay_off: PayOff,
             option_type: Literal["call", "put"] = 'call', num_sims: int = 1000,
             random_draws: np.array = None, random_jump_draws: np.array = None) -> float:
        """Returns the Vega value of an option through finite_differencing

        Parameters
        ----------
            S : (float) underlying price 

            K : (float) strike price 

            r : (float) risk-free rate, 0.05 means 5% 

            sigma : (float) volatility, 0.05 means 5% 

            T : (float) time till maturity in years 

            pay_off : (PayOff) class for determining optoin intrinsic value at expiration

            option_type : (str) one of ['call' or 'put'] for desired option type

            num_sims : (int) number of simulations to run

            random_jump_draws : (np.array) pre-sample random draws for the jump component of the model in size (int(T * 252 * 6.5), num_sims)

        Returns
        -------
            vega : (float) representing the option price's sensitivity to volatility"""

        validate_option_type(option_type)

        delta_sigma = 1 / self._time_steps(T)

        if random_draws is None:
            random_draws = self._random_draws(T, num_sims)

        if random_jump_draws is None:
            random_jump_draws = self._random_jump_draws(T, num_sims)

        return (self.mc_option_price(S=S, K=K, r=r, sigma=sigma + delta_sigma, T=T,
                                     option_type=option_type, num_sims=num_sims, random_draws=random_draws, pay_off=pay_off, random_jump_draws=random_jump_draws)
                - self.mc_option_price(S=S, K=K, r=r, sigma=sigma, T=T, option_type=option_type,
                                       num_sims=num_sims, random_draws=random_draws, pay_off=pay_off, random_jump_draws=random_jump_draws)) / delta_sigma

    def theta(self, S: float, K: float, r: float, sigma: float, T: float, pay_off: PayOff,
              option_type: Literal["call", "put"] = 'call', num_sims: int = 1000,
              random_draws: np.array = None, random_jump_draws: np.array = None) -> float:
        """Returns the Theta value of an option through finite differencing 

        Parameters
        ----------
            S : (float) underlying price 

            K : (float) strike price 

            r : (float) risk-free rate, 0.05 means 5% 

            sigma : (float) volatility, 0.05 means 5% 

            T : (float) time till maturity in years 

            pay_off : (PayOff) class for determining optoin intrinsic value at expiration

            option_type : (str) one of ['call' or 'put'] for desired option type

            num_sims : (int) number of simultaions to run

            random_jump_draws : (np.array) pre-sample random draws for the jump component of the model in size (int(T * 252 * 6.5), num_sims)

        Returns
        -------
            theta : (float) representing the option price's sensitivity to time passed, AKA time value"""

        validate_option_type(option_type)

        delta_T = T / self._time_steps(T)  # one extra time step

        if random_draws is None:
            random_draws = self._random_draws(T + delta_T, num_sims)

        return (self.mc_option_price(S, K, r, sigma, T + delta_T, option_type, num_sims, random_draws, random_jump_draws=random_jump_draws)
                - self.mc_option_price(S, K, r, sigma, T, option_type, num_sims, random_draws[:-2, :], random_jump_draws=random_jump_draws[:-2, :])) / delta_T

    def rho(self, S: float, K: float, r: float, sigma: float, T: float, pay_off: PayOff,
            option_type: Literal["call", "put"] = 'call', num_sims: int = 1000,
            random_draws: np.array = None, random_jump_draws: np.array = None) -> float:
        """Returns the Rho value of an option through finite_differencing formula

        Parameters
        ----------
            S : (float) underlying price 

            K : (float) strike price 

            r : (float) risk-free rate, 0.05 means 5% 

            sigma : (float) volatility, 0.05 means 5% 

            T : (float) time till maturity in years 

            pay_off : (PayOff) class for determining optoin intrinsic value at expiration

            option_type : (str) one of ['call' or 'put'] for desired option type

            num_sims : (int) number of simulations to run

            random_draws : (np.array) randomly sample paths from standard normal in size (int(T * 252 * 6.5), num_sims)

            random_jump_draws : (np.array) pre-sample random draws for the jump component of the model in size (int(T * 252 * 6.5), num_sims)

        Returns
        -------
            rho : (float) representing the option price's sensitivity to interest rate changes"""

        validate_option_type(option_type)

        if random_draws is None:
            random_draws = self._random_draws(T, num_sims)

        if random_jump_draws is None:
            random_jump_draws = self._random_jump_draws(T, num_sims)

        delta_r = T / self._time_steps(T)

        return (self.mc_option_price(S=S, K=K, r=r + delta_r, sigma=sigma, T=T, option_type=option_type,
                                     num_sims=num_sims, random_draws=random_draws, pay_off=pay_off, random_jump_draws=random_jump_draws)
                - self.mc_option_price(S=S, K=K, r=r, sigma=sigma, T=T, option_type=option_type,
                                       num_sims=num_sims, random_draws=random_draws, pay_off=pay_off, random_jump_draws=random_jump_draws)) / delta_r


class StochasticVolatility:

    def __init__(self):
        pass

    def _time_steps(self, T):
        return int(T * 252 * 6.5)

    def _random_draws(self, T, num_sims, corr):
        n_steps = self._time_steps(T)
        return np.random.multivariate_normal(mu=[0, 0],
                                             cov=np.array(
                                                 [[1, corr], [corr, 1]]),
                                             size=(num_sims, n_steps))

    def option_pricing(self, S0: float, r: float, T: float,
                       sigma: float, corr: float, epsilon: float,
                       kappa: float, theta: float, pay_off: PayOff, num_sims: int,
                       random_draws: np.array = None) -> float:
        """Returns the price of a Euopean option using a Monte Carlo Simulation based on
        Heston's stochastic volaility model 

        Parameters
        ----------
            S0 : (float) underlying price 

            r : (float) risk-free rate, 0.05 means 5% 

            T : (float) time till maturity in years 

            sigma : (float) volatility, 0.05 means 5% 

            corr : (float) correlation between asset returns and variance 

            epsilon : (float) variance of volatility distribution

            kappa : (float) rate of mean reversion for volatility process

            theta : (float) long-term mean of variance process 

            pay_off : (PayOff) class for determining optoin intrinsic value at expiration  

            num_sims : *OPTIONAL* (int) number of Monte Carlo Simulations to run

            random_draws : (np.array) pre-sample random draws which must be
                                        np.random.multivariate_normal(mu=[0, 0], 
                                                                    cov=np.array([[1, corr], [corr, 1]]),
                                                                    size=(num_sims, n_steps))

        Returns
        -------
            option_price : (float) calculated option price"""

        total_trading_hours = self._time_steps(T)

        sims = heston_path(S0=S0, mu=r, n_steps=total_trading_hours, T=T, sigma=sigma,
                           corr=corr, epsilon=epsilon, kappa=kappa, theta=theta,
                           num_sims=num_sims, random_draws=random_draws)

        # determining all payouts from various paths
        payoffs = pay_off.pay_off(sims)

        # calculating option price
        return np.exp(- r * T) * np.mean(payoffs)

    def delta(self, S0: float, r: float, T: float,
              sigma: float, corr: float, epsilon: float,
              kappa: float, theta: float, pay_off: PayOff, num_sims: int) -> float:
        """Returns the Delta value of an option through finite differencing and monte_carlo simulations

        Parameters
        ----------
            S : (float) underlying price 

            K : (float) strike price 

            r : (float) risk-free rate, 0.05 means 5% 

            sigma : (float) volatility, 0.05 means 5% 

            T : (float) time till maturity in years

            pay_off : (PayOff) class for determining optoin intrinsic value at expiration

            option_type : (str) one of ['call' or 'put'] for desired option type

            num_sims : (int) number of simulations to run 

            random_draws : (np.array) randomly sample paths from standard normal in size (np.array) pre-sample random draws which must be
                                        np.random.multivariate_normal(mu=[0, 0], 
                                                                    cov=np.array([[1, corr], [corr, 1]]),
                                                                    size=(num_sims, n_steps))

        Returns
        -------
            delta : (float) representing the option price's sensitivity to underlying price"""

        validate_option_type(option_type)

        delta_S = T / self._time_steps(T)

        random_draws = self._random_draws(T, num_sims, corr)

        return (self.option_pricing(S0=S0+delta_S, r=r, T=T, sigma=sigma, corr=corr, epsilon=epsilon, kappa=kappa, theta=theta, pay_off=pay_off, num_sims=num_sims, random_draws=random_draws)
                - self.option_pricing(S0=S0, r=r, T=T, sigma=sigma, corr=corr, epsilon=epsilon, kappa=kappa, theta=theta, pay_off=pay_off, num_sims=num_sims, random_draws=random_draws)) / delta_S


if __name__ == '__main__':
    black_scholes = AnalyticFormula()
    monte_carlo = MonteCarlo()
    S = 100
    K = 90
    r = 0.05
    sigma = 0.2
    T = 1
    lambda_j = 0.1  # Jump intensity
    mu_j = -0.2  # Mean jump size
    sigma_j = 0.3
    option_type = 'call'
    pay_off = PayOffEuropean(K, option_type)

    option_price = black_scholes.black_scholes_price(
        S, K, r, sigma, T, option_type)

    print(monte_carlo.mc_option_price(S, K, r, sigma, T, pay_off))
