"""Synthetic training artifact. Do not execute this file."""

import pickle


def load_unverified_model(model_file):
    """This intentionally unsafe example exists only to trigger the local scanner."""
    return pickle.load(model_file)
