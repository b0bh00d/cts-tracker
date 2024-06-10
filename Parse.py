#-------------------------------------------------------------------------#
# cts-tracker                                                 by Bob Hood #
#                                                                         #
# Module: Parse                                                           #
#                                                                         #
# CTS dump JSON parsing utilities                                         #
#-------------------------------------------------------------------------#

__author__     = "Bob Hood"
__version__    = "1.0"
__maintainer__ = "Bob Hood"
__email__      = "bhood@mozilla.com"
__status__     = "Production"

import os
import json

import Types

def extract_current_run_info(run_info: Types.RunInfo, run_file: str, ids: Types.Ids) -> None:
    """ Scan through the run output and gather our info for graphing status """
    run_info.run_date = os.stat(run_file).st_mtime

    cts = json.load(open(run_file, 'r'))

    run_info.chunk_count = len(cts)

    for category in cts:
        cat = cts[category]
        id = category[69:].replace('.html.ini','').replace('\\','_')
        for chunk in cat:
            if chunk == 'properties':
                pass
            elif chunk == 'tests':
                for child in cat[chunk]:
                    run_info.test_count += 1
                    test = cat[chunk][child]
                    for item in test:
                        if item == 'properties':
                            properties = test[item]

                            status = properties['implementation_status'] if 'implementation_status' in properties else None
                            expected = properties['expected'] if 'expected' in properties else None
                            disabled = properties['is_disabled']

                            run_info.disabled_test_count += 1 if disabled else 0

                            if not disabled:
                                # figure out the tier first
                                tier = 1    # this won't ever be true with this data set
                                if status is not None:
                                    tier = 3
                                    for name in status:
                                        platform = status[name]
                                        debug = platform['Debug']
                                        optimized = platform['Optimized']
                                        ids.test_implementation_status_ids.add(debug)
                                        ids.test_implementation_status_ids.add(optimized)
                                        assert name in run_info.test_tier_count[Types.TIERS[tier]], f"Platform {name} not in test_tier_count[{Types.TIERS[tier]}]"
                                        run_info.test_tier_count[Types.TIERS[tier]][name] += 1
                                else:
                                    # 'null' is tier 2
                                    tier = 2
                                    for name in run_info.test_tier_count[Types.TIERS[tier]]:
                                        run_info.test_tier_count[Types.TIERS[tier]][name] += 1

                                if expected is not None:
                                    for name in expected:
                                        platform = expected[name]
                                        debug = platform['Debug']
                                        run_info.test_dbg_passing_count[Types.TIERS[tier]][name] += 1 if (len(debug) == 1) and (debug[0] == 'OK') else 0
                                        run_info.test_dbg_intermittent_count[Types.TIERS[tier]][name] += 1 if len(debug) > 1 else 0
                                        optimized = platform['Optimized']
                                        run_info.test_opt_passing_count[Types.TIERS[tier]][name] += 1 if (len(debug) == 1) and (debug[0] == 'OK') else 0
                                        run_info.test_opt_intermittent_count[Types.TIERS[tier]][name] += 1 if len(optimized) > 1 else 0
                                        for id in debug:
                                            ids.tests_properties_expected_ids.add(id)
                                        for id in optimized:
                                            ids.tests_properties_expected_ids.add(id)

                        elif item == 'subtests':
                            subtests = test[item]
                            for child in subtests:
                                subtest = subtests[child]
                                for item in subtest:
                                    run_info.subtest_count += 1
                                    if item == 'properties':
                                        properties = subtest[item]

                                        status = properties['implementation_status'] if 'implementation_status' in properties else None
                                        expected = properties['expected'] if 'expected' in properties else None
                                        disabled = properties['is_disabled']

                                        run_info.disabled_subtest_count += 1 if disabled else 0

                                        if not disabled:
                                            # figure out the tier first
                                            tier = 1    # this won't ever be true with this data set
                                            if status is not None:
                                                tier = 3
                                                for name in status:
                                                    platform = status[name]
                                                    debug = platform['Debug']
                                                    optimized = platform['Optimized']
                                                    ids.subtest_implementation_status_ids.add(debug)
                                                    ids.subtest_implementation_status_ids.add(optimized)
                                                    assert name in run_info.subtest_tier_count[Types.TIERS[tier]], f"Platform {name} not in subtest_tier_count[{Types.TIERS[tier]}]"
                                                    run_info.subtest_tier_count[Types.TIERS[tier]][name] += 1
                                            else:
                                                # 'null' is tier 2
                                                tier = 2
                                                for name in run_info.subtest_tier_count[Types.TIERS[tier]]:
                                                    run_info.subtest_tier_count[Types.TIERS[tier]][name] += 1

                                            if expected is not None:
                                                for name in expected:
                                                    platform = expected[name]
                                                    debug = platform['Debug']
                                                    run_info.subtest_dbg_passing_count[Types.TIERS[tier]][name] += 1 if (len(debug) == 1) and (debug[0] == 'PASS') else 0
                                                    run_info.subtest_dbg_intermittent_count[Types.TIERS[tier]][name] += 1 if len(debug) > 1 else 0
                                                    optimized = platform['Optimized']
                                                    run_info.subtest_opt_passing_count[Types.TIERS[tier]][name] += 1 if (len(debug) == 1) and (debug[0] == 'PASS') else 0
                                                    run_info.subtest_opt_intermittent_count[Types.TIERS[tier]][name] += 1 if len(optimized) > 1 else 0
                                                    for id in debug:
                                                        ids.subtests_properties_expected_ids.add(id)
                                                    for id in optimized:
                                                        ids.subtests_properties_expected_ids.add(id)

