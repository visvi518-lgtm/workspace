"""
전략 파라미터 자동 최적화 — 유전 알고리즘 (GA)
────────────────────────────────────────────────
흐름:
  1. 백테스트 대상 기간의 데이터를 한 번만 다운로드 (캐시)
  2. 랜덤 파라미터 셋으로 초기 집단 생성
  3. 각 집단을 시뮬레이션하고 점수(Fitness) 계산
  4. 상위 엘리트를 기반으로 교배·돌연변이 → 다음 세대
  5. n_generations 반복 후 상위 K개 결과 반환

점수(Fitness) = 수익률 - 낙폭패널티×0.4 + 승률보너스×0.15
"""
from __future__ import annotations

import random
import threading
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Callable

import pandas as pd
import yfinance as yf
from dateutil.relativedelta import relativedelta

import config
from trader.backtester import _clean_df, BacktestResult
from trader.strategy import TechnicalStrategy


# ── 파라미터 공간 정의 ─────────────────────────────────────────
PARAM_SPACE = {
    #  name              min     max     step
    "swing_tp":        (0.015,  0.080,  0.005),
    "swing_sl":        (-0.050, -0.010, 0.005),
    "scalp_tp_kr":     (0.005,  0.025,  0.002),
    "scalp_tp_us":     (0.008,  0.030,  0.002),
    "scalp_sl":        (-0.015, -0.003, 0.002),
    "max_positions":   (4,      16,     1    ),
    "position_ratio":  (0.08,   0.30,   0.02 ),
}


@dataclass
class ParamSet:
    swing_tp:       float = 0.030
    swing_sl:       float = -0.020
    scalp_tp_kr:    float = 0.010
    scalp_tp_us:    float = 0.015
    scalp_sl:       float = -0.005
    max_positions:  int   = 8
    position_ratio: float = 0.15

    def label(self) -> str:
        return (
            f"스윙TP {self.swing_tp*100:.1f}%/"
            f"SL {self.swing_sl*100:.1f}%  "
            f"스캘KR {self.scalp_tp_kr*100:.1f}%/"
            f"US {self.scalp_tp_us*100:.1f}%/"
            f"SL {self.scalp_sl*100:.1f}%  "
            f"포지션{self.max_positions}개/{self.position_ratio*100:.0f}%"
        )


@dataclass
class OptimResult:
    iteration:      int
    generation:     int
    phase:          str          # "랜덤" | "교배" | "돌연변이"
    params:         ParamSet
    profit_rate:    float
    max_drawdown:   float
    win_rate:       float
    total_trades:   int
    score:          float


def _rand_val(lo, hi, step) -> float:
    n = round((hi - lo) / step)
    return round(lo + random.randint(0, n) * step, 5)


def _random_params() -> ParamSet:
    s = PARAM_SPACE
    return ParamSet(
        swing_tp       = _rand_val(*s["swing_tp"]),
        swing_sl       = _rand_val(*s["swing_sl"]),
        scalp_tp_kr    = _rand_val(*s["scalp_tp_kr"]),
        scalp_tp_us    = _rand_val(*s["scalp_tp_us"]),
        scalp_sl       = _rand_val(*s["scalp_sl"]),
        max_positions  = int(_rand_val(*s["max_positions"])),
        position_ratio = _rand_val(*s["position_ratio"]),
    )


def _mutate(p: ParamSet, rate: float = 0.35) -> ParamSet:
    s = PARAM_SPACE
    def m(val, key, is_int=False):
        if random.random() < rate:
            lo, hi, step = s[key]
            delta = random.choice([-step*2, -step, step, step*2])
            v = round(max(lo, min(hi, val + delta)), 5)
            return int(v) if is_int else v
        return val
    return ParamSet(
        swing_tp       = m(p.swing_tp,       "swing_tp"),
        swing_sl       = m(p.swing_sl,       "swing_sl"),
        scalp_tp_kr    = m(p.scalp_tp_kr,    "scalp_tp_kr"),
        scalp_tp_us    = m(p.scalp_tp_us,    "scalp_tp_us"),
        scalp_sl       = m(p.scalp_sl,       "scalp_sl"),
        max_positions  = m(p.max_positions,  "max_positions",  is_int=True),
        position_ratio = m(p.position_ratio, "position_ratio"),
    )


def _crossover(a: ParamSet, b: ParamSet) -> ParamSet:
    pick = lambda x, y: x if random.random() < 0.5 else y
    return ParamSet(
        swing_tp       = pick(a.swing_tp,       b.swing_tp),
        swing_sl       = pick(a.swing_sl,       b.swing_sl),
        scalp_tp_kr    = pick(a.scalp_tp_kr,    b.scalp_tp_kr),
        scalp_tp_us    = pick(a.scalp_tp_us,    b.scalp_tp_us),
        scalp_sl       = pick(a.scalp_sl,       b.scalp_sl),
        max_positions  = pick(a.max_positions,  b.max_positions),
        position_ratio = pick(a.position_ratio, b.position_ratio),
    )


def _fitness(r: BacktestResult | None) -> float:
    if r is None:
        return -999.0
    wr = r.win_trades / r.sell_trades * 100 if r.sell_trades > 0 else 0
    trade_pen = max(0, (8 - r.total_trades) * 3)
    return r.profit_rate - abs(r.max_drawdown) * 0.4 + wr * 0.15 - trade_pen


class StrategyOptimizer:
    def __init__(self):
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    # ── 데이터 사전 로드 (캐시) ────────────────────────────────

    def load_data(
        self,
        start_year: int, start_month: int, duration_months: int,
        use_kr: bool, use_us: bool,
        progress_cb: Callable | None = None,
    ) -> dict | None:
        """백테스트 기간 데이터 한 번만 다운로드"""
        start_d = date(start_year, start_month, 1)
        end_d   = start_d + relativedelta(months=duration_months)
        fetch_s = (start_d - timedelta(days=90)).strftime("%Y-%m-%d")
        fetch_e = (end_d   + timedelta(days=2)).strftime("%Y-%m-%d")

        # 종목 풀 (최적화는 속도를 위해 최대 30종목만 사용)
        try:
            from crawler.stock_screener import get_pool
            pool = get_pool(use_kr=use_kr, use_us=use_us, kr_n=20, us_n=15)
        except Exception:
            pool = []
            if use_kr:
                pool += [{**s, "market": "KR"} for s in config.DOMESTIC_STOCK_POOL]
            if use_us:
                pool += [{**s, "yf_code": s["code"], "market": "US"} for s in config.US_STOCK_POOL]

        daily_data: dict = {}
        total = len(pool)
        for i, stock in enumerate(pool):
            if self._cancelled:
                return None
            if progress_cb:
                progress_cb(f"데이터 로드 {i+1}/{total}: {stock['name']}", i / total * 0.8)
            yf_code = stock.get("yf_code", stock["code"])
            try:
                df = yf.Ticker(yf_code).history(start=fetch_s, end=fetch_e)
                if df.empty or len(df) < 15:
                    continue
                df = _clean_df(df)
                if not df.empty:
                    daily_data[(stock["code"], stock["market"])] = (df, stock["name"])
            except Exception:
                continue

        if progress_cb:
            progress_cb(f"데이터 로드 완료 ({len(daily_data)}종목)", 0.85)
        return daily_data if daily_data else None

    # ── 단일 파라미터 시뮬레이션 ───────────────────────────────

    def simulate_once(
        self,
        daily_data: dict,
        params: ParamSet,
        start_year: int, start_month: int, duration_months: int,
        initial_capital: float,
        exchange_rate: float,
    ) -> BacktestResult | None:
        """다운로드된 데이터로 빠른 시뮬레이션 (파라미터만 변경)"""
        from trader.backtester import Backtester

        # config에 임시 적용
        orig = _apply(params)
        try:
            bt = Backtester(TechnicalStrategy())
            result = bt._simulate_daily(
                daily_data=daily_data,
                start_d=date(start_year, start_month, 1),
                end_d=date(start_year, start_month, 1) + relativedelta(months=duration_months),
                initial_capital=initial_capital,
                exchange_rate=exchange_rate,
                stop_loss=params.swing_sl,
                take_profit=params.swing_tp,
                max_positions=params.max_positions,
            )
        except Exception:
            result = None
        finally:
            _restore(orig)
        return result

    # ── GA 메인 루프 ──────────────────────────────────────────

    def run(
        self,
        start_year: int, start_month: int, duration_months: int,
        initial_capital: float,
        use_kr: bool, use_us: bool,
        exchange_rate: float,
        n_generations: int = 5,
        pop_size: int = 8,
        elite_k: int = 3,
        on_progress: Callable | None = None,   # (current, total, msg, params) → None
        on_result:   Callable | None = None,   # (OptimResult, all_so_far) → None
        on_data_ready: Callable | None = None, # () → None  데이터 로드 완료 시
    ) -> list[OptimResult]:
        self._cancelled = False
        all_results: list[OptimResult] = []

        total_iters = n_generations * pop_size

        # 1. 데이터 로드
        def _prog(msg, frac):
            if on_progress:
                on_progress(0, total_iters, msg, None)

        daily_data = self.load_data(
            start_year, start_month, duration_months,
            use_kr, use_us, progress_cb=_prog,
        )
        if daily_data is None or self._cancelled:
            return []

        if on_data_ready:
            on_data_ready()

        sim_args = dict(
            start_year=start_year, start_month=start_month,
            duration_months=duration_months,
            initial_capital=initial_capital,
            exchange_rate=exchange_rate,
        )

        # 2. GA 세대 반복
        population: list[ParamSet] = [_random_params() for _ in range(pop_size)]
        global_iter = 0

        for gen in range(n_generations):
            if self._cancelled:
                break

            gen_results: list[tuple[float, OptimResult]] = []

            for idx, params in enumerate(population):
                if self._cancelled:
                    break

                global_iter += 1
                phase = "랜덤 탐색" if gen == 0 else ("교배" if idx < pop_size // 2 else "돌연변이")

                if on_progress:
                    on_progress(global_iter, total_iters,
                                f"[{gen+1}세대/{n_generations}] {phase} — {params.label()}",
                                params)

                result = self.simulate_once(daily_data, params, **sim_args)
                score  = _fitness(result)

                if result:
                    wr = result.win_trades / result.sell_trades * 100 if result.sell_trades > 0 else 0
                    opt_r = OptimResult(
                        iteration=global_iter, generation=gen + 1, phase=phase,
                        params=params, profit_rate=result.profit_rate,
                        max_drawdown=result.max_drawdown, win_rate=wr,
                        total_trades=result.total_trades, score=score,
                    )
                else:
                    opt_r = OptimResult(
                        iteration=global_iter, generation=gen + 1, phase=phase,
                        params=params, profit_rate=0, max_drawdown=0,
                        win_rate=0, total_trades=0, score=-999,
                    )

                all_results.append(opt_r)
                gen_results.append((score, opt_r))

                if on_result:
                    on_result(opt_r, all_results)

            if self._cancelled:
                break

            # 3. 다음 세대 생성
            gen_results.sort(key=lambda x: -x[0])
            elites = [r.params for _, r in gen_results[:elite_k]]

            next_pop: list[ParamSet] = list(elites)  # 엘리트 보존
            while len(next_pop) < pop_size:
                if len(elites) >= 2 and random.random() < 0.5:
                    p1, p2 = random.sample(elites, 2)
                    child  = _crossover(p1, p2)
                    child  = _mutate(child, 0.25)
                    next_pop.append(child)
                else:
                    next_pop.append(_mutate(random.choice(elites), 0.40))

            population = next_pop

        return sorted(all_results, key=lambda x: -x.score)


# ── config 임시 적용 ───────────────────────────────────────────

def _apply(p: ParamSet) -> dict:
    orig = {
        "SCALP_TAKE_PROFIT_KR": config.SCALP_TAKE_PROFIT_KR,
        "SCALP_TAKE_PROFIT_US": config.SCALP_TAKE_PROFIT_US,
        "SCALP_STOP_LOSS":      config.SCALP_STOP_LOSS,
        "MAX_POSITIONS":        config.MAX_POSITIONS,
        "MAX_POSITION_RATIO":   config.MAX_POSITION_RATIO,
    }
    config.SCALP_TAKE_PROFIT_KR = p.scalp_tp_kr
    config.SCALP_TAKE_PROFIT_US = p.scalp_tp_us
    config.SCALP_STOP_LOSS      = p.scalp_sl
    config.MAX_POSITIONS        = p.max_positions
    config.MAX_POSITION_RATIO   = p.position_ratio
    return orig


def _restore(orig: dict):
    for k, v in orig.items():
        setattr(config, k, v)
