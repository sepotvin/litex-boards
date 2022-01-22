#!/usr/bin/env python3

#
# This file is part of LiteX-Boards.
#
# Copyright (c) 2021 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

import argparse

from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer

from litex_boards.platforms import efinix_trion_t20_mipi_dev_kit

from litex.build.generic_platform import *

from litex.soc.cores.clock import *
from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *
from litex.soc.cores.led import LedChaser

# CRG ----------------------------------------------------------------------------------------------

class _CRG(Module):
    def __init__(self, platform, sys_clk_freq):
        self.clock_domains.cd_sys = ClockDomain()

        # # #

        clk50 = platform.request("clk50")
        rst_n = platform.request("user_btn", 0)

        # PLL
        self.submodules.pll = pll = TRIONPLL(platform)
        self.comb += pll.reset.eq(~rst_n)
        pll.register_clkin(clk50, 50e6)
        pll.create_clkout(self.cd_sys, sys_clk_freq, with_reset=True)

# BaseSoC ------------------------------------------------------------------------------------------

class BaseSoC(SoCCore):
    def __init__(self, sys_clk_freq=int(100e6), with_spi_flash=False, with_led_chaser=True, **kwargs):
        platform = efinix_trion_t20_mipi_dev_kit.Platform()

        # SoCCore ----------------------------------------------------------------------------------
        SoCCore.__init__(self, platform, sys_clk_freq,
            ident = "LiteX SoC on Efinix Trion T20 MIPI Dev Kit",
            **kwargs
        )

        # CRG --------------------------------------------------------------------------------------
        self.submodules.crg = _CRG(platform, sys_clk_freq)

        # SPI Flash --------------------------------------------------------------------------------
        if with_spi_flash:
            from litespi.modules import W25Q32JV
            from litespi.opcodes import SpiNorFlashOpCodes as Codes
            self.add_spi_flash(mode="1x", module=W25Q32JV(Codes.READ_1_1_1), with_master=True)

        # Leds -------------------------------------------------------------------------------------
        if with_led_chaser:
            self.submodules.leds = LedChaser(
                pads         = platform.request_all("user_led"),
                sys_clk_freq = sys_clk_freq)

# Build --------------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="LiteX SoC on Efinix Trion T20 MIPI Dev Kit")
    parser.add_argument("--build",          action="store_true", help="Build bitstream.")
    parser.add_argument("--load",           action="store_true", help="Load bitstream.")
    parser.add_argument("--sys-clk-freq",   default=100e6,        help="System clock frequency.")
    parser.add_argument("--with-spi-flash", action="store_true", help="Enable SPI Flash (MMAPed).")
    builder_args(parser)
    soc_core_args(parser)
    args = parser.parse_args()

    soc     = BaseSoC(
        sys_clk_freq   = int(float(args.sys_clk_freq)),
        with_spi_flash = args.with_spi_flash,
         **soc_core_argdict(args))
    builder = Builder(soc, **builder_argdict(args))
    builder.build(run=args.build)

    if args.load:
        prog = soc.platform.create_programmer()
        prog.load_bitstream(os.path.join(builder.gateware_dir, f"{soc.build_name}.bit"))

if __name__ == "__main__":
    main()
