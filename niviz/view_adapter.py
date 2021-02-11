"""
Provides interface to join objects generated by ConfigSpec
to Nipype ReportCapableInterface
"""

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from nipype.interfaces.mixins import reporting

from pathlib import Path
from string import Template
from dataclasses import dataclass, InitVar

import logging
import logging.config

logging.config.fileConfig("logging.conf")
logger = logging.getLogger(__name__)


@dataclass
class ArgInputSpec:
    '''
    Class to record information about a
    set of files should be defined as inputs
    '''
    name: str
    interface_args: dict = None
    method: str
    bids_output: Path

    out_path: InitVar[str]
    bids_entities: InitVar[tuple[tuple[str, str]]]

    def __post_init__(self, out_path, bids_entities):
        '''
        Construct final output path

        Raises:
            KeyError if BIDS entities required for output_path are missing
        '''

        self.bids_output = Path(
            Template(out_path).substitute(
                {x[0]: x[1] for x in bids_entities}))


class RPTFactory(object):
    '''
    Factory class to generate Nipype RPT nodes
    given argument specification objects derived
    from niviz
    '''

    _interfaces: reporting.ReportCapableInterface

    def get_interface(self,
                      spec: ArgInputSpec) -> reporting.ReportCapableInterface:

        try:
            interface_class = self._interfaces[spec.method]
        except KeyError:
            logger.error(
                f"View method {spec.method} has not been registered "
                "with RPTFactory. If using a custom ReportCapableInterface"
                " register to RPTFactory using\n"
                "from view_adapter import register_interface\n"
                f"register_interface(ReportCapableInterface, {spec.method})")
            raise

        # Create and configure node args
        interface = interface_class(**spec.argmap)
        interface.outputs.out_report = spec.bids_output
        return interface

    def register_interface(self,
                           rpt_interface: reporting.ReportCapableInterface,
                           method: str) -> None:
        '''
        Register a RPT to enable creation with factory_method()
        '''
        self._interfaces[method] = rpt_interface
        return


factory = RPTFactory()


def register_interface(rpt_interface: reporting.ReportCapableInterface,
                       method: str) -> None:
    '''
    Helper function to register a ReportCapableInterface to the persistent
    RPTFactory instance
    '''
    factory.register_interface(rpt_interface, method)
