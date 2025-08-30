# unified-ai-shell/modules/__init__.py

"""
This file makes the 'modules' directory a Python package.

It also simplifies importing by bringing the main classes from each module
into the package's top-level namespace. This allows for cleaner imports like:
`from modules import WebsiteGenerator`
instead of the more verbose:
`from modules.website_generator import WebsiteGenerator`
"""

from .website_generator import WebsiteGenerator
from .code_generator import CodeGenerator

# The __all__ variable defines the public API of this package.
# When a user writes `from modules import *`, only these names will be imported.
__all__ = [
    "WebsiteGenerator",
    "CodeGenerator"
]


