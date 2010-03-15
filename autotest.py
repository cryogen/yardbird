#!/usr/bin/python

"""
This is a very hackish one-off inotify program that waits for python
files to be modified, and then runs the test suite.
If the test suite passes, it then re-runs it under a statement coverage
analyzer.
All results, in addition to being displayed to the terminal, are sent as
notifications to the desktop GUI.
"""

import os
import sys
from subprocess import call

import gtk
import pynotify     # Display notifications
import pyinotify    # Filesystem event monitoring

import coverage

app_name = 'Yardbird'
pynotify.init("%s Tests" % app_name)

def run_tests():
    num_failed = call(['./manage.py', 'test'], cwd='example')
    if num_failed:
        notify_tests_failed(num_failed)
        return False
    return True

def generate_coverage():
    try:
        os.unlink('./example/.coverage')
    except OSError:
        pass
    num_failed = call(['python', '../coverage.py', '-x', './manage.py', 'test'], cwd='example')
    reload(coverage)
    cov = coverage.the_coverage
    cov.use_cache(True, cache_file='./example/.coverage')
    cov.get_ready()
    return cov

def coverage_report(cov):
    morfs = [morf for morf in cov.filter_by_prefix(cov.cexecuted.keys(),
        omit_prefixes=['/usr', '<doctest', 'coverage', 'autotest']) if
        '<doctest' not in cov.morf_name(morf)]
    morfs.sort(cov.morf_name_compare)

    report = {}
    total_statements = 0
    total_tested = 0

    for morf in morfs:
        _, statements, missing, readable = cov.analysis(morf)
        num_statements = len(statements)
        if not num_statements:
            continue
        total_statements += num_statements
        num_tested = num_statements - len(missing)
        total_tested += num_tested
        if num_tested < num_statements:
            report[cov.morf_name(morf)] = (num_statements, num_tested,
                    str(readable))
    if total_tested < total_statements:
        percentage = 100.0 * total_tested / total_statements
        notify_incomplete_coverage(percentage, report)
    else:
        notify_complete_coverage()
    return report

def notify_tests_failed(num_failed):
    notification = pynotify.Notification('%s Test Failure' % app_name,
        '%d tests failed' % num_failed, gtk.STOCK_DIALOG_ERROR)
    notification.set_urgency(pynotify.URGENCY_LOW)
    notification.show()

def notify_tests_passed():
    notification = pynotify.Notification('%s Tests Passed' % app_name,
        'All tests successfully ran',
        gtk.STOCK_DIALOG_INFO)
    notification.set_urgency(pynotify.URGENCY_LOW)
    notification.show()

def notify_incomplete_coverage(coverage, stats):
    report = ''
    for filename, vals in stats.iteritems():
        total, tested, lines = vals
        if report:
            report += '\n'
        report += '%d%%  %s  %s' % (100.0 * tested / total, filename,
                lines)
    title = '%s Test Coverage %d%%' % (app_name, coverage)
    print '\n', title
    print '=' * len(title)
    print report
    notification = pynotify.Notification(title, report,
            gtk.STOCK_DIALOG_WARNING)
    notification.set_urgency(pynotify.URGENCY_LOW)
    notification.show()

def notify_complete_coverage():
    notification = pynotify.Notification('%s Test Coverage Complete' %
            app_name, 'Your tests have 100% statement coverage!\n' +
            'Now comes the hard part.', gtk.STOCK_DIALOG_INFO)
    notification.set_urgency(pynotify.URGENCY_LOW)
    notification.show()

class SourceChanged(pyinotify.ProcessEvent):
    def process_IN_MODIFY(self, event):
        if not event.pathname.endswith('.py'):
            return
        if run_tests():
            notify_tests_passed()
            coverage_report(generate_coverage())


def autorun_tests():
    wm = pyinotify.WatchManager()
    handler = SourceChanged()
    notifier = pyinotify.Notifier(wm, default_proc_fun=handler)
    wm.add_watch(os.getcwd(), pyinotify.IN_MODIFY, rec=True, auto_add=True)
    notifier.loop()

if __name__ == '__main__':
    if run_tests():
        notify_tests_passed()
        coverage_report(generate_coverage())
    autorun_tests()

