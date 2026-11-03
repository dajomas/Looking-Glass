"""Deterministic unit coverage; no application/HTTP fixture is required."""
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
import random
import unittest

from looking_glass import security


class ThrottleTests(unittest.TestCase):
    def setUp(self):
        self.now = 100.0
        clock = patch.object(security.time, "monotonic", side_effect=lambda: self.now)
        clock.start()
        self.addCleanup(clock.stop)
        self.t = security.LoginThrottle(3, 10)
        self.t.MAX_KEYS = 4

    def test_checks_do_not_allocate(self):
        for i in range(1000):
            self.assertFalse(self.t.blocked("ip", str(i)))
        self.assertEqual(self.t._fails, {})

    def test_threshold_and_exact_expiry(self):
        for i in range(3):
            self.assertFalse(self.t.blocked("ip", "u"))
            self.t.fail("ip", "u")
        self.assertTrue(self.t.blocked("ip", "u"))
        self.now = 109.999
        self.assertTrue(self.t.blocked("ip", "u"))
        self.now = 110
        self.assertFalse(self.t.blocked("ip", "u"))
        self.assertEqual(self.t._fails, {})

    def test_rolling_window_does_not_extend_on_checks(self):
        for instant in (100, 101, 102):
            self.now = instant
            self.t.fail("ip", "u")
        self.now = 109
        self.assertTrue(self.t.blocked("ip", "u"))
        self.now = 110
        self.assertFalse(self.t.blocked("ip", "u"))

    def test_history_is_bounded_and_keeps_newest(self):
        for i in range(100):
            self.now = 100 + i / 100
            self.t.fail("ip", "u")
        self.assertEqual(self.t._fails[self.t._key("ip", "u")], [100.97, 100.98, 100.99])
        self.now = 110.97
        self.assertFalse(self.t.blocked("ip", "u"))

    def test_fail_prunes_without_checks(self):
        self.t.fail("ip", "old")
        self.now = 110
        self.t.fail("ip", "new")
        self.assertNotIn(self.t._key("ip", "old"), self.t._fails)

    def test_check_prunes_other_keys(self):
        self.t.fail("ip", "old")
        self.now = 110
        self.assertFalse(self.t.blocked("different", "different"))
        self.assertEqual(self.t._fails, {})

    def test_capacity_denies_unknown_without_eviction(self):
        for i in range(4):
            self.t.fail("ip", str(i))
        before = {key: list(hits) for key, hits in self.t._fails.items()}
        self.assertTrue(self.t.blocked("ip", "unknown"))
        self.assertFalse(self.t.blocked("ip", "0"))
        self.t.fail("ip", "unknown")
        self.assertEqual(self.t._fails, before)

    def test_capacity_preserves_locked_key(self):
        for i in range(3):
            self.t.fail("ip", "locked")
        for i in range(100):
            self.t.fail("ip", str(i))
        self.assertEqual(len(self.t._fails), 4)
        self.assertTrue(self.t.blocked("ip", "locked"))

    def test_expiry_releases_capacity(self):
        for i in range(4):
            self.t.fail("ip", str(i))
        self.now = 110
        self.assertFalse(self.t.blocked("ip", "new"))
        self.t.fail("ip", "new")
        self.assertEqual(list(self.t._fails), [self.t._key("ip", "new")])

    def test_case_reset_and_ip_isolation(self):
        for i in range(3):
            self.t.fail("ip", "Alice")
        self.assertTrue(self.t.blocked("ip", "ALICE"))
        self.assertFalse(self.t.blocked("other-ip", "Alice"))
        self.t.reset("ip", "aLiCe")
        self.t.reset("ip", "absent")
        self.assertFalse(self.t.blocked("ip", "Alice"))
        self.assertEqual(self.t._fails, {})

    def test_reset_releases_capacity(self):
        for i in range(4):
            self.t.fail("ip", str(i))
        self.t.reset("ip", "0")
        self.assertFalse(self.t.blocked("ip", "new"))

    def test_concurrent_failure_and_churn_bounds(self):
        def worker(i):
            for j in range(10):
                self.t.blocked("ip", str(i))
                self.t.fail("ip", str(i))
        with ThreadPoolExecutor(max_workers=12) as pool:
            list(pool.map(worker, range(100)))
        self.assertEqual(len(self.t._fails), 4)
        self.assertTrue(all(len(hits) == 3 for hits in self.t._fails.values()))

    def test_concurrent_reset_checks_and_failures(self):
        def worker(i):
            for j in range(20):
                self.t.fail("ip", str(i % 8))
                self.t.blocked("ip", str(i % 8))
                self.t.reset("ip", str((i + 1) % 8))
        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(worker, range(32)))
        self.assertLessEqual(len(self.t._fails), 4)
        self.assertTrue(all(0 < len(hits) <= 3 for hits in self.t._fails.values()))

    def test_nonpositive_threshold_stays_blocked_without_retention(self):
        for threshold in (0, -1):
            throttle = security.LoginThrottle(threshold, 10)
            throttle.fail("ip", "u")
            self.assertTrue(throttle.blocked("ip", "u"))
            self.assertEqual(throttle._fails, {})

    def test_nonpositive_window_does_not_lock_or_retain(self):
        for window in (0, -1):
            throttle = security.LoginThrottle(3, window)
            for i in range(10):
                throttle.fail("ip", str(i))
            self.assertFalse(throttle.blocked("ip", "u"))
            self.assertEqual(throttle._fails, {})

    def test_inflight_failure_at_full_capacity_does_not_evict(self):
        self.assertFalse(self.t.blocked("ip", "inflight"))
        for i in range(4):
            self.t.fail("ip", str(i))
        self.t.fail("ip", "inflight")
        self.assertEqual(len(self.t._fails), 4)
        self.assertNotIn(self.t._key("ip", "inflight"), self.t._fails)
        self.assertTrue(self.t.blocked("ip", "inflight"))

    def test_randomized_decisions_match_unbounded_reference(self):
        rng = random.Random(9)
        reference = {}
        for i in range(1000):
            self.now += rng.choice((0, .25, 1, 3))
            key = rng.choice(("a", "b", "c"))
            action = rng.choice(("check", "check", "fail", "reset"))
            if action == "fail":
                reference.setdefault(key, []).append(self.now)
                self.t.fail("ip", key)
            elif action == "reset":
                reference.pop(key, None)
                self.t.reset("ip", key)
            else:
                hits = [t for t in reference.get(key, []) if self.now - t < 10]
                self.assertEqual(self.t.blocked("ip", key), len(hits) >= 3)
            self.assertTrue(all(len(hits) <= 3 for hits in self.t._fails.values()))


if __name__ == "__main__":
    unittest.main()
