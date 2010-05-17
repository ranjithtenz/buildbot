import os

from twisted.trial import unittest

from buildbot.process import buildstep
from buildbot.status import builder

class BuildStep(unittest.TestCase):
    class NullStep(buildstep.BuildStep):
        def __init__(self, finalResult=builder.SUCCESS, **kwargs):
            buildstep.BuildStep.__init__(self, **kwargs)
            self.finalResult = finalResult
            self.addFactoryArguments(finalResult=finalResult)

        def start(self):
            self.finished(finalResult)

    def test_constructor_defaults(self):
        ns = NullStep()
        self.assertEqual(
            [ ns.name, ns.finalResult ],
            [ 'generic', builder.SUCCESS ])

    def test_factory_defaults(self):
