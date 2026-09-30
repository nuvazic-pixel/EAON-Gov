import pytest
from eaon_gov.nl import DeterministicNLAdapter, IntentValidationError

@pytest.mark.parametrize("text,origin,destination", [
    ("M-am mutat din Landsberg în Göttingen și am o mașină.", "Landsberg", "Gottingen"),
    ("Ich bin von Landsberg nach Göttingen umgezogen und habe ein Auto.", "Landsberg", "Gottingen"),
    ("I moved from Landsberg to Göttingen and have a car.", "Landsberg", "Gottingen"),
])
def test_relocation_ro_de_en(text, origin, destination):
    env = DeterministicNLAdapter().parse(text)
    assert env.event == "relocation"
    assert env.entities == {"origin": origin, "destination": destination}
    assert env.context["vehicle_owner"] is True
    assert env.unknown_fields == ("taxable", "beneficiary")

def test_ambiguous_input_is_rejected():
    with pytest.raises(IntentValidationError):
        DeterministicNLAdapter().parse("M-am mutat recent. Ce trebuie să fac?")

def test_unrelated_input_is_rejected():
    with pytest.raises(IntentValidationError):
        DeterministicNLAdapter().parse("Care este vremea azi?")

def test_envelope_converts_to_core_scenario():
    text = "M-am mutat din Landsberg în Göttingen și am o mașină."
    env = DeterministicNLAdapter().parse(text)
    scenario = env.to_scenario("nl-001", text)
    assert scenario["parsed_intent"]["event"] == "relocation"
    assert scenario["context_data"]["vehicle_owner"] is True
