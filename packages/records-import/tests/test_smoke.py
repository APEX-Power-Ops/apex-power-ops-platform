def test_imports_banked_model_and_self():
    # the banked converter (read-only reuse) + this package both import in the same env
    from power_test_converters.model import PtmModel  # noqa: F401
    from records_import import __version__
    assert __version__
