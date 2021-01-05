# Copyright (c) 2021 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Unit tests for the token_cache module."""
import pytest

from bosdyn.client.token_cache import TokenCache, TokenCacheFilesystem, ClearFailedError, NotInCacheError, WriteFailedError


def test_no_op_cache():
    tc = TokenCache()
    with pytest.raises(NotInCacheError):
        tc.read('nonexistent')

    assert len(tc.match('')) == 0


def test_read_empty_cache():
    tc = TokenCacheFilesystem()
    with pytest.raises(NotInCacheError):
        tc.read('nonexistent')


def test_read_one_entry_cache():
    tc = TokenCacheFilesystem()
    tc.write('base_user1', b'100')

    with pytest.raises(NotInCacheError):
        tc.read('user_bad')

    assert b'100' == tc.read('base_user1')


def test_read_two_entries_cache():
    tc = TokenCacheFilesystem()
    tc.write('base_user2', b'200')
    tc.write('base_user1', b'100')

    with pytest.raises(NotInCacheError):
        tc.read('user_bad')

    assert b'100' == tc.read('base_user1')


def test_matching():
    tc = TokenCacheFilesystem()
    tc.write('base_user2', b'200')
    tc.write('base_user1', b'100')

    matches = tc.match('base_user')
    assert 2 == len({'base_user1', 'base_user2'} & matches)


def test_no_matches():
    tc = TokenCacheFilesystem()
    tc.write('base_user2', b'200')
    tc.write('base_user1', b'100')

    matches = tc.match('username')
    assert 0 == len(matches)


def test_clearing_existing_tokens():
    tc = TokenCacheFilesystem()
    tc.write('base_user2', b'200')
    tc.write('base_user1', b'100')

    tc.clear('base_user1')
    tc.clear('base_user2')

    matches = tc.match('base_user')
    assert 0 == len(matches)


def test_clearing_nonexisting_tokens():
    tc = TokenCacheFilesystem()

    with pytest.raises(ClearFailedError):
        tc.clear('user_bad')
