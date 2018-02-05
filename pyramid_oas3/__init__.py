# -*- coding: utf-8 -*-
import pyramid

from pyramid_oas3.tween import (
    validation_tween_factory, ResponseValidationError)
from pyramid_oas3.jsonschema.exceptions import ValidationErrors

__all__ = [
    'validation_tween_factory',
    'ValidationErrors',
    'ResponseValidationError',
]


def includeme(config):
    config.add_tween(
        "pyramid_oas3.validation_tween_factory",
        under=pyramid.tweens.EXCVIEW
    )
