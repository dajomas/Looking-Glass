import logging
import unittest
from looking_glass.access_logging import AccessStatusFilter, configure_access_logging


class AccessLoggingTests(unittest.TestCase):
    def record(self, status, level=logging.INFO):
        return logging.LogRecord('uvicorn.access',level,'',0,'%s %s %s %s %s',('client','GET','/','1.1',status),None)

    def test_success_suppressed(self):
        for status in (100,101,200,201,204,301,302,303,304,307,308):
            with self.subTest(status=status):
                self.assertFalse(AccessStatusFilter().filter(self.record(status)))

    def test_failed_requests_retained(self):
        for status in (400,401,403,404,409,413,422,429,500,503):
            self.assertTrue(AccessStatusFilter().filter(self.record(status)))

    def test_warnings_retained(self):
        self.assertTrue(AccessStatusFilter().filter(self.record(200,logging.WARNING)))

    def test_debug_opt_in(self):
        self.assertTrue(AccessStatusFilter(True).filter(self.record(200)))

    def test_unknown_formats_retained(self):
        record=self.record('invalid')
        self.assertTrue(AccessStatusFilter().filter(record))
        record.args={'status':200}
        self.assertTrue(AccessStatusFilter().filter(record))
        record.args=()
        self.assertTrue(AccessStatusFilter().filter(record))

    def test_configuration_idempotent(self):
        logger=logging.getLogger('uvicorn.access')
        previous=list(logger.filters)
        try:
            configure_access_logging();configure_access_logging(True)
            ours=[f for f in logger.filters if isinstance(f,AccessStatusFilter)]
            self.assertEqual(len(ours),1)
            self.assertTrue(ours[0].log_success)
        finally:
            logger.filters[:]=previous

    def test_configuration_rejects_string(self):
        with self.assertRaises(ValueError):configure_access_logging('false')


if __name__ == '__main__':unittest.main()
