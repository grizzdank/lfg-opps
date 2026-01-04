"""Opportunity source integrations."""

from .base import BaseSource
from .freelancer import FreelancerSource
from .upwork import UpworkSource

__all__ = ["BaseSource", "FreelancerSource", "UpworkSource"]
