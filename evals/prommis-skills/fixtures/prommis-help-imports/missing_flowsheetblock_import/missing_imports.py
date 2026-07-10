"""Fixture with a missing IDAES import."""


def build_model():
    flowsheet = FlowsheetBlock(dynamic=False)
    return flowsheet
