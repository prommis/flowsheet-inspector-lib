#################################################################################
# Process Optimization and Modeling for Minerals Sustainability (PrOMMiS) Copyright (c) 2023-2026
#
# “Process Optimization and Modeling for Minerals Sustainability (PrOMMiS)” was produced under the DOE
# Process Optimization and Modeling for Minerals Sustainability (“PrOMMiS”) initiative, and is
# copyrighted by the software owners: The Regents of the University of California, through Lawrence
# Berkeley National Laboratory, National Technology & Engineering Solutions of Sandia, LLC through
# Sandia National Laboratories, Carnegie Mellon University, University of Notre Dame, and West
# Virginia University Research Corporation.
#
# NOTICE. This Software was developed under funding from the U.S. Department of Energy and the
# U.S. Government consequently retains certain rights. As such, the U.S. Government has been granted
# for itself and others acting on its behalf a paid-up, nonexclusive, irrevocable, worldwide license
# in the Software to reproduce, distribute copies to the public, prepare derivative works, and perform
# publicly and display publicly, and to permit other to do so.
#
#################################################################################
import pytest
from pydantic import BaseModel
from ..runner import Runner, Action

## -- setup --

simple = Runner(("notrun-1", "hello", "hello.dude", "world", "notrun-2"))


@pytest.fixture
def tmp_simple_db(tmp_path):
    dbpath = tmp_path / "test_runner_simple.db"
    simple.set_report_db(dbfile=dbpath)


@simple.step("hello")
def say_hello(context):
    context["greeting"] = "Hello"
    dude("yo")


@simple.label("hello", "dude")
def dude(s):
    print(f"{s}! this is called from hello, not directly by runner")


@simple.step("world")
def say_to_world(context):
    msg = f"{context['greeting']}, World!"
    print(msg)
    context["greeting"] = msg


empty = Runner(("hi", "bye"))


@pytest.fixture
def tmp_empty_db(tmp_path):
    dbpath = tmp_path / "test_runner_empty.db"
    empty.set_report_db(dbfile=dbpath)


# -- end setup --


@pytest.mark.unit
def test_simple_run_all(tmp_simple_db):
    simple.run_steps()
    assert simple._context["greeting"] == "Hello, World!"


@pytest.mark.unit
def test_runner_actions():

    rn = Runner(("a step",))

    def do_nothing(context):
        print("do nothing")

    rn.add_action("nothing", do_nothing)
    rn.get_action("nothing")
    with pytest.raises(KeyError):
        rn.get_action("something")
    rn.remove_action("nothing")
    with pytest.raises(KeyError):
        rn.get_action("nothing")


@pytest.mark.unit
def test_run_steps_order(tmp_simple_db):
    with pytest.raises(ValueError):
        simple.run_steps("world", "hello")


@pytest.mark.unit
def test_run_steps_args(tmp_simple_db):
    simple.run_steps(first="hello")
    simple.run_steps(last="world")


@pytest.mark.unit
def test_run_1step(tmp_simple_db):
    simple.run_step("hello")


@pytest.mark.unit
def test_run_empty_steps():
    empty.run_steps()


@pytest.mark.unit
def test_run_bad_steps():
    with pytest.raises(KeyError):
        simple.run_steps("howdy", "pardner")

    with pytest.raises(KeyError):
        simple.run_step("notrun-1")


@pytest.mark.unit
def test_runner_context():
    simple.run_steps()
    assert simple["greeting"]


@pytest.mark.unit
def test_add_bad_step():
    with pytest.raises(KeyError):

        @simple.step("bad")
        def do_bad(ctx):
            return

    with pytest.raises(KeyError):

        @simple.label("bad", "sub")
        def do_bad2(ctx):
            return

    # undefined step cannot have a label

    with pytest.raises(ValueError):

        @simple.label("notrun-1", "sub")
        def do_bad3(ctx):
            return


class RunActionExample(Action):
    def report(self) -> dict:
        return {"example": True}


class ReportModel(BaseModel):
    ok: bool = True


class ReportModelAction(Action):
    def report(self) -> ReportModel:
        return ReportModel()


class DelegatingAction(Action):
    def report(self):
        return Action.report(self)


@pytest.mark.unit
def test_runaction(tmp_simple_db):
    simple.reset()
    simple.add_action("foo", RunActionExample)
    simple.run_steps()
    assert simple.get_action("foo").report() == {"example": True}


@pytest.mark.unit
def test_run_steps_conflicting_args_and_endpoint_skip(tmp_path):
    calls = []
    rn = Runner(("a", "b", "c"))
    rn.set_report_db(dbfile=tmp_path / "test_runner_rn.sqlite")

    @rn.step("a")
    def step_a(ctx):
        calls.append("a")

    @rn.step("b")
    def step_b(ctx):
        calls.append("b")

    @rn.step("c")
    def step_c(ctx):
        calls.append("c")

    with pytest.raises(ValueError, match="Cannot specify both 'after' and 'first'"):
        rn.run_steps(first="a", after="a")

    with pytest.raises(ValueError, match="Cannot specify both 'before' and 'last'"):
        rn.run_steps(last="c", before="c")

    rn.run_steps(after="a", before="c")
    assert calls == ["b"]
    assert rn._last_run_steps == ["b"]


@pytest.mark.unit
def test_find_step_no_defined_steps_and_normalize_name(tmp_path):
    rn = Runner(("a", "b"))
    rn.set_report_db(dbfile=tmp_path / "test_runner_rn.sqlite")
    assert rn._find_step() == -1
    assert rn._find_step(reverse=True) == -1
    assert rn.normalize_name(None) == Runner.STEP_ANY


@pytest.mark.unit
def test_runner_report_with_model_and_dict_actions(tmp_path):
    rn = Runner(("run",))
    rn.set_report_db(dbfile=tmp_path / "test_runner_rn.sqlite")

    @rn.step("run")
    def do_run(ctx):
        ctx["ran"] = True

    rn.add_action("dict_action", RunActionExample)
    rn.add_action("model_action", ReportModelAction)

    rn.run_steps()
    report = rn.report()

    assert report["actions"]["dict_action"] == {"example": True}
    assert report["actions"]["model_action"] == {"ok": True}
    assert report["last_run"] == ["run"]


@pytest.mark.unit
def test_action_default_report_returns_none():
    action = DelegatingAction(simple)
    assert action.report() is None


class ExplodingAction(Action):
    """Action whose step hooks raise, to test failure containment."""

    def before_step(self, step_name):
        raise RuntimeError("boom in before_step")

    def after_step(self, step_name):
        raise ValueError("boom in after_step")

    def report(self) -> dict:
        return {"exploded": True}


@pytest.mark.unit
def test_action_step_hook_failure_does_not_stop_run(tmp_path):
    """Regression: an action raising in `before_step`/`after_step` must not
    abort the run. Previously the exception escaped the step wrapper and
    killed `run_steps` before any step status was recorded."""
    rn = Runner(("a", "b"))
    rn.set_report_db(dbfile=tmp_path / "test_runner_boom.sqlite")
    calls = []

    @rn.step("a")
    def step_a(ctx):
        calls.append("a")

    @rn.step("b")
    def step_b(ctx):
        calls.append("b")

    rn.add_action("boom", ExplodingAction)
    rn.add_action("healthy", RunActionExample)
    rn.run_steps()

    # both steps ran and the run itself is not failed
    assert calls == ["a", "b"]
    assert not rn.failed
    assert rn._last_run_steps == ["a", "b"]
    # the action failures were recorded, and other actions still work
    assert isinstance(rn.failed_actions["boom.before_step"], RuntimeError)
    assert isinstance(rn.failed_actions["boom.after_step"], ValueError)
    assert rn.get_action("healthy").report() == {"example": True}
