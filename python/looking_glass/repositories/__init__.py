"""Data access layer. Every function takes an open sqlite3.Connection.

Keeping SQL here (and only here) means routes and services stay storage-agnostic.
"""
