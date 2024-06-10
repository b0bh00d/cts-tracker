#-------------------------------------------------------------------------#
# cts-tracker                                                 by Bob Hood #
#                                                                         #
# Module: Plot                                                            #
#                                                                         #
# Plot-generating functions                                               #
#-------------------------------------------------------------------------#

__author__     = "Bob Hood"
__version__    = "1.0"
__maintainer__ = "Bob Hood"
__email__      = "bhood@mozilla.com"
__status__     = "Production"

import os
import pprint

from copy           import deepcopy
from datetime       import datetime

from typing         import List

try:
    import matplotlib.pyplot as plt
    import numpy as np
except ImportError:
    pass

try:
    import altair as alt
    import pandas as pd
except ImportError:
    pass

import Types

def regenerate_tier_graphs(options, history: List[Types.RunInfo]) -> None:
    """ Update the rendered graphs with the current history data """
    if options.matplotlib:
        dates = []

        tiers = {}
        for tier in Types.TIERS[1:]:
            tiers[tier] = []

        platforms = {}
        for platform in Types.PLATFORMS:
            platforms[platform] = deepcopy(tiers)

        # format the run info for graphing
        min_y = 1000000
        max_y = 0
        for run in history:
            dt = datetime.fromtimestamp(run.run_date)#, tz=timezone.utc)
            dates.append(datetime.strftime(dt, '%b %d %H:%M'))
            for tier in Types.TIERS[1:]:
                # platforms don't appear to differ at this level, so we only need
                # the data from one of them
                val = run.test_tier_count[tier][Types.PLATFORMS[0]]
                platforms[Types.PLATFORMS[0]][tier].append(val)

                min_y = min(min_y, val)
                max_y = max(max_y, val)

        pprint.pp(platforms)

        fig, ax = plt.subplots()

        # plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%d/%Y'))
        # plt.gca().xaxis.set_major_locator(mdates.DayLocator())

        ax.stackplot(dates, platforms[Types.PLATFORMS[0]].values(), labels=platforms[Types.PLATFORMS[0]].keys())

        # ax.vlines(dates, min_y, max_y, color='k', ls=':')

        h_offset = 0.01
        last_label = len(dates) - 1
        for i in range(len(dates)):
            if i != last_label:
                h_offset += i
            else:
                h_offset += i / 2.5
            # last_val = 0
            for tier in Types.TIERS[1:]:
                val = platforms[Types.PLATFORMS[0]][tier][i]
                if val != 0:
                    plt.annotate(val, (h_offset, val))
                    # last_val = val

        # ax.set(xlim=(0, 2), ylim=(0, max_y + 500))

        ax.legend(loc='center left', reverse=True)
        ax.set_title('Tier Migration')
        ax.set_xlabel('Run Dates')
        ax.set_ylabel('Total Tests')

        file_name = os.path.join(options.repo, 'images', 'Tier_Migration.png')
        plt.savefig(file_name)

    elif options.altair:
        # https://altair-viz.github.io/user_guide/data.html

        data = {'date': []}

        # https://altair-viz.github.io/gallery/line_chart_with_arrows.html
        # layers = []

        for run in history:
            dt = datetime.fromtimestamp(run.run_date)#, tz=timezone.utc)
            data['date'].append(datetime.strftime(dt, '%Y-%m-%d'))

            for tier in Types.TIERS[1:]:
                # in terms of tier migration, all platforms
                # produce the same data, so we only need to
                # pass through one platform
                val = run.test_tier_count[tier][Types.PLATFORMS[0]]
                if tier not in data:
                    data[tier] = []
                data[tier].append(val)

                # layers.append(
                #     alt.Chart().mark_text(size=9, align="center", baseline="bottom").encode(
                #         x=alt.datum(1.0),
                #         y=alt.datum(val),
                #         text=alt.datum(str(val))
                #     )
                # )

        # convert wide-form data to long-form, which is easier
        # for Altair
        pd_form = pd.DataFrame(data).melt('date', var_name='tier', value_name='tests')

        chart = alt.Chart(pd_form, title="Tier Migration").mark_area(line=True, point=True).encode(
            alt.X('date').title('Run Date'),
            alt.Y('tests').title('Count of Tests'),
            alt.Color('tier').title('Tiers')
        ).properties(width=300, height=300)

        # layers.insert(0, chart)
        # alt.layer(*layers).save(open("Teir_Migration.png", "wb"), "png", scale_factor=1.5)

        file_name = os.path.join(options.repo, 'images', 'Tier_Migration.png')
        chart.save(open(file_name, "wb"), "png", scale_factor=1.5)

def regenerate_intermittent_graphs(options, run: Types.RunInfo) -> None:
    """ Update the intermittent plots for tiers and platforms """
    for tier in Types.TIERS[1:]:
        for platform in Types.PLATFORMS:
            total = run.test_tier_count[tier][platform]
            dbg_build = run.test_dbg_intermittent_count[tier][platform]
            opt_build = run.test_opt_intermittent_count[tier][platform]

            if options.matplotlib:
                values = {
                    "Intermittents" : np.array([dbg_build, opt_build]),
                    "Total" : np.array([total, total]),
                }

                fig, ax = plt.subplots()
                bottom = np.zeros(2)
                width = 0.5

                for build, counts in values.items():
                    p = ax.bar(['Debug', 'Optimized'], counts, width, label=build, bottom=bottom)
                    bottom += counts
                    ax.bar_label(p, label_type='center')

                ax.set_title(f'{tier}: {platform} Intermittents')
                ax.legend()

                file_name = os.path.join(options.repo, 'images', f'{tier}_{platform}_intermittents.png'.replace(' ', '_'))
                plt.savefig(file_name)
            elif options.altair:
                values = { "build" : ["Debug", "Debug", "Optimized", "Optimized"],
                           "type" : ["Intermittents", "Total", "Intermittents", "Total"],
                           "tests" : [dbg_build, total-dbg_build, opt_build, total-opt_build],
                }

                form = pd.DataFrame(values)

                chart = alt.Chart(form, title=f"{tier}: {platform} Intermittents").mark_bar().encode(
                    alt.X('build').title('Build Type'),
                    alt.Y('tests').title('Count of Tests'),
                    alt.Color('type').title('Result Type'),
                    order=alt.Order('type').sort('ascending')
                ).properties(width=300, height=300)

                file_name = os.path.join(options.repo, 'images', f'{tier}_{platform}_intermittents.png'.replace(' ', '_'))
                chart.save(open(file_name, "wb"), "png", scale_factor=1.5)

def regenerate_passfail_graphs(options, run: Types.RunInfo) -> None:
    """ Update the pass/fail plots for tiers and platforms """
    for tier in Types.TIERS[1:]:
        for platform in Types.PLATFORMS:
            total = run.test_tier_count[tier][platform]
            dbg_build = run.test_dbg_passing_count[tier][platform]
            opt_build = run.test_opt_passing_count[tier][platform]

            if options.matplotlib:
                values = {
                    "Passing" : np.array([dbg_build, opt_build]),
                    "Total" : np.array([total, total]),
                }

                fig, ax = plt.subplots()
                bottom = np.zeros(2)
                width = 0.5

                for build, counts in values.items():
                    p = ax.bar(['Debug', 'Optimized'], counts, width, label=build, bottom=bottom)
                    bottom += counts
                    ax.bar_label(p, label_type='center')

                ax.set_title(f'{tier}: {platform} Passing')
                ax.legend()

                file_name = os.path.join(options.repo, 'images', f'{tier}_{platform}_passing.png'.replace(' ', '_'))
                plt.savefig(file_name)
            elif options.altair:
                values = { "build" : ["Debug", "Debug", "Optimized", "Optimized"],
                           "type" : ["Passing", "Total", "Passing", "Total"],
                           "tests" : [dbg_build, total-dbg_build, opt_build, total-opt_build],
                }

                form = pd.DataFrame(values)

                chart = alt.Chart(form, title=f"{tier}: {platform} Passing").mark_bar().encode(
                    alt.X('build').title('Build Type'),
                    alt.Y('tests').title('Count of Tests'),
                    alt.Color('type').title('Result Type'),
                    order=alt.Order('type').sort('ascending')
                ).properties(width=300, height=300)

                file_name = os.path.join(options.repo, 'images', f'{tier}_{platform}_passing.png'.replace(' ', '_'))
                chart.save(open(file_name, "wb"), "png", scale_factor=1.5)
