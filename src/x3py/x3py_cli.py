#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © 2022, UChicago Argonne, LLC - All Rights Reserved

__version__ = "0.0.1"
__author__ = "Alberto Mittone"
__lastrev__ = "Last revision: 04/11/23"

import sys
import glob
import click

from x3py.x3reg import ITKregistration
from x3py.config import ProInit
from x3py.utils import make_dir, distribute_jobs
import x3py.x3logging as x3logging


@click.command()
@click.option('--filename', type=click.Path(exists=True), required=True, help='Path to the first input file (reference).')
@click.option('--method', default='TranslationTransform', show_default=True, help='Registration method to use.')
@click.option('--config', default='config.json', show_default=True, help='Path to configuration JSON file.')
@click.option('--log', default='x3py.log', show_default=True, help='Log file path.')
def main(filename, method, config, log):
    # Output folder structure
    tmp = filename.split('/')
    folder = '/'.join(tmp[:-1]) or '.'
    tmp.insert(-1, 'corrected')
    ndir = '/'.join(tmp[:-1])
    make_dir(ndir)

    ext = filename.split('.')[-1]
    total = glob.glob(f"{folder}/*.{ext}")
    total.sort()

    if not total:
        click.echo("No files found.")
        sys.exit(1)

    ref_name, total = total[0], total[1:]
    click.echo(f"Using reference: {ref_name}")
    if not total:
        click.echo("Only reference file found. Nothing to register.")
        sys.exit(0)

    x3logging.logger.info("Processing:")
    for f in total:
        x3logging.logger.info(f)

    extra_args = [ref_name, method]
    try:
        pI = ProInit(ref_name)
        itkr = ITKregistration(extra_args, pI.ReturnParameters())
    except Exception as e:
        click.echo(f"Error initializing registration: {e}")
        sys.exit(1)

    def runreg(i):
        try:
            itkr.ImgProcH5(i)
        except Exception as e:
            x3logging.logger.error(f"Failed to register file index {i}: {e}")

    distribute_jobs(runreg, range(len(total)))


if __name__ == "__main__":
    main()
