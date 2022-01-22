#!/usr/bin/env python3

#
# This file is part of LiteX-Boards.
#
# Copyright (c) 2020 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

import os
import sys
import argparse

from migen import *

from litex.build.io import CRG

from litex_boards.platforms import tinyfpga_bx

from litex.soc.integration.soc_core import *
from litex.soc.integration.soc import SoCRegion
from litex.soc.integration.builder import *
from litex.soc.cores.led import LedChaser

kB = 1024
mB = 1024*kB

# BaseSoC ------------------------------------------------------------------------------------------

class BaseSoC(SoCCore):
    def __init__(self, bios_flash_offset, sys_clk_freq=int(16e6), with_led_chaser=True, **kwargs):
        platform = tinyfpga_bx.Platform()

        # Disable Integrated ROM since too large for iCE40.
        kwargs["integrated_rom_size"]  = 0

        # SoCCore ----------------------------------------------------------------------------------
        SoCCore.__init__(self, platform, sys_clk_freq,
            ident = "LiteX SoC on TinyFPGA BX",
            **kwargs)

        # CRG --------------------------------------------------------------------------------------
        self.submodules.crg = CRG(platform.request("clk16"))

        # SPI Flash --------------------------------------------------------------------------------
        from litespi.modules import AT25SF081
        from litespi.opcodes import SpiNorFlashOpCodes as Codes
        self.add_spi_flash(mode="1x", module=AT25SF081(Codes.READ_1_1_1), with_master=False)

        # Add ROM linker region --------------------------------------------------------------------
        self.bus.add_region("rom", SoCRegion(
            origin = self.bus.regions["spiflash"].origin + bios_flash_offset,
            size   = 32*kB,
            linker = True)
        )
        self.cpu.set_reset_address(self.bus.regions["rom"].origin)

        # Leds -------------------------------------------------------------------------------------
        if with_led_chaser:
            self.submodules.leds = LedChaser(
                pads         = platform.request_all("user_led"),
                sys_clk_freq = sys_clk_freq)

# Build --------------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="LiteX SoC on TinyFPGA BX")
    parser.add_argument("--build",             action="store_true", help="Build bitstream.")
    parser.add_argument("--bios-flash-offset", default="0x50000",   help="BIOS offset in SPI Flash.")
    parser.add_argument("--sys-clk-freq",      default=16e6,        help="System clock frequency.")
    builder_args(parser)
    soc_core_args(parser)
    args = parser.parse_args()

    soc = BaseSoC(
         bios_flash_offset = int(args.bios_flash_offset, 0),
         sys_clk_freq      = int(float(args.sys_clk_freq)),
         **soc_core_argdict(args)
    )
    builder = Builder(soc, **builder_argdict(args))
    builder.build(run=args.build)

if __name__ == "__main__":
    main()
