#-------------------------------------------------------------------------#
# cts-tracker                                                 by Bob Hood #
#                                                                         #
# Module: Types                                                           #
#                                                                         #
# Type definitions used throughout the system                             #
#-------------------------------------------------------------------------#

__author__     = "Bob Hood"
__version__    = "1.0"
__maintainer__ = "Bob Hood"
__email__      = "bhood@mozilla.com"
__status__     = "Production"

from copy           import deepcopy
from dataclasses    import dataclass

from typing         import Dict

PLATFORMS = ['Windows', 'MacOs', 'Linux']
# first is empty so indexnig matches tier numbers
TIERS = [None, 'Tier 1', 'Tier 2', 'Tier 3']

@dataclass
class RunInfo:
    run_date: float = 0.0

    chunk_count: int = 0

    test_count: int = 0
    test_tier_count: Dict[str, Dict[str, int]] = None

    test_dbg_intermittent_count: Dict[str, Dict[str, int]] = None
    test_opt_intermittent_count: Dict[str, Dict[str, int]] = None

    test_dbg_passing_count: Dict[str, Dict[str, int]] = None
    test_opt_passing_count: Dict[str, Dict[str, int]] = None

    subtest_count: int = 0
    subtest_tier_count: Dict[str, Dict[str, int]] = None

    subtest_dbg_intermittent_count: Dict[str, Dict[str, int]] = None
    subtest_opt_intermittent_count: Dict[str, Dict[str, int]] = None

    subtest_dbg_passing_count: Dict[str, Dict[str, int]] = None
    subtest_opt_passing_count: Dict[str, Dict[str, int]] = None

    disabled_test_count: int = 0
    disabled_subtest_count: int = 0

    def __post_init__(self):
        platform_map = {}
        for platform in PLATFORMS:
            platform_map[platform] = 0

        tier_platform_map = {}
        for tier in TIERS[1:]:
            tier_platform_map[tier] = deepcopy(platform_map)

        self.test_tier_count = deepcopy(tier_platform_map)
        self.subtest_tier_count = deepcopy(tier_platform_map)

        self.test_dbg_intermittent_count = deepcopy(tier_platform_map)
        self.test_opt_intermittent_count = deepcopy(tier_platform_map)

        self.test_dbg_passing_count = deepcopy(tier_platform_map)
        self.test_opt_passing_count = deepcopy(tier_platform_map)

        self.subtest_dbg_intermittent_count = deepcopy(tier_platform_map)
        self.subtest_opt_intermittent_count = deepcopy(tier_platform_map)

        self.subtest_dbg_passing_count = deepcopy(tier_platform_map)
        self.subtest_opt_passing_count = deepcopy(tier_platform_map)

@dataclass
class Ids:
    tests_properties_expected_ids = set()
    subtests_properties_expected_ids = set()
    test_implementation_status_ids = set()
    subtest_implementation_status_ids = set()
