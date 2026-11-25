#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
黎曼幸运数 —— 用 ζ 函数非平凡零点生成 大乐透 / 双色球 号码

映射规则
---------
黎曼猜想：ζ(s) 的全部非平凡零点都落在临界线 Re(s)=1/2 上。
把第 n 个非平凡零点写成  rho_n = 1/2 + i*gamma_n ，gamma_n 是其虚部。

1. 前区(大乐透 1-35) / 红球(双色球 1-33)
        n = int(gamma_n) % 区间上限 + 1          # 零点的"整数部"
2. 后区(大乐透 1-12) / 蓝球(双色球 1-16)
        n = int(frac(gamma_n) * 区间上限) + 1     # 零点的"小数部"
3. 每期先用 seed 打乱零点取样顺序，再用"取模 + 顺延去重"保证号码不重复，
   同一个 seed 永远得到同一注号码（可复现、可复核）。

注意：这只是把数学常数翻译成数字的仪式感。开奖是独立随机事件，
      与本脚本没有任何因果关系，中奖概率与随手乱写完全相同。
      大乐透头奖 1/21,425,712，双色球头奖 1/17,721,088。

用法
-----
    python riemann_lucky.py                          # 今天日期作种子
    python riemann_lucky.py --period 2026150         # 指定期号作种子
    python riemann_lucky.py --sets 3 --zeros 200     # 出 3 组，取前 200 个零点
    python riemann_lucky.py --game dlt               # 只出大乐透
    python riemann_lucky.py --trace                  # 显示每个号码的取值来源
    python riemann_lucky.py --save                   # 追加写入 号码记录.txt
"""

import argparse
import datetime as dt
import os
import random
import sys

try:
    import mpmath
except ImportError:
    sys.exit("缺少依赖，请先执行:  python -m pip install mpmath")

# ---------------------------------------------------------------- 零点取样

_ZERO_CACHE = {}


def get_zeros(n: int) -> list[float]:
    """返回前 n 个非平凡零点的虚部 gamma_1 ... gamma_n（升序）。"""
    key = n
    if key in _ZERO_CACHE:
        return _ZERO_CACHE[key]

    mpmath.mp.dps = 20  # 20 位有效数字足够
    zeros = []
    for k in range(1, n + 1):
        z = mpmath.zetazero(k)
        zeros.append(float(mpmath.im(z)))
    _ZERO_CACHE[key] = zeros
    return zeros


# ---------------------------------------------------------------- 号码映射

def _pick(values, count, high, frac_mode=False):
    """从 values 里取 count 个 1..high 的不重复整数。

    frac_mode=False：用整数部  int(gamma) % high + 1
    frac_mode=True ：用小数部  int(frac*high) + 1
    返回 [(号码, 来源gamma), ...]
    """
    used, out = set(), []
    i, guard = 0, 0
    while len(out) < count and guard < 100000:
        guard += 1
        g = values[i % len(values)]
        i += 1
        if frac_mode:
            n = int((g - int(g)) * high) + 1
        else:
            n = int(g) % high + 1
        if n < 1:
            n = 1
        if n > high:
            n = high
        tries = 0
        while n in used and tries < high:
            n = n % high + 1
            tries += 1
        if n not in used:
            used.add(n)
            out.append((n, g))
    return out


def make_dlt(zeros, rng):
    """大乐透：前区5个(1-35) + 后区2个(1-12)"""
    pool = list(zeros)
    rng.shuffle(pool)
    front = _pick(pool, 5, 35, frac_mode=False)
    back = _pick(pool, 2, 12, frac_mode=True)
    return sorted(front, key=lambda x: x[0]), sorted(back, key=lambda x: x[0])


def make_ssq(zeros, rng):
    """双色球：红球6个(1-33) + 蓝球1个(1-16)"""
    pool = list(zeros)
    rng.shuffle(pool)
    red = _pick(pool, 6, 33, frac_mode=False)
    blue = _pick(pool, 1, 16, frac_mode=True)
    return sorted(red, key=lambda x: x[0]), blue


# ---------------------------------------------------------------- 输出

def fmt(nums, width):
    return " ".join(f"{n:0{width}d}" for n, _ in nums)


def seed_of(period: str | None, set_no: int) -> int:
    if period:
        base = int("".join(ch for ch in period if ch.isdigit()) or "0")
    else:
        base = int(dt.date.today().strftime("%Y%m%d"))
    return base * 100 + set_no


BANNER = """\
============================================================
  黎曼幸运数 · 非平凡零点取号
  临界线 Re(s)=1/2   |   号码与开奖无因果关系，仅供娱乐
============================================================"""


def main():
    ap = argparse.ArgumentParser(description="用黎曼 ζ 零点生成彩票号码（娱乐向）")
    ap.add_argument("--game", choices=["all", "dlt", "ssq"], default="all",
                    help="all=两种都出(默认)  dlt=大乐透  ssq=双色球")
    ap.add_argument("--sets", type=int, default=2, help="每种彩出几组，默认 2")
    ap.add_argument("--zeros", type=int, default=60, help="取前 N 个零点，默认 60")
    ap.add_argument("--period", default=None, help="期号，如 2026150；缺省用当天日期")
    ap.add_argument("--seed", type=int, default=None, help="直接指定随机种子（覆盖 --period）")
    ap.add_argument("--trace", action="store_true", help="显示每个号码的取值来源零点")
    ap.add_argument("--save", action="store_true", help="追加写入同目录 号码记录.txt")
    args = ap.parse_args()

    if args.sets < 1:
        sys.exit("--sets 至少为 1")
    zeros = get_zeros(max(args.zeros, 20))

    lines = [BANNER]
    head = f"期号种子：{args.period or dt.date.today().strftime('%Y%m%d')}" \
           f"   零点数：{len(zeros)}   γ₁={zeros[0]:.6f}"
    lines.append(head)
    lines.append("")

    want_dlt = args.game in ("all", "dlt")
    want_ssq = args.game in ("all", "ssq")

    for s in range(1, args.sets + 1):
        sd = args.seed + s if args.seed is not None else seed_of(args.period, s)
        rng = random.Random(sd)

        if want_dlt:
            front, back = make_dlt(zeros, rng)
            lines.append(f"[大乐透 第{s}组 / seed={sd}]")
            lines.append(f"  前区：{fmt(front, 2)}")
            lines.append(f"  后区：{fmt(back, 2)}")
            if args.trace:
                for n, g in front:
                    lines.append(f"      {n:02d} ← int(γ={g:.6f}) % 35 + 1")
                for n, g in back:
                    lines.append(f"      {n:02d} ← frac(γ={g:.6f}) × 12 + 1")
            lines.append("")

        # 双色球用另一套种子，避免两组雷同（由主种子派生，仍可复现）
        sd2 = random.Random(sd).randrange(1, 2 ** 31)
        rng2 = random.Random(sd2)
        if want_ssq:
            red, blue = make_ssq(zeros, rng2)
            lines.append(f"[双色球 第{s}组 / seed={sd2}]")
            lines.append(f"  红球：{fmt(red, 2)}")
            lines.append(f"  蓝球：{fmt(blue, 2)}")
            if args.trace:
                for n, g in red:
                    lines.append(f"      {n:02d} ← int(γ={g:.6f}) % 33 + 1")
                for n, g in blue:
                    lines.append(f"      {n:02d} ← frac(γ={g:.6f}) × 16 + 1")
            lines.append("")

    out = "\n".join(lines).rstrip() + "\n"
    print(out)

    if args.save:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "号码记录.txt")
        stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"\n### 生成时间 {stamp}\n")
            f.write(out)
        print(f"已追加写入：{path}")


if __name__ == "__main__":
    main()
