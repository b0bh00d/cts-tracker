#-------------------------------------------------------------------------#
# cts-tracker                                                 by Bob Hood #
#                                                                         #
# Module: main                                                            #
#                                                                         #
# Entry point for the cts-tracker system                                  #
#-------------------------------------------------------------------------#

__author__     = "Bob Hood"
__version__    = "1.0"
__maintainer__ = "Bob Hood"
__email__      = "bhood@mozilla.com"
__status__     = "Production"

import os
import sys
import pickle
import subprocess
import importlib.util

from argparse       import ArgumentParser
from typing         import List

import Plot
import Types
import Parse

HAVE_MATPLOTLIB = importlib.util.find_spec('matplotlib') is not None
HAVE_ALTAIR = importlib.util.find_spec('altair') is not None

def diagnostics(ids: Types.Ids, run_info: Types.RunInfo):
    """ Print some useful and intersting information about the latest run """
    print('chunks', run_info.chunk_count)
    print('tests', run_info.test_count, 'disabled', run_info.disabled_test_count)
    print('subtests', run_info.subtest_count, 'disabled', run_info.disabled_subtest_count)
    # tests->properties->expected 'SKIP', 'TIMEOUT', 'CRASH', 'OK', 'ERROR'
    print('tests_properties_expected_ids', ids.tests_properties_expected_ids)
    # subtests->properties->expected 'OK', 'PASS', 'FAIL', 'SKIP', 'TIMEOUT'
    print('subtests_properties_expected_ids', ids.subtests_properties_expected_ids)
    print('test_implementation_status', ids.test_implementation_status_ids)
    print('subtest_implementation_status', ids.subtest_implementation_status_ids)

    print('\ntests', run_info.test_count, 'disabled', run_info.disabled_test_count)
    for tier in Types.TIERS[1:]:
        print(run_info.test_tier_count[tier])
        for platform in Types.PLATFORMS:
            print(f'\ttest_dbg_intermittent_count[{tier}][{platform}]', run_info.test_dbg_intermittent_count[tier][platform])
        for platform in Types.PLATFORMS:
            print(f'\ttest_opt_intermittent_count[{tier}][{platform}]', run_info.test_opt_intermittent_count[tier][platform])
        for platform in Types.PLATFORMS:
            print(f'\ttest_dbg_passing_count[{tier}][{platform}]', run_info.test_dbg_passing_count[tier][platform])
        for platform in Types.PLATFORMS:
            print(f'\ttest_opt_passing_count[{tier}][{platform}]', run_info.test_opt_passing_count[tier][platform])

    print('\nsubtests', run_info.subtest_count, 'disabled', run_info.disabled_subtest_count)
    for tier in Types.TIERS[1:]:
        print(tier)
        for platform in Types.PLATFORMS:
            print(f'\tsubtest_dbg_intermittent_count[{tier}][{platform}]', run_info.subtest_dbg_intermittent_count[tier][platform])
        for platform in Types.PLATFORMS:
            print(f'\tsubtest_opt_intermittent_count[{tier}][{platform}]', run_info.subtest_opt_intermittent_count[tier][platform])
        for platform in Types.PLATFORMS:
            print(f'\tsubtest_dbg_passing_count[{tier}][{platform}]', run_info.subtest_dbg_passing_count[tier][platform])
        for platform in Types.PLATFORMS:
            print(f'\tsubtest_opt_passing_count[{tier}][{platform}]', run_info.subtest_opt_passing_count[tier][platform])

if __name__ == "__main__":
    parser = ArgumentParser(description="SyncNet")
    parser.add_argument("-m", "--maxhistory", metavar="RUNCOUNT", default=5, type=int, help="Maximum number of run histories to remember")
    parser.add_argument("-R", "--repo", metavar="PATH", default=None, type=str, help="Path to the github repo for cts-tracker")
    parser.add_argument("-M", "--matplotlib", action="store_true", default=False, help="Generate charts using matplotlib")
    parser.add_argument("-A", "--altair", action="store_true", default=False, help="Generate charts using altair")

    options, args = parser.parse_known_args()

    # validate the local repo
    if not options.repo:
        print('Error: the data path to the github repo was not specified')
        sys.exit(1)
    elif not os.path.exists(options.repo):
        print(f"Error: the repo path ('{options.repo}') is not accessible")
        sys.exit(1)
    else:
        # validate data paths
        data_path = os.path.join(options.repo, 'data')
        image_path = os.path.join(options.repo, 'images')
        if not os.path.exists(data_path):
            print(f"Error: the repo data path ('{data_path}') is not accessible")
            sys.exit(1)
        elif not os.path.exists(image_path):
            print(f"Error: the repo images path ('{image_path}') is not accessible")
            sys.exit(1)

    if options.matplotlib and (not HAVE_MATPLOTLIB):
        print('Error: the matplotlib graphing package is not available')
        sys.exit(1)
    if options.altair and (not HAVE_ALTAIR):
        print('Error: the altair graphing package is not available')
        sys.exit(1)

    if options.matplotlib:
        options.altair = False
    elif options.altair:
        options.matplotlib = False

    # note the current modified stamp of the dump file
    run_file = os.path.join(options.repo, 'data', 'dump.json')
    last_run_date = os.stat(run_file).st_mtime

    # make sure the local report is current
    cwd = os.getcwd()
    os.chdir(options.repo)
    try:
        output = subprocess.check_output(['git', 'pull'], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
        print('Error: failed to execute an update of the local repo')
        sys.exit(1)
    os.chdir(cwd)

    # get the post-update stamp of the dump file
    current_run_date = os.stat(run_file).st_mtime

    if last_run_date != current_run_date:
        # the dump file has been updated with new CTS run data

        history_file = os.path.join(options.repo, 'data', 'history.pickle')

        # this might be better as an sqlite database instead of
        # just a _(NonSQL) list of pickled RunInfo data

        history_data: List[Types.RunInfo] = []
        if os.path.exists(history_file):
            history_data = pickle.load(open(history_file, 'rb'))

        run_info = Types.RunInfo()
        ids = Types.Ids()
        Parse.extract_current_run_info(run_info, run_file, ids)

        # append the data from this latest run
        history_data.append(run_info)

        # trim excess history
        while len(history_data) > options.maxhistory:
            history_data.pop(0)

        # save run data
        with open(history_file, 'wb') as f:
            pickle.dump(history_data, f)

        # print diagnostics
        #diagnostics(ids, run_info)

        # if we have an actual history, re-create the plots
        if len(history_data) > 1:
            Plot.regenerate_tier_graphs(options, history_data)

            # intermittent and passing graphs only regard the most recent run data
            Plot.regenerate_intermittent_graphs(options, history_data[-1])
            Plot.regenerate_passfail_graphs(options, history_data[-1])

        # commit the changes in the local repo and push
        # them upstream

        cwd = os.getcwd()
        os.chdir(options.repo)

        try:
            output = subprocess.check_call(['git', 'add', '.'], stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError:
            print('Error: failed to execute an add on the local repo')
            sys.exit(1)

        try:
            output = subprocess.check_call(['git', 'commit', '-m', 'Automatic updated of history and charts'], stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError:
            print('Error: failed to execute a commit on the local repo')
            sys.exit(1)

        try:
            output = subprocess.check_call(['git', 'push'], stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError:
            print('Error: failed to execute a push on the local repo')
            sys.exit(1)

        os.chdir(cwd)

    sys.exit(0)
